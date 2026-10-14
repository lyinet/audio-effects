"""Gemini Flash TTS via Interactions REST API (google-genai optional)."""

from __future__ import annotations

import base64
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import requests

from .common import convert_audio, load_style_prompt

GEMINI_CHUNK_CHARS = 1800  # under 8192 token input; keep safe for long旁白
DEFAULT_MODEL = "gemini-3.8-flash-lite-tts"
INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"

GEMINI_VOICES = {
    "Kore": "Firm — 教学旁白默认",
    "Charon": "Informative — 讲解向男声",
    "Rasalgethi": "Informative",
    "Sadaltager": "Knowledgeable",
    "Iapetus": "Clear",
    "Erinome": "Clear",
    "Gacrux": "Mature",
    "Sulafat": "Warm",
    "Achernar": "Soft",
    "Puck": "Upbeat（旁白慎用）",
    "Fenrir": "Excitable（旁白慎用）",
}


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("缺少 GEMINI_API_KEY 或 GOOGLE_API_KEY")
    return key


def default_style(lang: str, prompts_dir: Path | None = None) -> str:
    style = load_style_prompt("gemini-style", lang, prompts_dir=prompts_dir)
    if style:
        return style
    if lang == "zh":
        return "清晰沉稳的教学旁白，中等语速，吐字清楚，耐心专业，像资深工程师讲解代码"
    return (
        "calm, clear, medium-paced educational narrator; "
        "warm professional coding instructor; precise diction; documentary explainer tone"
    )


def _extract_audio_b64(data: dict[str, Any]) -> str | None:
    """Pull base64 audio from Interactions response (SDK shape or raw steps)."""
    # Convenience field some SDKs expose as nested dict
    oa = data.get("output_audio")
    if isinstance(oa, dict) and oa.get("data"):
        return oa["data"]
    if isinstance(oa, str) and oa:
        return oa

    steps = data.get("steps") or []
    last: str | None = None
    for step in steps:
        if not isinstance(step, dict):
            continue
        if step.get("type") and step.get("type") != "model_output":
            # still scan content
            pass
        for part in step.get("content") or []:
            if not isinstance(part, dict):
                continue
            if part.get("type") in ("audio", "output_audio") and part.get("data"):
                last = part["data"]
            # Some payloads use mime_type + data
            mime = (part.get("mime_type") or part.get("mimeType") or "").lower()
            if "audio" in mime and part.get("data"):
                last = part["data"]
    if last:
        return last

    # outputs / candidates fallbacks
    for key in ("outputs", "output"):
        block = data.get(key)
        if isinstance(block, list):
            for item in block:
                if isinstance(item, dict) and item.get("data") and "audio" in str(
                    item.get("type", "audio")
                ):
                    return item["data"]
        elif isinstance(block, dict) and block.get("data"):
            return block["data"]
    return None


def synthesize_gemini(
    text: str,
    *,
    out_path: Path,
    voice: str = "Kore",
    style: str | None = None,
    lang: str = "zh",
    model: str | None = None,
    fmt: str = "wav",
    prompts_dir: Path | None = None,
) -> dict:
    """Unary Interactions TTS; returns WAV by default (RIFF)."""
    if len(text) > GEMINI_CHUNK_CHARS * 2:
        # Soft guard; caller should chunk
        pass

    key = get_api_key()
    model_id = model or os.environ.get("GEMINI_TTS_MODEL", DEFAULT_MODEL)
    style_str = style if style is not None else default_style(lang, prompts_dir=prompts_dir)

    content_item: dict[str, Any] = {"type": "text", "text": text}
    if style_str.strip():
        content_item["annotations"] = [
            {"type": "speech_metadata", "style": style_str.strip()}
        ]

    body = {
        "model": model_id,
        "input": [
            {
                "type": "user_input",
                "content": [content_item],
            }
        ],
        "response_format": {"type": "audio"},
        "generation_config": {
            "speech_config": [{"voice": voice}],
        },
    }
    headers = {
        "x-goog-api-key": key,
        "Content-Type": "application/json",
    }
    r = requests.post(INTERACTIONS_URL, headers=headers, json=body, timeout=300)
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"Gemini 非 JSON 响应 HTTP {r.status_code}: {r.text[:300]}") from None

    if r.status_code != 200:
        err = data.get("error") or data
        raise RuntimeError(
            f"Gemini 合成失败 HTTP {r.status_code}: {json.dumps(err, ensure_ascii=False)[:500]}"
        )

    b64 = _extract_audio_b64(data)
    if not b64:
        raise RuntimeError(
            f"Gemini 响应无 audio data，top_keys={list(data)} "
            f"steps={len(data.get('steps') or [])}"
        )

    raw = base64.b64decode(b64)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Unary Interactions returns WAV (RIFF) by default
    want = fmt.lower().lstrip(".")
    if want in ("wav", "wave") or (raw[:4] == b"RIFF" and want == "wav"):
        if want in ("wav", "wave"):
            out_path.write_bytes(raw)
        else:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)
                tmp.write(raw)
            try:
                convert_audio(tmp_path, out_path)
            finally:
                tmp_path.unlink(missing_ok=True)
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(raw)
        try:
            convert_audio(tmp_path, out_path)
        finally:
            tmp_path.unlink(missing_ok=True)

    meta = {
        "provider": "gemini",
        "model": model_id,
        "voice": voice,
        "style": style_str,
        "out": str(out_path),
        "bytes": out_path.stat().st_size,
        "interaction_id": data.get("id") or data.get("name"),
    }
    meta_path = out_path.with_suffix(out_path.suffix + ".json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta
