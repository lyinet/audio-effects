#!/usr/bin/env python3
"""Seed Audio 1.0 dry narration synthesizer (openspeech HTTP non-streaming).

Usage:
  export BYTEPLUS_SEED_API_KEY=...
  python scripts/synthesize.py --text "接下来我们打开终端，输入 npm install。"
  python scripts/synthesize.py --file script.txt --out-dir ./narration-audio --subtitle
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import uuid
from pathlib import Path

try:
    import requests
except ImportError:
    print("需要 requests：pip install requests", file=sys.stderr)
    sys.exit(1)

DEFAULT_URL = "https://openspeech.bytedance.com/api/v3/tts/create"
DEFAULT_MODEL = "seed-audio-1.0"

STYLE_ZH = (
    "Clean dry studio narration only. No music, no sound effects, no ambience bed, "
    "no applause, no crowd.\n"
    "Language: Chinese.\n"
    "Narrator: adult, clear Mandarin, warm professional coding instructor, "
    "medium-low pitch, calm measured pace, precise diction.\n"
    'Read exactly: "{script}"'
)
STYLE_EN = (
    "Clean dry studio narration only. No music, no sound effects, no ambience.\n"
    "Language: English.\n"
    "Narrator: adult, clear American English, warm professional coding instructor, "
    "medium pace, crisp consonants, calm and confident.\n"
    'Read exactly: "{script}"'
)

CODE_READ_MAP = [
    (re.compile(r"\bnpm install\b", re.I), "N-P-M install"),
    (re.compile(r"\bgit clone\b", re.I), "git clone"),
    (re.compile(r"\bAPI\b"), "A-P-I"),
    (re.compile(r"\bJSON\b"), "Jason"),
    (re.compile(r"\bURL\b"), "U-R-L"),
    (re.compile(r"O\(n\)", re.I), "O of n"),
]


def detect_lang(text: str) -> str:
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return "zh" if cjk >= max(1, len(text) // 8) else "en"


def preprocess_script(text: str) -> str:
    t = text.strip()
    t = re.sub(r"[`*_#>]+", "", t)
    t = re.sub(r"\([^)]*(说|语气|平静|缓慢)[^)]*\)", "", t)
    t = re.sub(r"（[^）]*(说|语气|平静|缓慢)[^）]*）", "", t)
    for pat, repl in CODE_READ_MAP:
        t = pat.sub(repl, t)
    # paths: src/index.ts -> src slash index dot T-S (light touch)
    def path_repl(m: re.Match) -> str:
        p = m.group(0)
        p = p.replace("/", " slash ").replace(".", " dot ")
        p = re.sub(r"\bts\b", "T-S", p, flags=re.I)
        p = re.sub(r"\bjs\b", "J-S", p, flags=re.I)
        return p

    t = re.sub(r"\b[\w.-]+/[\w./-]+\b", path_repl, t)
    return re.sub(r"\s+", " ", t).strip()


def build_prompt(script: str, lang: str) -> str:
    tmpl = STYLE_ZH if lang == "zh" else STYLE_EN
    return tmpl.format(script=script)


def get_api_key() -> str:
    key = os.environ.get("BYTEPLUS_SEED_API_KEY") or os.environ.get("VOLC_TTS_API_KEY")
    if not key:
        print("缺少 BYTEPLUS_SEED_API_KEY 或 VOLC_TTS_API_KEY", file=sys.stderr)
        sys.exit(2)
    return key


def synthesize(
    text_prompt: str,
    *,
    out_path: Path,
    fmt: str = "mp3",
    sample_rate: int | None = None,
    speech_rate: int = 0,
    loudness_rate: int = 0,
    pitch_rate: int = 0,
    enable_subtitle: bool = False,
    speaker: str | None = None,
    url: str | None = None,
) -> dict:
    key = get_api_key()
    endpoint = url or os.environ.get("SEED_TTS_URL", DEFAULT_URL)
    if sample_rate is None:
        sample_rate = 44100 if fmt == "mp3" else 40000

    audio_config = {
        "format": fmt,
        "sample_rate": sample_rate,
        "speech_rate": speech_rate,
        "loudness_rate": loudness_rate,
        "pitch_rate": pitch_rate,
        "enable_subtitle": enable_subtitle,
    }
    body: dict = {
        "model": os.environ.get("SEED_TTS_MODEL", DEFAULT_MODEL),
        "text_prompt": text_prompt,
        "audio_config": audio_config,
    }
    if speaker:
        body["speaker"] = speaker

    if len(text_prompt) > 3000:
        raise ValueError(f"text_prompt 超长：{len(text_prompt)} > 3000")

    headers = {
        "X-Api-Key": key,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    r = requests.post(endpoint, headers=headers, json=body, timeout=180)
    logid = r.headers.get("X-Tt-Logid", "")
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"非 JSON 响应 HTTP {r.status_code}: {r.text[:300]}") from None

    if r.status_code != 200 or data.get("code") not in (None, 0, "0"):
        # some success responses omit code; treat missing code + audio as ok
        if not (r.status_code == 200 and (data.get("audio") or data.get("url"))):
            raise RuntimeError(
                f"合成失败 HTTP {r.status_code} code={data.get('code')} "
                f"message={data.get('message')} logid={logid}"
            )

    raw = None
    if data.get("audio"):
        raw = base64.b64decode(data["audio"])
    elif data.get("url"):
        raw = requests.get(data["url"], timeout=120).content
    if not raw:
        raise RuntimeError(f"响应无 audio/url，keys={list(data)} logid={logid}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)

    meta = {
        "out": str(out_path),
        "bytes": len(raw),
        "duration": data.get("duration"),
        "original_duration": data.get("original_duration"),
        "logid": logid,
        "subtitle": data.get("subtitle"),
        "url_ttl_hint": data.get("url"),
    }
    meta_path = out_path.with_suffix(out_path.suffix + ".json")
    # do not persist temporary signed url long-term if user prefers; keep for 2h debug
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def split_segments(text: str) -> list[str]:
    # split on blank lines or ## headings
    parts = re.split(r"\n\s*\n|^## .+$", text, flags=re.M)
    segs = [preprocess_script(p) for p in parts if preprocess_script(p)]
    return segs or [preprocess_script(text)]


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed Audio dry narration synthesizer")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="单段旁白原文")
    g.add_argument("--file", type=Path, help="多段脚本文件（空行分段）")
    ap.add_argument("--out-dir", type=Path, default=Path("./narration-audio"))
    ap.add_argument("--format", default="mp3", choices=["mp3", "wav", "pcm", "ogg_opus"])
    ap.add_argument("--speech-rate", type=int, default=0, help="-50..100，教学可试 -15")
    ap.add_argument("--loudness-rate", type=int, default=0)
    ap.add_argument("--pitch-rate", type=int, default=0)
    ap.add_argument("--speaker", default=None, help="豆包 2.0 音色 ID（可选）")
    ap.add_argument("--subtitle", action="store_true", help="开启字级时间戳")
    ap.add_argument("--lang", choices=["auto", "zh", "en"], default="auto")
    ap.add_argument("--raw-prompt", action="store_true", help="不套干声模板，text_prompt 原样发送")
    args = ap.parse_args()

    raw = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    segments = split_segments(raw) if args.file else [preprocess_script(raw)]

    manifest = []
    for i, seg in enumerate(segments, 1):
        lang = args.lang if args.lang != "auto" else detect_lang(seg)
        prompt = seg if args.raw_prompt else build_prompt(seg, lang)
        out = args.out_dir / f"{i:02d}.{args.format}"
        print(f"[{i}/{len(segments)}] lang={lang} chars_prompt={len(prompt)} -> {out}")
        meta = synthesize(
            prompt,
            out_path=out,
            fmt=args.format,
            speech_rate=args.speech_rate,
            loudness_rate=args.loudness_rate,
            pitch_rate=args.pitch_rate,
            enable_subtitle=args.subtitle,
            speaker=args.speaker,
        )
        meta["segment"] = i
        meta["script"] = seg
        meta["lang"] = lang
        manifest.append(meta)
        print(
            f"  duration={meta.get('duration')}s original={meta.get('original_duration')}s "
            f"bytes={meta['bytes']}"
        )

    man_path = args.out_dir / "manifest.json"
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"清单: {man_path}")


if __name__ == "__main__":
    main()
