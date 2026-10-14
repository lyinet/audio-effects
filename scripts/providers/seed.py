"""ByteDance / Volcengine Seed Audio 1.0 via openspeech."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import uuid
from pathlib import Path

import requests

DEFAULT_URL = "https://openspeech.bytedance.com/api/v3/tts/create"
DEFAULT_MODEL = "seed-audio-1.0"
REF_MAX_BYTES = 10 * 1024 * 1024
REF_MAX_SECONDS = 30

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


def get_api_key() -> str:
    key = os.environ.get("BYTEPLUS_SEED_API_KEY") or os.environ.get("VOLC_TTS_API_KEY")
    if not key:
        raise RuntimeError("缺少 BYTEPLUS_SEED_API_KEY 或 VOLC_TTS_API_KEY")
    return key


def build_prompt(script: str, lang: str, *, use_ref: bool) -> str:
    if use_ref:
        tmpl = STYLE_ZH_REF if lang == "zh" else STYLE_EN_REF
    else:
        tmpl = STYLE_ZH if lang == "zh" else STYLE_EN
    return tmpl.format(script=script)


def ensure_at_audio_token(prompt: str) -> str:
    if "@音频1" in prompt or "@音频 1" in prompt:
        return prompt
    return (
        "Match the exact voice timbre and delivery of @音频1. "
        "Same speaker identity throughout.\n" + prompt
    )


def load_ref_audio_b64(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"参考音频不存在: {path}")
    size = path.stat().st_size
    if size > REF_MAX_BYTES:
        raise ValueError(f"参考音频过大: {size} > 10MB ({path})")
    if size == 0:
        raise ValueError(f"参考音频为空: {path}")
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


def synthesize_seed(
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
        "provider": "seed",
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
