#!/usr/bin/env python3
"""Multi-provider dry narration TTS: Qwen / Gemini / Seed Audio.

Usage:
  export DASHSCOPE_API_KEY=...   # preferred when Seed has no quota
  # or export GEMINI_API_KEY=...
  # or export BYTEPLUS_SEED_API_KEY=...

  python scripts/synthesize.py --text "接下来我们打开终端，输入 npm install。"
  python scripts/synthesize.py --provider qwen --voice Cherry --file script.txt --concat
  python scripts/synthesize.py --provider gemini --voice Kore --file script.txt --concat

Default --provider auto: first available key in order qwen → gemini → seed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

try:
    import requests  # noqa: F401
except ImportError:
    print("需要 requests：pip install requests", file=sys.stderr)
    sys.exit(1)

from providers.common import (  # noqa: E402
    chunk_by_sentences,
    detect_lang,
    ffmpeg_concat,
    preprocess_script,
    split_paragraphs,
)
from providers.gemini import (  # noqa: E402
    GEMINI_CHUNK_CHARS,
    GEMINI_VOICES,
    synthesize_gemini,
)
from providers.qwen import (  # noqa: E402
    QWEN_MAX_CHARS,
    QWEN_VOICES,
    language_type_for,
    synthesize_qwen,
)
from providers.seed import (  # noqa: E402
    REF_MAX_SECONDS,
    build_prompt,
    build_references,
    ensure_at_audio_token,
    synthesize_seed,
)


def resolve_provider(explicit: str) -> str:
    if explicit != "auto":
        return explicit
    if os.environ.get("DASHSCOPE_API_KEY"):
        return "qwen"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("BYTEPLUS_SEED_API_KEY") or os.environ.get("VOLC_TTS_API_KEY"):
        return "seed"
    print(
        "未找到可用密钥。请设置 DASHSCOPE_API_KEY（Qwen）、"
        "GEMINI_API_KEY / GOOGLE_API_KEY（Gemini）或 "
        "BYTEPLUS_SEED_API_KEY（Seed）。",
        file=sys.stderr,
    )
    sys.exit(2)


def default_voice(provider: str, lang: str, override: str | None) -> str:
    if override:
        return override
    if provider == "qwen":
        return "Cherry"
    if provider == "gemini":
        return "Kore"
    return ""


def prompts_dir() -> Path | None:
    for cand in (
        _SCRIPTS.parent / "prompts",
        _SCRIPTS.parent.parent / "prompts",
    ):
        if cand.is_dir():
            return cand
    return None


def expand_chunks(segments: list[str], provider: str) -> list[str]:
    if provider == "qwen":
        limit = QWEN_MAX_CHARS
    elif provider == "gemini":
        limit = GEMINI_CHUNK_CHARS
    else:
        limit = 2500
    out: list[str] = []
    for seg in segments:
        out.extend(chunk_by_sentences(seg, limit))
    return out or segments


def main() -> None:
    ap = argparse.ArgumentParser(
        description="干声教学旁白合成（Qwen / Gemini / Seed Audio）"
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="单段旁白原文")
    g.add_argument("--file", type=Path, help="多段脚本文件（空行分段）")
    ap.add_argument(
        "--provider",
        choices=["auto", "qwen", "gemini", "seed"],
        default="auto",
        help="默认 auto：按密钥优先 qwen → gemini → seed",
    )
    ap.add_argument("--out-dir", type=Path, default=Path("./narration-audio"))
    ap.add_argument(
        "--format",
        default=None,
        help="输出格式：seed 默认 mp3；qwen/gemini 默认 wav（可转 mp3）",
    )
    ap.add_argument("--speech-rate", type=int, default=0, help="仅 Seed：-50..100")
    ap.add_argument("--loudness-rate", type=int, default=0, help="仅 Seed")
    ap.add_argument("--pitch-rate", type=int, default=0, help="仅 Seed")
    ap.add_argument(
        "--voice",
        default=None,
        help="Qwen/Gemini 音色名（如 Cherry / Kore）；Seed 时可作 --speaker 别名",
    )
    ap.add_argument(
        "--speaker",
        default=None,
        help="Seed：豆包 2.0 / 复刻音色 ID（references[0].speaker）",
    )
    ap.add_argument("--ref-audio", type=Path, default=None, help="仅 Seed：本地参考音频锁")
    ap.add_argument("--ref-url", default=None, help="仅 Seed：参考音频 URL")
    ap.add_argument(
        "--save-as-voice-lock",
        type=Path,
        default=None,
        help="仅 Seed：把第 1 段输出存为锁文件",
    )
    ap.add_argument("--concat", action="store_true", help="ffmpeg 拼成 narration-full.*")
    ap.add_argument("--subtitle", action="store_true", help="仅 Seed：字级时间戳")
    ap.add_argument("--lang", choices=["auto", "zh", "en"], default="auto")
    ap.add_argument(
        "--model",
        default=None,
        help="覆盖模型 ID",
    )
    ap.add_argument(
        "--style",
        default=None,
        help="Gemini：覆盖 speech_metadata.style；默认读 prompts/gemini-style-*.txt",
    )
    ap.add_argument("--raw-prompt", action="store_true", help="仅 Seed：不套干声模板")
    ap.add_argument(
        "--list-voices",
        action="store_true",
        help="列出内置 Qwen/Gemini 音色提示后退出",
    )
    args = ap.parse_args()

    if args.list_voices:
        print("Qwen voices:")
        for k, v in QWEN_VOICES.items():
            print(f"  {k}: {v}")
        print("Gemini voices:")
        for k, v in GEMINI_VOICES.items():
            print(f"  {k}: {v}")
        print("Seed: 使用 --speaker=<豆包2.0/复刻ID> 或 --ref-audio 锁文件")
        return

    provider = resolve_provider(args.provider)
    print(f"provider={provider} (requested={args.provider})")

    if provider != "seed":
        if args.ref_audio or args.ref_url or args.save_as_voice_lock:
            print(
                f"--ref-audio / --ref-url / --save-as-voice-lock 仅适用于 Seed，"
                f"当前 provider={provider}。Qwen/Gemini 请全程使用同一 --voice。",
                file=sys.stderr,
            )
            sys.exit(2)
        if args.subtitle or args.raw_prompt:
            print(
                f"--subtitle / --raw-prompt 仅适用于 Seed（当前 provider={provider}）",
                file=sys.stderr,
            )
            sys.exit(2)
        if args.speech_rate or args.loudness_rate or args.pitch_rate:
            print(
                f"提示: speech_rate/loudness/pitch 仅 Seed 生效，已忽略（provider={provider}）",
                file=sys.stderr,
            )
        if args.speaker and not args.voice:
            print(
                "提示: --speaker 是 Seed 字段；Qwen/Gemini 请用 --voice",
                file=sys.stderr,
            )

    fmt = args.format
    if fmt is None:
        fmt = "mp3" if provider == "seed" else "wav"

    raw = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    if not raw.strip() and not args.list_voices:
        print("文本为空", file=sys.stderr)
        sys.exit(2)

    segments = split_paragraphs(raw) if args.file else [preprocess_script(raw)]
    chunks = expand_chunks(segments, provider)

    voice = default_voice(provider, "zh", args.voice)
    seed_speaker = args.speaker
    if provider == "seed" and seed_speaker is None and args.voice:
        seed_speaker = args.voice

    references = None
    if provider == "seed":
        try:
            references = build_references(
                speaker=seed_speaker, ref_audio=args.ref_audio, ref_url=args.ref_url
            )
        except (ValueError, FileNotFoundError) as e:
            print(str(e), file=sys.stderr)
            sys.exit(2)

    manifest = []
    out_paths: list[Path] = []
    pdir = prompts_dir()

    for i, seg in enumerate(chunks, 1):
        lang = args.lang if args.lang != "auto" else detect_lang(seg)
        if not args.voice:
            voice = default_voice(provider, lang, None)
        out = args.out_dir / f"{i:02d}.{fmt}"
        print(
            f"[{i}/{len(chunks)}] provider={provider} lang={lang} "
            f"voice={voice or seed_speaker or '-'} chars={len(seg)} -> {out}"
        )

        if provider == "qwen":
            meta = synthesize_qwen(
                seg,
                out_path=out,
                voice=voice,
                language_type=language_type_for(lang),
                model=args.model,
                fmt=fmt,
            )
        elif provider == "gemini":
            meta = synthesize_gemini(
                seg,
                out_path=out,
                voice=voice,
                style=args.style,
                lang=lang,
                model=args.model,
                fmt=fmt,
                prompts_dir=pdir,
            )
        else:
            use_ref = references is not None
            if args.raw_prompt:
                prompt = seg
                if use_ref:
                    prompt = ensure_at_audio_token(prompt)
            else:
                prompt = build_prompt(seg, lang, use_ref=use_ref)
            meta = synthesize_seed(
                prompt,
                out_path=out,
                fmt=fmt,
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
            f"  bytes={meta.get('bytes')} "
            f"voice={meta.get('voice') or meta.get('reference_mode')}"
        )

        if i == 1 and args.save_as_voice_lock and provider == "seed":
            lock = args.save_as_voice_lock
            lock.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(out, lock)
            print(f"  voice-lock saved: {lock}")
            od = meta.get("original_duration")
            if isinstance(od, (int, float)) and od > REF_MAX_SECONDS:
                print(
                    f"  警告: 锁文件时长 {od}s > {REF_MAX_SECONDS}s",
                    file=sys.stderr,
                )

    man_path = args.out_dir / "manifest.json"
    man_path.parent.mkdir(parents=True, exist_ok=True)
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"清单: {man_path}")

    if args.concat and out_paths:
        full = args.out_dir / f"narration-full.{fmt}"
        ffmpeg_concat(out_paths, full)
        print(f"拼接: {full}")


if __name__ == "__main__":
    if "--list-voices" in sys.argv and not any(
        a == "--text" or a == "--file" or a.startswith("--text=") or a.startswith("--file=")
        for a in sys.argv
    ):
        sys.argv.extend(["--text", "_"])
    main()
