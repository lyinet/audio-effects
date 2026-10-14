# audio-effects

为代码讲解视频（尤其 Claude Opus 片子）生成**教学旁白**的工具与提示词库。

支持 **Qwen TTS**（DashScope）、**Gemini Flash TTS**、字节 **Seed Audio**。`--provider auto` 按密钥优先：**Qwen → Gemini → Seed**（Seed 无额度时可直接用前两者）。语言跟脚本文本走（中/英）。

## 仓库结构

```
docs/                               # API / 锁声 / 提示词 / 维护
prompts/                            # 干声与风格模板
scripts/
  synthesize.py                     # 多 provider CLI
  providers/                        # seed / qwen / gemini
  install-claude-skill.py           # 一键装到 ~/.claude/skills/
  pack-claude-skill.py              # 重建 dist zip
skills/code-video-narration-tts/    # 技能源（SKILL.md）
plugins/code-video-narration-tts/   # 可选 Claude Code 插件
dist/code-video-narration-tts-claude.zip
.env.example
CHANGELOG.md
```

## 安装到 Claude Code（CLI）

```bash
python3 scripts/install-claude-skill.py
# 或解压 dist zip 后：python3 install-claude-skill.py
```

详见包内 `INSTALL_CLAUDE.md`。Claude app / Cowork **不会**读本机 `~/.claude/skills/`。

## 快速开始

```bash
cp .env.example .env   # 填入 DASHSCOPE_API_KEY 或 GEMINI_API_KEY（或 Seed 密钥）
export $(grep -v '^#' .env | xargs)
pip install requests
```

### Qwen（推荐，Seed 无额度时）

```bash
export DASHSCOPE_API_KEY='sk-...'
python3 scripts/synthesize.py --provider qwen --voice Cherry \
  --text "接下来我们打开终端，输入 npm install。"
# 长片：同一 voice + 自动 ≤600 字切段
python3 scripts/synthesize.py --provider qwen --voice Cherry --file script.txt --concat
```

文档：[`docs/API_QWEN_TTS.md`](docs/API_QWEN_TTS.md)

### Gemini Flash TTS

```bash
export GEMINI_API_KEY='...'
python3 scripts/synthesize.py --provider gemini --voice Kore \
  --text "接下来我们打开终端，输入 npm install。"
python3 scripts/synthesize.py --provider gemini --voice Kore --file script.txt --concat
# 更高保真：--model gemini-3.8-flash-tts
```

文档：[`docs/API_GEMINI_TTS.md`](docs/API_GEMINI_TTS.md)

### Seed Audio（有额度时）

```bash
export BYTEPLUS_SEED_API_KEY='...'
# 长片路线 A：锁文件 + --ref-audio
python3 scripts/synthesize.py --provider seed --text "本片统一音色锁定样本。" \
  --save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15
python3 scripts/synthesize.py --provider seed --file script.txt \
  --ref-audio ./voice-refs/project-voice.mp3 --speech-rate -15 --concat
```

文档：[`docs/API_SEED_AUDIO.md`](docs/API_SEED_AUDIO.md)、[`docs/VOICE_CONSISTENCY.md`](docs/VOICE_CONSISTENCY.md)

### 自动选 provider

```bash
python3 scripts/synthesize.py --text "试听一句。"   # auto：有哪个密钥用哪个
python3 scripts/synthesize.py --list-voices
```

## 音色一致性（摘要）

| Provider | 怎么锁 |
|----------|--------|
| **Qwen / Gemini** | 全片同一 `--voice`（+ Gemini 同一短 style） |
| **Seed** | 路线 A：`--ref-audio` 锁文件；或固定 `--speaker` |

## 原则

1. **风格与正文分离**——指令字段放风格，念稿字段只放要说的话。
2. **代码视频用干声**——不要默认加音乐/音效。
3. **语言跟脚本**——`--lang auto|zh|en`。
4. **长片锁音色**——按上表，勿混用 provider 的锁声参数。
5. **密钥不出库**。

## 许可证

私有仓库；未另行声明前仅供仓库所有者使用。
