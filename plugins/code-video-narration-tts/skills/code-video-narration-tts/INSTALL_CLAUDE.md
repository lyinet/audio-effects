# 在 Claude 中安装

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
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" \
  --text "大家好，这是本片统一的教学旁白音色锁定样本。" \
  --save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" \
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
