#!/usr/bin/env python3
"""Install the code-video-narration-tts Claude skill (cross-platform, stdlib only).

Default target: ~/.claude/skills/code-video-narration-tts (Claude Code user scope).

Examples:
  python scripts/install-claude-skill.py
  python scripts/install-claude-skill.py --scope project
  python install-claude-skill.py --from code-video-narration-tts-claude.zip
  python scripts/install-claude-skill.py --uninstall
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

SKILL_NAME = "code-video-narration-tts"
REQUIRED_FILES = ("SKILL.md",)


def _home_claude_skills() -> Path:
    return Path.home() / ".claude" / "skills"


def _resolve_target(scope: str, project_dir: Path | None) -> Path:
    if scope == "user":
        return _home_claude_skills() / SKILL_NAME
    root = (project_dir or Path.cwd()).resolve()
    return root / ".claude" / "skills" / SKILL_NAME


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _repo_root_from_script() -> Path | None:
    # scripts/install-claude-skill.py → repo root
    candidate = _script_dir().parent
    if (candidate / "scripts" / "synthesize.py").is_file() and (
        candidate / "skills" / SKILL_NAME / "SKILL.md"
    ).is_file():
        return candidate
    return None


def _looks_like_skill_dir(path: Path) -> bool:
    return path.is_dir() and (path / "SKILL.md").is_file()


def _find_skill_inside(root: Path) -> Path | None:
    """Return a skill directory under root (itself or one level down)."""
    if _looks_like_skill_dir(root):
        return root
    nested = root / SKILL_NAME
    if _looks_like_skill_dir(nested):
        return nested
    # zip may extract to a single top folder
    if root.is_dir():
        children = [p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]
        for child in children:
            if _looks_like_skill_dir(child):
                return child
            nested2 = child / SKILL_NAME
            if _looks_like_skill_dir(nested2):
                return nested2
    return None


def _build_from_repo(repo: Path, staging: Path) -> Path:
    """Assemble the same layout as dist/code-video-narration-tts/ into staging."""
    dest = staging / SKILL_NAME
    dest.mkdir(parents=True, exist_ok=True)

    skill_src = repo / "skills" / SKILL_NAME / "SKILL.md"
    # Prefer packaged Claude SKILL if present (may include English frontmatter)
    packaged = repo / "dist" / SKILL_NAME / "SKILL.md"
    if packaged.is_file():
        shutil.copy2(packaged, dest / "SKILL.md")
    else:
        shutil.copy2(skill_src, dest / "SKILL.md")

    for name in (".env.example",):
        src = repo / name
        if src.is_file():
            shutil.copy2(src, dest / name)

    install_doc = repo / "dist" / SKILL_NAME / "INSTALL_CLAUDE.md"
    if not install_doc.is_file():
        # fall back: may live at docs or we write a stub later
        install_doc = repo / "INSTALL_CLAUDE.md"
    if install_doc.is_file():
        shutil.copy2(install_doc, dest / "INSTALL_CLAUDE.md")

    scripts_dest = dest / "scripts"
    scripts_dest.mkdir(exist_ok=True)
    shutil.copy2(repo / "scripts" / "synthesize.py", scripts_dest / "synthesize.py")

    prompts_src = repo / "prompts"
    if prompts_src.is_dir():
        shutil.copytree(prompts_src, dest / "prompts", dirs_exist_ok=True)

    refs_dest = dest / "references"
    refs_dest.mkdir(exist_ok=True)
    for doc in (
        "API_SEED_AUDIO.md",
        "VOICE_CONSISTENCY.md",
        "TTS_PROMPTING_BEST_PRACTICES.md",
    ):
        src = repo / "docs" / doc
        if src.is_file():
            shutil.copy2(src, refs_dest / doc)

    # Prefer already-built dist tree if complete (keeps Claude-tuned SKILL + INSTALL)
    dist_skill = repo / "dist" / SKILL_NAME
    if _looks_like_skill_dir(dist_skill) and (dist_skill / "scripts" / "synthesize.py").is_file():
        # Replace staging with a clean copy of dist
        shutil.rmtree(dest)
        shutil.copytree(dist_skill, dest)

    return dest


def _extract_zip(zip_path: Path, staging: Path) -> Path:
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(staging)
    found = _find_skill_inside(staging)
    if not found:
        raise SystemExit(
            f"Zip 内未找到含 SKILL.md 的技能目录（期望 {SKILL_NAME}/）：{zip_path}"
        )
    return found


def locate_payload(from_path: Path | None) -> tuple[Path, tempfile.TemporaryDirectory | None]:
    """Return (skill_dir, tempdir_or_None). Caller must clean tempdir when done."""
    tmp: tempfile.TemporaryDirectory | None = None

    if from_path is not None:
        src = from_path.expanduser().resolve()
        if not src.exists():
            raise SystemExit(f"找不到 --from 路径：{src}")
        if src.is_file() and src.suffix.lower() == ".zip":
            tmp = tempfile.TemporaryDirectory(prefix="claude-skill-")
            skill = _extract_zip(src, Path(tmp.name))
            return skill, tmp
        if src.is_dir():
            found = _find_skill_inside(src)
            if not found:
                raise SystemExit(f"目录内未找到 SKILL.md：{src}")
            return found, None
        raise SystemExit(f"--from 须为 zip 或目录：{src}")

    # 1) Same directory as this script (zip-root layout: install next to skill folder)
    here = _script_dir()
    beside = here / SKILL_NAME
    if _looks_like_skill_dir(beside):
        return beside, None
    if _looks_like_skill_dir(here):
        return here, None
    # CWD (user unzipped and ran from that folder)
    cwd_skill = Path.cwd() / SKILL_NAME
    if _looks_like_skill_dir(cwd_skill):
        return cwd_skill, None

    # 2) Repo dist/
    repo = _repo_root_from_script()
    if repo is not None:
        dist_skill = repo / "dist" / SKILL_NAME
        if _looks_like_skill_dir(dist_skill) and (
            dist_skill / "scripts" / "synthesize.py"
        ).is_file():
            return dist_skill, None
        # 3) Build from repo sources
        tmp = tempfile.TemporaryDirectory(prefix="claude-skill-build-")
        skill = _build_from_repo(repo, Path(tmp.name))
        return skill, tmp

    raise SystemExit(
        "无法定位技能包。请在仓库内运行，或使用：\n"
        "  python install-claude-skill.py --from code-video-narration-tts-claude.zip"
    )


def _copy_tree(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def _validate_skill(skill_dir: Path) -> None:
    for name in REQUIRED_FILES:
        if not (skill_dir / name).is_file():
            raise SystemExit(f"技能包缺少 {name}：{skill_dir}")
    syn = skill_dir / "scripts" / "synthesize.py"
    if not syn.is_file():
        print(f"警告：未找到 scripts/synthesize.py（{skill_dir}）", file=sys.stderr)


def _print_next_steps(target: Path) -> None:
    print()
    print("下一步：")
    print("  1. 设置环境变量 BYTEPLUS_SEED_API_KEY（或 VOLC_TTS_API_KEY）")
    print("  2. Claude Code：新开会话，或执行 /reload-skills（插件则 /reload-plugins）")
    print("  3. 长片旁白（路线 A）：先锁声再分段")
    print(
        f'       python "${{CLAUDE_SKILL_DIR}}/scripts/synthesize.py" '
        '--text "大家好，这是本片统一的教学旁白音色锁定样本。" '
        "--save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15"
    )
    print(
        f'       python "${{CLAUDE_SKILL_DIR}}/scripts/synthesize.py" '
        "--file script.txt --ref-audio ./voice-refs/project-voice.mp3 "
        "--speech-rate -15 --concat"
    )
    print(f"  4. 已安装到：{target}")
    print()
    print("注意：Claude Code 读取 ~/.claude/skills/ 与项目 .claude/skills/。")
    print("      Claude app / Cowork 云端不会读本机该目录；请用 claude.ai 上传 skill，")
    print("      或把项目技能放进已克隆仓库的 .claude/skills/。详见 INSTALL_CLAUDE.md。")


def install(
    *,
    scope: str,
    project_dir: Path | None,
    from_path: Path | None,
    force: bool,
    dry_run: bool,
) -> Path:
    skill_dir, tmp = locate_payload(from_path)
    try:
        _validate_skill(skill_dir)
        target = _resolve_target(scope, project_dir)
        print(f"来源：{skill_dir}")
        print(f"目标：{target}（scope={scope}）")
        if target.exists() and not force:
            raise SystemExit(
                f"目标已存在：{target}\n请加 --force 覆盖，或先 --uninstall。"
            )
        if dry_run:
            print("[dry-run] 将复制完整技能树（SKILL.md、scripts/、prompts/、references/ 等）")
            return target
        _copy_tree(skill_dir, target)
        print(f"已安装：{target}")
        _print_next_steps(target)
        return target
    finally:
        if tmp is not None:
            tmp.cleanup()


def uninstall(
    *,
    scope: str,
    project_dir: Path | None,
    dry_run: bool,
) -> None:
    target = _resolve_target(scope, project_dir)
    print(f"将移除：{target}")
    if not target.exists():
        print("目标不存在，无需卸载。")
        return
    if dry_run:
        print("[dry-run] 将删除上述目录")
        return
    shutil.rmtree(target)
    print("已卸载。")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="安装 code-video-narration-tts Claude 技能到本机 skills 目录"
    )
    parser.add_argument(
        "--scope",
        choices=("user", "project"),
        default="user",
        help="user → ~/.claude/skills/…；project → <cwd|project-dir>/.claude/skills/…",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=None,
        help="project scope 时的项目根目录（默认当前工作目录）",
    )
    parser.add_argument(
        "--from",
        dest="from_path",
        type=Path,
        default=None,
        help="zip 包或已解压的技能目录",
    )
    parser.add_argument("--force", action="store_true", help="覆盖已存在的安装目录")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要执行的操作")
    parser.add_argument("--uninstall", action="store_true", help="删除已安装的技能目录")
    args = parser.parse_args(argv)

    if args.uninstall:
        uninstall(scope=args.scope, project_dir=args.project_dir, dry_run=args.dry_run)
        return 0

    install(
        scope=args.scope,
        project_dir=args.project_dir,
        from_path=args.from_path,
        force=args.force,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("已中断", file=sys.stderr)
        raise SystemExit(130)
