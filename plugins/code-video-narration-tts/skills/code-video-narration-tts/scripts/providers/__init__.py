"""TTS providers: seed (openspeech), qwen (DashScope), gemini (Interactions API)."""

from .common import (
    detect_lang,
    preprocess_script,
    split_paragraphs,
    chunk_by_sentences,
    ffmpeg_concat,
    convert_audio,
    load_style_prompt,
)
from .seed import synthesize_seed
from .qwen import synthesize_qwen, QWEN_MAX_CHARS, QWEN_VOICES
from .gemini import synthesize_gemini, GEMINI_CHUNK_CHARS, GEMINI_VOICES

__all__ = [
    "detect_lang",
    "preprocess_script",
    "split_paragraphs",
    "chunk_by_sentences",
    "ffmpeg_concat",
    "convert_audio",
    "load_style_prompt",
    "synthesize_seed",
    "synthesize_qwen",
    "synthesize_gemini",
    "QWEN_MAX_CHARS",
    "QWEN_VOICES",
    "GEMINI_CHUNK_CHARS",
    "GEMINI_VOICES",
]
