---
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
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" \
  --text "大家好，这是本片统一的教学旁白音色锁定样本。" \
  --save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15

# ② 各段同一锁 + 同一语速，拼接
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" \
  --file script.txt \
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
