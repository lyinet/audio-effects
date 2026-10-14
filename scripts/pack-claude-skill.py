#!/usr/bin/env python3
"""Rebuild dist/code-video-narration-tts/ and the Claude zip (+ optional plugin skills)."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_NAME = "code-video-narration-tts"
VERSION = "0.5.0"
DIST = REPO / "dist" / SKILL_NAME
ZIP_PATH = REPO / "dist" / f"{SKILL_NAME}-claude.zip"
PLUGIN_SKILL = REPO / "plugins" / SKILL_NAME / "skills" / SKILL_NAME
TPL = Path(__file__).resolve().parent / "_pack_templates"


def _rm_and_mkdir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def build_skill_tree(dest: Path) -> None:
    _rm_and_mkdir(dest)
    shutil.copy2(TPL / "CLAUDE_SKILL.md", dest / "SKILL.md")
    shutil.copy2(TPL / "INSTALL_CLAUDE.md", dest / "INSTALL_CLAUDE.md")
    shutil.copy2(REPO / ".env.example", dest / ".env.example")

    scripts = dest / "scripts"
    scripts.mkdir()
    shutil.copy2(REPO / "scripts" / "synthesize.py", scripts / "synthesize.py")
    providers_src = REPO / "scripts" / "providers"
    if providers_src.is_dir():
        shutil.copytree(
            providers_src,
            scripts / "providers",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    shutil.copytree(REPO / "prompts", dest / "prompts")

    refs = dest / "references"
    refs.mkdir()
    for doc in (
        "API_SEED_AUDIO.md",
        "API_QWEN_TTS.md",
        "API_GEMINI_TTS.md",
        "VOICE_CONSISTENCY.md",
        "TTS_PROMPTING_BEST_PRACTICES.md",
    ):
        src = REPO / "docs" / doc
        if src.is_file():
            shutil.copy2(src, refs / doc)


def sync_plugin_skill() -> None:
    plugin_root = REPO / "plugins" / SKILL_NAME
    plugin_root.mkdir(parents=True, exist_ok=True)
    manifest_dir = plugin_root / ".claude-plugin"
    manifest_dir.mkdir(exist_ok=True)
    (manifest_dir / "plugin.json").write_text(
        "{\n"
        f'  "name": "{SKILL_NAME}",\n'
        f'  "version": "{VERSION}",\n'
        '  "description": "Dry narration TTS: Qwen / Gemini / Seed Audio with voice lock.",\n'
        '  "author": { "name": "lyinet" }\n'
        "}\n",
        encoding="utf-8",
    )
    build_skill_tree(PLUGIN_SKILL)


def write_marketplace() -> None:
    mp = REPO / ".claude-plugin"
    mp.mkdir(exist_ok=True)
    (mp / "marketplace.json").write_text(
        "{\n"
        '  "name": "audio-effects",\n'
        '  "description": "Audio / narration tooling for coding tutorial videos",\n'
        '  "owner": { "name": "lyinet" },\n'
        '  "plugins": [\n'
        "    {\n"
        f'      "name": "{SKILL_NAME}",\n'
        f'      "source": "./plugins/{SKILL_NAME}",\n'
        '      "description": "Qwen / Gemini / Seed dry VO with voice consistency",\n'
        f'      "version": "{VERSION}"\n'
        "    }\n"
        "  ]\n"
        "}\n",
        encoding="utf-8",
    )


def write_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in ("install-claude-skill.py", "install-claude-skill.sh"):
            src = REPO / "scripts" / name
            zf.write(src, arcname=name)
        zf.write(DIST / "INSTALL_CLAUDE.md", arcname="INSTALL_CLAUDE.md")
        for path in sorted(DIST.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                zf.write(path, arcname=f"{SKILL_NAME}/{path.relative_to(DIST).as_posix()}")


def main() -> None:
    if not (TPL / "CLAUDE_SKILL.md").is_file():
        raise SystemExit(f"missing templates under {TPL}")
    build_skill_tree(DIST)
    sync_plugin_skill()
    write_marketplace()
    write_zip()
    print(f"Built {DIST}")
    print(f"Built {ZIP_PATH} ({ZIP_PATH.stat().st_size} bytes)")
    print(f"Synced plugin skill → {PLUGIN_SKILL}")
    print(f"Wrote {REPO / '.claude-plugin' / 'marketplace.json'}")


if __name__ == "__main__":
    main()
