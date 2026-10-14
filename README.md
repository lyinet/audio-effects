# audio-effects

为代码讲解视频（尤其 Claude Opus 片子）生成**教学旁白**的工具与提示词库。

默认声音路线：字节 **Seed**（干声优先；Seed Audio 1.0 强制无 BGM/SFX），并支持 **Qwen TTS**、**Gemini Flash TTS**。语言跟脚本文本走（中/英）。

## 仓库结构

```
docs/                               # API / 锁声 / 提示词 / 维护
prompts/                            # 干声与参考锁模板
scripts/
  synthesize.py                     # Seed Audio CLI（--ref-audio / --concat）
  install-claude-skill.py           # 一键装到 ~/.claude/skills/ 或项目
  pack-claude-skill.py              # 重建 dist zip + 插件技能树
skills/code-video-narration-tts/    # 技能源（SKILL.md）
plugins/code-video-narration-tts/   # 可选 Claude Code 插件
.claude-plugin/marketplace.json     # 本地 marketplace 清单
dist/code-video-narration-tts-claude.zip
.env.example
CHANGELOG.md
```


## 安装到 Claude Code（CLI）

Claude app 无法跨目录安装本机 skills。用命令行装到 Claude Code：

```bash
# 仓库内
python scripts/install-claude-skill.py

# 或解压 dist zip 后
python3 install-claude-skill.py
# → 默认 ~/.claude/skills/code-video-narration-tts/
```

项目级：`python scripts/install-claude-skill.py --scope project`。详见包内 `INSTALL_CLAUDE.md`。

**注意**：Claude Code 读取 `~/.claude/skills/`；Claude app / Cowork 云端**不会**读该目录（需 claude.ai 上传或项目内 `.claude/skills/`）。

可选插件：`claude --plugin-dir plugins/code-video-narration-tts`，或本地 marketplace（见 `.claude-plugin/marketplace.json`）。

## 快速开始

### 一键试听（推荐）

```bash
cp .env.example .env   # 填入 BYTEPLUS_SEED_API_KEY
export $(grep -v '^#' .env | xargs)
pip install requests
python scripts/synthesize.py --text "接下来我们打开终端，输入 npm install。" --speech-rate -15
# 输出：narration-audio/01.mp3 + manifest.json
```

需要字级时间戳（对齐视频）时加 `--subtitle`。固定豆包 2.0 音色时加 `--speaker <音色ID>`。

### 长视频：锁定音色一致性

纯文本多段会**换声**。长片请先锁一版音色，再每段带同一参考：

```bash
# ① 短句生成锁文件（建议 ≤20s）
python scripts/synthesize.py --text "大家好，这是本片统一的教学旁白音色。" \
  --save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15

# ② 全片各段用同一锁 + 同一语速，最后拼接
python scripts/synthesize.py --file script.txt \
  --ref-audio ./voice-refs/project-voice.mp3 --speech-rate -15 --concat
```

完整说明（字段、`@音频N`、反模式、ffmpeg）：[`docs/VOICE_CONSISTENCY.md`](docs/VOICE_CONSISTENCY.md)。  
官方字段：[`docs/API_SEED_AUDIO.md`](docs/API_SEED_AUDIO.md)。

### 手工流程

1. 准备旁白脚本（按场景分段）。
2. 配置密钥（勿提交到仓库）：
   - Seed / 豆包：`BYTEPLUS_SEED_API_KEY`
   - Qwen：`DASHSCOPE_API_KEY`
   - Gemini：`GEMINI_API_KEY`
3. 打开 `skills/code-video-narration-tts/SKILL.md`，按其中流程合成。
4. 风格串优先用 `prompts/` 下对应文件；完整原理见 `docs/TTS_PROMPTING_BEST_PRACTICES.md`。

## 共用旁白风格（默认）

- **中文**：清晰沉稳的教学旁白，中等偏慢语速，吐字清楚，语气耐心专业，适合代码教程。
- **英文**：Calm clear educational narration, medium-slow pace, precise diction, warm professional coding instructor.

## 原则

1. **风格与正文分离**——指令字段放风格，念稿字段只放要说的话。
2. **代码视频用干声**——不要默认加音乐/音效。
3. **语言跟脚本**——不要整篇强行指定错误语言。
4. **长片锁音色**——多段必须同一 `--ref-audio` 或同一 `--speaker`。
5. **密钥不出库**。

## 许可证

私有仓库；未另行声明前仅供仓库所有者使用。
