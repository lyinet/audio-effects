"""Qwen3 TTS via DashScope multimodal-generation HTTP API (no hard SDK dep)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import requests

from .common import convert_audio

QWEN_MAX_CHARS = 600
DEFAULT_MODEL = "qwen3-tts-flash"
DEFAULT_BASE = "https://dashscope.aliyuncs.com/api/v1"
GEN_PATH = "/services/aigc/multimodal-generation/generation"

# Common system voices (see docs); Cherry is the usual default.
QWEN_VOICES = {
    "Cherry": "阳光自然女声（默认）",
    "Serena": "温柔女声",
    "Elias": "沉稳男声",
    "Dylan": "北京口音男声",
    "Jada": "上海口音女声",
    "Sunny": "四川口音女声",
    "Neil": "专业男声",
    "Jennifer": "美式女声",
}


def get_api_key() -> str:
    key = os.environ.get("DASHSCOPE_API_KEY")
    if not key:
        raise RuntimeError("缺少 DASHSCOPE_API_KEY")
    return key


def language_type_for(lang: str) -> str:
    if lang == "zh":
        return "Chinese"
    if lang == "en":
        return "English"
    return "Auto"


def _endpoint() -> str:
    base = os.environ.get("DASHSCOPE_BASE_URL", DEFAULT_BASE).rstrip("/")
    if base.endswith("/services/aigc/multimodal-generation/generation"):
        return base
    return f"{base}{GEN_PATH}"


def synthesize_qwen(
    text: str,
    *,
    out_path: Path,
    voice: str = "Cherry",
    language_type: str = "Chinese",
    model: str | None = None,
    fmt: str = "mp3",
) -> dict:
    """Synthesize one chunk (≤600 chars). Returns meta; writes out_path."""
    if len(text) > QWEN_MAX_CHARS:
        raise ValueError(f"Qwen 单次文本超长：{len(text)} > {QWEN_MAX_CHARS}")

    key = get_api_key()
    model_id = model or os.environ.get("QWEN_TTS_MODEL", DEFAULT_MODEL)
    body = {
        "model": model_id,
        "input": {
            "text": text,
            "voice": voice,
            "language_type": language_type,
        },
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    r = requests.post(_endpoint(), headers=headers, json=body, timeout=180)
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"Qwen 非 JSON 响应 HTTP {r.status_code}: {r.text[:300]}") from None

    # DashScope errors often still return JSON with code/message
    output = data.get("output")
    if r.status_code != 200 or not output:
        raise RuntimeError(
            f"Qwen 合成失败 HTTP {r.status_code} "
            f"code={data.get('code')} message={data.get('message')}"
        )

    output = output or {}
    audio = output.get("audio") or {}
    raw: bytes | None = None
    audio_url = audio.get("url")
    if audio_url:
        raw = requests.get(audio_url, timeout=120).content
    elif audio.get("data"):
        import base64

        raw = base64.b64decode(audio["data"])
    elif output.get("audio_url"):
        raw = requests.get(output["audio_url"], timeout=120).content

    if not raw:
        raise RuntimeError(
            f"Qwen 响应无 audio.url/data，keys={list(data)} output_keys={list(output)}"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    # DashScope usually returns wav; convert if needed
    native_fmt = (audio.get("format") or "wav").lower().lstrip(".")
    if fmt.lower() == native_fmt or (fmt == "wav" and native_fmt in ("wav", "wave")):
        out_path.write_bytes(raw)
    else:
        with tempfile.NamedTemporaryFile(suffix=f".{native_fmt}", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(raw)
        try:
            convert_audio(tmp_path, out_path)
        finally:
            tmp_path.unlink(missing_ok=True)

    meta = {
        "provider": "qwen",
        "model": model_id,
        "voice": voice,
        "language_type": language_type,
        "out": str(out_path),
        "bytes": out_path.stat().st_size,
        "usage": data.get("usage"),
        "request_id": data.get("request_id"),
        "audio_url_ttl_hint": audio_url,
        "native_format": native_fmt,
    }
    meta_path = out_path.with_suffix(out_path.suffix + ".json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta
