#!/usr/bin/env python3
"""Seed Audio 1.0 dry narration synthesizer (openspeech HTTP non-streaming).

Usage:
  export BYTEPLUS_SEED_API_KEY=...
  python scripts/synthesize.py --text "接下来我们打开终端，输入 npm install。"
  python scripts/synthesize.py --file script.txt --out-dir ./narration-audio --subtitle

Voice consistency (long videos):
  # 1) One-time lock take (or reuse first good segment)
  python scripts/synthesize.py --text "这是用于锁定音色的短旁白。" \
    --save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15
  # 2) Every later segment uses the same lock file
  python scripts/synthesize.py --file script.txt --ref-audio ./voice-refs/project-voice.mp3 \
    --speech-rate -15 --concat
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

try:
    import requests
except ImportError:
    print("需要 requests：pip install requests", file=sys.stderr)
    sys.exit(1)

DEFAULT_URL = "https://openspeech.bytedance.com/api/v3/tts/create"
DEFAULT_MODEL = "seed-audio-1.0"
REF_MAX_BYTES = 10 * 1024 * 1024  # 10 MB official cap
REF_MAX_SECONDS = 30  # official per-clip cap

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

# When locking to a reference clip / speaker via @音频1
STYLE_ZH_REF = (
    "Clean dry studio narration only. No music, no sound effects, no ambience bed, "
    "no applause, no crowd.\n"
    "Language: Chinese.\n"
    "Use the exact same voice timbre, pitch, and delivery as @音频1. "
    "Keep one consistent narrator identity; do not invent a new speaker.\n"
    "Narrator: adult, clear Mandarin, warm professional coding instructor, "
    "calm measured pace, precise diction.\n"
    'Read exactly: "{script}"'
)
STYLE_EN_REF = (
    "Clean dry studio narration only. No music, no sound effects, no ambience.\n"
    "Language: English.\n"
    "Use the exact same voice timbre, pitch, and delivery as @音频1. "
    "Keep one consistent narrator identity; do not invent a new speaker.\n"
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

    def path_repl(m: re.Match) -> str:
        p = m.group(0)
        p = p.replace("/", " slash ").replace(".", " dot ")
        p = re.sub(r"\bts\b", "T-S", p, flags=re.I)
        p = re.sub(r"\bjs\b", "J-S", p, flags=re.I)
        return p

    t = re.sub(r"\b[\w.-]+/[\w./-]+\b", path_repl, t)
    return re.sub(r"\s+", " ", t).strip()


def build_prompt(script: str, lang: str, *, use_ref: bool) -> str:
    if use_ref:
        tmpl = STYLE_ZH_REF if lang == "zh" else STYLE_EN_REF
    else:
        tmpl = STYLE_ZH if lang == "zh" else STYLE_EN
    return tmpl.format(script=script)


def ensure_at_audio_token(prompt: str) -> str:
    """Official API expects @音频N when references are present."""
    if "@音频1" in prompt or "@音频 1" in prompt:
        return prompt
    return (
        "Match the exact voice timbre and delivery of @音频1. "
        "Same speaker identity throughout.\n" + prompt
    )


def get_api_key() -> str:
    key = os.environ.get("BYTEPLUS_SEED_API_KEY") or os.environ.get("VOLC_TTS_API_KEY")
    if not key:
        print("缺少 BYTEPLUS_SEED_API_KEY 或 VOLC_TTS_API_KEY", file=sys.stderr)
        sys.exit(2)
    return key


def load_ref_audio_b64(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"参考音频不存在: {path}")
    size = path.stat().st_size
    if size > REF_MAX_BYTES:
        raise ValueError(f"参考音频过大: {size} > 10MB ({path})")
    if size == 0:
        raise ValueError(f"参考音频为空: {path}")
    # Soft duration check via ffprobe when available
    try:
        out = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            dur = float(out.stdout.strip())
            if dur > REF_MAX_SECONDS + 0.5:
                raise ValueError(
                    f"参考音频时长 {dur:.1f}s 超过官方上限 {REF_MAX_SECONDS}s，请截短后再用"
                )
    except FileNotFoundError:
        pass
    return base64.b64encode(path.read_bytes()).decode("ascii")


def build_references(
    *,
    speaker: str | None,
    ref_audio: Path | None,
    ref_url: str | None,
) -> list[dict] | None:
    """Official shape: references[] items; each item ONE of speaker/audio_data/audio_url."""
    modes = sum(1 for x in (speaker, ref_audio, ref_url) if x)
    if modes == 0:
        return None
    if modes > 1:
        raise ValueError("--speaker / --ref-audio / --ref-url 互斥，只能选一种锁定方式")
    if speaker:
        return [{"speaker": speaker}]
    if ref_url:
        return [{"audio_url": ref_url}]
    assert ref_audio is not None
    return [{"audio_data": load_ref_audio_b64(ref_audio)}]


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
    references: list[dict] | None = None,
    url: str | None = None,
) -> dict:
    key = get_api_key()
    endpoint = url or os.environ.get("SEED_TTS_URL", DEFAULT_URL)
    if sample_rate is None:
        sample_rate = 44100 if fmt == "mp3" else 40000

    prompt = text_prompt
    if references:
        prompt = ensure_at_audio_token(prompt)

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
        "text_prompt": prompt,
        "audio_config": audio_config,
    }
    if references:
        body["references"] = references

    if len(prompt) > 3000:
        raise ValueError(f"text_prompt 超长：{len(prompt)} > 3000")

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
        "used_references": bool(references),
        "reference_mode": (
            "speaker"
            if references and "speaker" in references[0]
            else "audio_data"
            if references and "audio_data" in references[0]
            else "audio_url"
            if references and "audio_url" in references[0]
            else None
        ),
    }
    meta_path = out_path.with_suffix(out_path.suffix + ".json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def split_segments(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n|^## .+$", text, flags=re.M)
    segs = [preprocess_script(p) for p in parts if preprocess_script(p)]
    return segs or [preprocess_script(text)]


def ffmpeg_concat(paths: list[Path], out_path: Path) -> None:
    if not paths:
        raise ValueError("没有可拼接的音频")
    if len(paths) == 1:
        shutil.copy2(paths[0], out_path)
        return
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("需要 ffmpeg 才能 --concat")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        list_path = Path(f.name)
        for p in paths:
            esc = str(p.resolve()).replace("'", r"'\''")
            f.write(f"file '{esc}'\n")
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c",
            "copy",
            str(out_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            cmd2 = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c:a",
                "libmp3lame" if out_path.suffix.lower() == ".mp3" else "pcm_s16le",
                str(out_path),
            ]
            proc2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=180)
            if proc2.returncode != 0:
                raise RuntimeError(
                    f"ffmpeg concat 失败:\n{proc.stderr[-500:]}\n---\n{proc2.stderr[-500:]}"
                )
    finally:
        list_path.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Seed Audio dry narration synthesizer（支持参考音色锁定）"
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="单段旁白原文")
    g.add_argument("--file", type=Path, help="多段脚本文件（空行分段）")
    ap.add_argument("--out-dir", type=Path, default=Path("./narration-audio"))
    ap.add_argument("--format", default="mp3", choices=["mp3", "wav", "pcm", "ogg_opus"])
    ap.add_argument("--speech-rate", type=int, default=0, help="-50..100，教学可试 -15")
    ap.add_argument("--loudness-rate", type=int, default=0)
    ap.add_argument("--pitch-rate", type=int, default=0)
    ap.add_argument(
        "--speaker",
        default=None,
        help="豆包 2.0 / 复刻音色 ID（写入 references[0].speaker，与参考音频互斥）",
    )
    ap.add_argument(
        "--ref-audio",
        type=Path,
        default=None,
        help="本地参考音频（≤30s/≤10MB）→ references[0].audio_data；prompt 自动含 @音频1",
    )
    ap.add_argument(
        "--ref-url",
        default=None,
        help="参考音频 URL → references[0].audio_url；与 --ref-audio/--speaker 互斥",
    )
    ap.add_argument(
        "--save-as-voice-lock",
        type=Path,
        default=None,
        help="把本批第 1 段输出复制为音色锁文件（建议 voice-refs/project-voice.mp3）",
    )
    ap.add_argument(
        "--concat",
        action="store_true",
        help="多段合成后 ffmpeg 拼成 out-dir/narration-full.<format>",
    )
    ap.add_argument("--subtitle", action="store_true", help="开启字级时间戳")
    ap.add_argument("--lang", choices=["auto", "zh", "en"], default="auto")
    ap.add_argument("--raw-prompt", action="store_true", help="不套干声模板，text_prompt 原样发送")
    args = ap.parse_args()

    try:
        references = build_references(
            speaker=args.speaker, ref_audio=args.ref_audio, ref_url=args.ref_url
        )
    except (ValueError, FileNotFoundError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

    use_ref = references is not None
    raw = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    segments = split_segments(raw) if args.file else [preprocess_script(raw)]

    manifest = []
    out_paths: list[Path] = []
    for i, seg in enumerate(segments, 1):
        lang = args.lang if args.lang != "auto" else detect_lang(seg)
        if args.raw_prompt:
            prompt = seg
            if use_ref:
                prompt = ensure_at_audio_token(prompt)
        else:
            prompt = build_prompt(seg, lang, use_ref=use_ref)
        out = args.out_dir / f"{i:02d}.{args.format}"
        mode = "plain"
        if references:
            mode = next(iter(references[0].keys()), "ref")
        print(
            f"[{i}/{len(segments)}] lang={lang} ref={mode} "
            f"chars_prompt={len(prompt)} -> {out}"
        )
        meta = synthesize(
            prompt,
            out_path=out,
            fmt=args.format,
            speech_rate=args.speech_rate,
            loudness_rate=args.loudness_rate,
            pitch_rate=args.pitch_rate,
            enable_subtitle=args.subtitle,
            references=references,
        )
        meta["segment"] = i
        meta["script"] = seg
        meta["lang"] = lang
        manifest.append(meta)
        out_paths.append(out)
        print(
            f"  duration={meta.get('duration')}s original={meta.get('original_duration')}s "
            f"bytes={meta['bytes']}"
        )

        if i == 1 and args.save_as_voice_lock:
            lock = args.save_as_voice_lock
            lock.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(out, lock)
            print(f"  voice-lock saved: {lock}")
            od = meta.get("original_duration")
            if isinstance(od, (int, float)) and od > REF_MAX_SECONDS:
                print(
                    f"  警告: 锁文件时长 {od}s > {REF_MAX_SECONDS}s，"
                    f"后续作 --ref-audio 可能被拒；请用短句单独生成锁文件。",
                    file=sys.stderr,
                )

    man_path = args.out_dir / "manifest.json"
    man_path.parent.mkdir(parents=True, exist_ok=True)
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"清单: {man_path}")

    if args.concat and out_paths:
        full = args.out_dir / f"narration-full.{args.format}"
        ffmpeg_concat(out_paths, full)
        print(f"拼接: {full}")


if __name__ == "__main__":
    main()
