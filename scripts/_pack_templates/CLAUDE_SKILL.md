---
name: code-video-narration-tts
description: >
  Use after a Claude Opus (or similar) code-explanation video is drafted, to
  synthesize dry educational narration via Qwen (DashScope), Gemini Flash TTS,
  or Seed Audio. Triggers: 旁白, TTS, Qwen, Gemini, SeedAudio, narration,
  配音, voiceover, 音色一致. Long videos must lock voice (Qwen/Gemini: same
  --voice; Seed: --ref-audio).
---

# 代码视频旁白 TTS

干声教学旁白。默认 **`--provider auto`**：密钥优先 **Qwen → Gemini → Seed**。

脚本路径用 `${CLAUDE_SKILL_DIR}`。

## 密钥

- Qwen：`DASHSCOPE_API_KEY`（可选 `DASHSCOPE_BASE_URL`）
- Gemini：`GEMINI_API_KEY` 或 `GOOGLE_API_KEY`
- Seed：`BYTEPLUS_SEED_API_KEY`

## 命令

```bash
pip install requests

# Qwen
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" --provider qwen --voice Cherry \
  --file script.txt --concat

# Gemini（默认 Kore + gemini-3.8-flash-lite-tts）
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" --provider gemini --voice Kore \
  --file script.txt --concat

# Seed 路线 A
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" --provider seed --text "音色锁定样本。" \
  --save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" --provider seed --file script.txt \
  --ref-audio ./voice-refs/project-voice.mp3 --speech-rate -15 --concat
```

## 锁声

| Provider | 做法 |
|----------|------|
| Qwen | 全片同一 `--voice`（≤600 字/段自动切） |
| Gemini | 同一 `--voice` + 同一短 style（~1800 字/段） |
| Seed | `--ref-audio` 或 `--speaker` |

参考：`references/API_QWEN_TTS.md`、`API_GEMINI_TTS.md`、`API_SEED_AUDIO.md`、`VOICE_CONSISTENCY.md`。

## 完成标准

- [ ] 可用 provider；干声；已切段/拼接
- [ ] 多段音色一致；密钥未入库
