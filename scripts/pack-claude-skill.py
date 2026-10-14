#!/usr/bin/env python3
"""Rebuild dist/code-video-narration-tts/ and the Claude zip (+ optional plugin skills)."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_NAME = "code-video-narration-tts"
DIST = REPO / "dist" / SKILL_NAME
ZIP_PATH = REPO / "dist" / f"{SKILL_NAME}-claude.zip"
PLUGIN_SKILL = (
    REPO / "plugins" / SKILL_NAME / "skills" / SKILL_NAME
)

# Claude-oriented SKILL (Chinese body + English trigger keywords + CLAUDE_SKILL_DIR)
CLAUDE_SKILL_MD = '''---
name: code-video-narration-tts
description: >
  Use after a Claude Opus (or similar) code-explanation video is drafted, to
  synthesize dry educational narration audio via Volcengine openspeech Seed
  Audio 1.0 (optional Qwen/Gemini). Triggers: 旁白, TTS, SeedAudio, narration,
  配音, voiceover, 音色一致 for coding tutorials. 长片须用参考音色锁一致性。
---

# 代码视频旁白 TTS

为代码讲解视频生成**干声**教学旁白（无 BGM/SFX）。默认：**Seed Audio 1.0**（openspeech）。

脚本路径一律用 `${CLAUDE_SKILL_DIR}`，安装后不依赖当前工作目录。

## 何时使用

- Opus / 代码片子分镜完成，需要旁白
- 用户说：旁白 / TTS / SeedAudio / 配音 / 音色不一致

## 官方约束

- `POST https://openspeech.bytedance.com/api/v3/tts/create`，头 `X-Api-Key`
- `model`: `seed-audio-1.0`；`text_prompt` ≤ **3000** 字；单次 ≤ **120** 秒
- 音色锁在 `references[]`：每项 `speaker` / `audio_data` / `audio_url` **三选一**
- Prompt 写 `@音频1`…`@音频3`；参考单条 ≤30s / ≤10MB，最多 3 条
- 详解：`references/API_SEED_AUDIO.md`、`references/VOICE_CONSISTENCY.md`

环境变量：`BYTEPLUS_SEED_API_KEY` 或 `VOLC_TTS_API_KEY`。

## 长片锁声（默认路线 A）

纯 `text_prompt` 无参考时，每次可能换音色。长片流程：

```bash
pip install requests
export BYTEPLUS_SEED_API_KEY='...'

# ① 短句生成锁文件（建议 8–20s）
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" \\
  --text "大家好，这是本片统一的教学旁白音色锁定样本。" \\
  --save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15

# ② 各段同一锁 + 同一语速，拼接
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" \\
  --file script.txt \\
  --ref-audio ./voice-refs/project-voice.mp3 --speech-rate -15 --concat
```

备选：全程同一 `--speaker=<豆包2.0/复刻ID>`，不要再叠参考音频。

## 默认策略

1. 风格在引号外，台词在 `Read exactly: "..."` 内（见 `prompts/seed-audio-dry-*.txt`）
2. 强制干声：No music / No SFX / No ambience
3. 教学语速可 `speech_rate=-15`；**全片同一语速/音量/音调**
4. 对齐视频：`--subtitle`，保存字级时间戳
5. 念稿预处理：去舞台指示与 Markdown；`npm install`→「N-P-M install」

## 完成标准

- [ ] openspeech + `seed-audio-1.0`
- [ ] 干声模板；风格未被念出
- [ ] 未超 3000 字 / 120s；超长已切段
- [ ] 多段同一 `--ref-audio` 或同一 `--speaker`
- [ ] 交付音频 + manifest；密钥未入库
'''

INSTALL_CLAUDE_MD = '''# 在 Claude 中安装

## 推荐：命令行一键安装（Claude Code）

解压 zip 后，在解压目录执行：

```bash
python3 install-claude-skill.py
# 或
./install-claude-skill.sh
```

默认装到 **用户级**：`~/.claude/skills/code-video-narration-tts/`（所有本地项目可用）。

常用参数：

```bash
# 仅当前项目
python3 install-claude-skill.py --scope project

# 指定项目根目录
python3 install-claude-skill.py --scope project --project-dir /path/to/repo

# 从 zip / 目录安装
python3 install-claude-skill.py --from code-video-narration-tts-claude.zip
python3 install-claude-skill.py --from ./code-video-narration-tts

# 覆盖重装 / 卸载 / 演练
python3 install-claude-skill.py --force
python3 install-claude-skill.py --uninstall
python3 install-claude-skill.py --dry-run
```

在完整仓库内也可：

```bash
python scripts/install-claude-skill.py
```

安装后：配置 `BYTEPLUS_SEED_API_KEY`，Claude Code 新开会话或 `/reload-skills`。

### 长片锁声（路线 A）

见包内 `references/VOICE_CONSISTENCY.md`。摘要：

```bash
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" \\
  --text "大家好，这是本片统一的教学旁白音色锁定样本。" \\
  --save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" \\
  --file script.txt --ref-audio ./voice-refs/project-voice.mp3 --speech-rate -15 --concat
```

## Claude Code vs Claude app / Cowork

| 环境 | 本机 `~/.claude/skills/` | 怎么用本 skill |
|------|--------------------------|----------------|
| **Claude Code**（终端） | ✅ 会读取 | 用上面的 CLI 安装即可 |
| **Claude app / Cowork（云端）** | ❌ **不会**读本机该目录 | 在 [claude.ai](https://claude.ai) 上传 skill，**或**把技能放进已克隆仓库的 `.claude/skills/`（`--scope project`），再在云端打开该项目 |

请勿以为「在 Claude app 里跨目录拷贝」能装到本机 skills；那正是本安装器要解决的问题。

## 可选：插件方式（Claude Code）

仓库已带最小插件布局：

```bash
# 单次会话加载
claude --plugin-dir /path/to/audio-effects/plugins/code-video-narration-tts

# 或把本仓库加为本地 marketplace 后再安装（需能访问该 git 路径）
claude plugin marketplace add /path/to/audio-effects
claude plugin install code-video-narration-tts@audio-effects
```

私有 GitHub 无额外鉴权文档时，**仍以 `install-claude-skill.py` 为主路径**。

## 手动复制（不推荐）

若无法运行 Python：把 `code-video-narration-tts/` 整夹复制到：

- 用户级：`~/.claude/skills/code-video-narration-tts/`
- 项目级：`<项目>/.claude/skills/code-video-narration-tts/`

确认含 `SKILL.md`、`scripts/synthesize.py`、`prompts/`、`references/`。

## 不要打进包的内容

真实 API Key、`.env`、生成的 `*.mp3`、`voice-refs/`。
'''


def _rm_and_mkdir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def build_skill_tree(dest: Path) -> None:
    _rm_and_mkdir(dest)
    (dest / "SKILL.md").write_text(CLAUDE_SKILL_MD, encoding="utf-8")
    (dest / "INSTALL_CLAUDE.md").write_text(INSTALL_CLAUDE_MD, encoding="utf-8")
    shutil.copy2(REPO / ".env.example", dest / ".env.example")

    scripts = dest / "scripts"
    scripts.mkdir()
    shutil.copy2(REPO / "scripts" / "synthesize.py", scripts / "synthesize.py")

    shutil.copytree(REPO / "prompts", dest / "prompts")

    refs = dest / "references"
    refs.mkdir()
    for doc in (
        "API_SEED_AUDIO.md",
        "VOICE_CONSISTENCY.md",
        "TTS_PROMPTING_BEST_PRACTICES.md",
    ):
        shutil.copy2(REPO / "docs" / doc, refs / doc)


def sync_plugin_skill() -> None:
    plugin_root = REPO / "plugins" / SKILL_NAME
    plugin_root.mkdir(parents=True, exist_ok=True)
    manifest_dir = plugin_root / ".claude-plugin"
    manifest_dir.mkdir(exist_ok=True)
    (manifest_dir / "plugin.json").write_text(
        """{\n"""
        f'  "name": "{SKILL_NAME}",\n'
        '  "version": "0.4.0",\n'
        '  "description": "Dry Seed Audio narration TTS for coding tutorial videos (voice-lock route A).",\n'
        '  "author": { "name": "lyinet" }\n'
        "}\n",
        encoding="utf-8",
    )
    build_skill_tree(PLUGIN_SKILL)


def write_marketplace() -> None:
    mp = REPO / ".claude-plugin"
    mp.mkdir(exist_ok=True)
    (mp / "marketplace.json").write_text(
        """{\n"""
        '  "name": "audio-effects",\n'
        '  "description": "Audio / narration tooling for coding tutorial videos",\n'
        '  "owner": { "name": "lyinet" },\n'
        '  "plugins": [\n'
        "    {\n"
        f'      "name": "{SKILL_NAME}",\n'
        f'      "source": "./plugins/{SKILL_NAME}",\n'
        '      "description": "Seed Audio dry VO + voice-lock for long videos",\n'
        '      "version": "0.4.0"\n'
        "    }\n"
        "  ]\n"
        "}\n",
        encoding="utf-8",
    )


def write_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Installers at zip root (unzip and run without full repo)
        for name in ("install-claude-skill.py", "install-claude-skill.sh"):
            src = REPO / "scripts" / name
            zf.write(src, arcname=name)
        zf.write(DIST / "INSTALL_CLAUDE.md", arcname="INSTALL_CLAUDE.md")
        for path in sorted(DIST.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=f"{SKILL_NAME}/{path.relative_to(DIST).as_posix()}")


def main() -> None:
    build_skill_tree(DIST)
    # Keep a copy of installer docs in dist already via INSTALL_CLAUDE.md
    sync_plugin_skill()
    write_marketplace()
    write_zip()
    print(f"Built {DIST}")
    print(f"Built {ZIP_PATH} ({ZIP_PATH.stat().st_size} bytes)")
    print(f"Synced plugin skill → {PLUGIN_SKILL}")
    print(f"Wrote {REPO / '.claude-plugin' / 'marketplace.json'}")


if __name__ == "__main__":
    main()
