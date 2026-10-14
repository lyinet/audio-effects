---
name: 代码视频旁白 TTS
description: >-
  在代码讲解视频（如 Claude Opus 片子）做完后，用 Qwen / Gemini / Seed Audio
  把旁白脚本合成干声音频。多段长片须锁定音色一致性（Qwen/Gemini 固定 voice；Seed 用 ref-audio）。
---
# 代码视频旁白 TTS

默认 **`--provider auto`**：有密钥则优先 **Qwen → Gemini → Seed**。语言跟脚本走。

实现：`scripts/synthesize.py` + `scripts/providers/`。  
文档：`docs/API_QWEN_TTS.md`、`docs/API_GEMINI_TTS.md`、`docs/API_SEED_AUDIO.md`、`docs/VOICE_CONSISTENCY.md`。

Claude Code 安装后命令用 `${CLAUDE_SKILL_DIR}`；仓库内用 `scripts/synthesize.py`。

## 何时运行

片子/分镜完成需要旁白；或用户说配旁白 / TTS / 换 provider / 音色不一致。

## Provider 速查

| Provider | 密钥 | 默认音色 | 切段 | 锁声 |
|----------|------|----------|------|------|
| **qwen** | `DASHSCOPE_API_KEY` | `Cherry` | ≤600 字 | 全片同一 `--voice` |
| **gemini** | `GEMINI_API_KEY` | `Kore` | ~1800 字 | 同一 voice + 短 style |
| **seed** | `BYTEPLUS_SEED_API_KEY` | ref / speaker | ≤3000 字 / 120s | `--ref-audio` 或 `--speaker` |

## 推荐命令

```bash
pip install requests

# Qwen（Seed 无额度时）
export DASHSCOPE_API_KEY='...'
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" --provider qwen --voice Cherry \
  --file script.txt --concat

# Gemini
export GEMINI_API_KEY='...'
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" --provider gemini --voice Kore \
  --file script.txt --concat

# Seed 长片路线 A
export BYTEPLUS_SEED_API_KEY='...'
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" --provider seed --text "音色锁定样本。" \
  --save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" --provider seed --file script.txt \
  --ref-audio ./voice-refs/project-voice.mp3 --speech-rate -15 --concat
```

仓库内把 `${CLAUDE_SKILL_DIR}/scripts/synthesize.py` 换成 `scripts/synthesize.py`。

## 默认策略

1. 风格与正文分离（Gemini：`speech_metadata.style`；Seed：引号外方向；Qwen flash：靠 voice）。
2. 强制干声旁白，不加 BGM/SFX。
3. 长片锁音色：见上表；**勿**对 Qwen/Gemini 使用 `--ref-audio`。
4. 念稿预处理：去舞台指示与 Markdown；`npm install`→「N-P-M install」。
5. `python ... --list-voices` 查看内置音色名。

## 安装到 Claude Code

```bash
python scripts/install-claude-skill.py
python scripts/install-claude-skill.py --scope project
```

## 完成标准

- [ ] 已选可用 provider（auto 或显式），密钥未入库
- [ ] 干声；风格未被念出
- [ ] 超长已切段；需要时已 `--concat`
- [ ] 多段音色一致（同一 voice 或同一 ref-audio）
- [ ] 交付 `NN.*` + `manifest.json`（长片另有 `narration-full.*`）
