---
name: 代码视频旁白 TTS
description: >-
  在代码讲解视频（如 Claude Opus 片子）做完后，用 SeedAudio / Doubao Seed-TTS / Qwen TTS / Gemini
  Flash TTS 把旁白脚本合成音频，并套用各家优化过的教学旁白提示词时使用。
---
# 代码视频旁白 TTS

把旁白脚本文本合成为可挂到代码讲解视频上的音频。默认走 **Seed 系**（优先干声旁白）；可选 Qwen、Gemini。语言跟脚本文本走。

完整提示词库与对照表见仓库 `docs/TTS_PROMPTING_BEST_PRACTICES.md` 与 `prompts/`（若本机有 [audio-effects](https://github.com/lyinet/audio-effects) 检出，优先读那里）。

## 何时运行

- Opus（或其他）片子/分镜已完成，手里有旁白稿。
- 用户说「配旁白」「TTS」「生成解说」「SeedAudio / Qwen / Gemini 配音」。

## 默认策略（最优化）

1. **风格与正文分离**：风格进各家「指令字段」；`text` / 引号内只放要念的字。
2. **共用旁白风格**（映射到各 provider）：
   - 中文：`清晰沉稳的教学旁白，中等偏慢语速，吐字清楚，语气耐心专业，适合代码教程。`
   - 英文：`Calm clear educational narration, medium-slow pace, precise diction, warm professional coding instructor.`
3. **Seed 产品分流**：
   - 只要干净念稿 → 优先 **Doubao Seed-TTS 2.0**（`text` + `context_texts[0]`）。
   - 用户点名 Seed Audio 1.0 → 用 **干声场景模板**（强制 No music / No SFX），台词放在引号内。
4. **Qwen**：单语脚本显式设 `language_type=Chinese|English`；有 instruct 能力时用 `instructions` + `optimize_instructions=true`；`[serious]` 等标签仅用于 `qwen-audio-3.0-tts-*`。
5. **Gemini 3.8**：`speech_metadata.style` 放风格；`text` 仅原文 + 可选 `<short pause>`；先试空 style，不够再加短 style 并整轨复用同一字符串。
6. **念稿预处理**：去掉舞台指示、Markdown、emoji；代码读法改写（`npm install`→「N-P-M install」；`src/index.ts`→「src slash index dot T-S」）。

## 输入

1. 旁白脚本（按场景分段更佳）
2. `provider`：`seed_tts` | `seed_audio`（默认若未指定：有豆包 TTS 密钥用 `seed_tts`，否则 `seed_audio` 干声）| `qwen` | `gemini` | `edge`
3. 输出目录（默认 `./narration-audio/`）、格式（默认 `mp3`；Gemini 多为 wav 再转）
4. 可选音色覆盖

也可设 `TTS_PROVIDER=...`。

Seed Audio HTTP 默认：`SEED_TTS_URL=https://openspeech.bytedance.com/api/v3/tts/create`（火山/openspeech 密钥）；BytePlus 国际端点需另配对应 key。

## 密钥

| Provider | 环境变量 |
|---|---|
| seed_tts / seed_audio | `BYTEPLUS_SEED_API_KEY` 或火山/豆包侧 `X-Api-Key`；端点可用 `SEED_TTS_URL` |
| qwen | `DASHSCOPE_API_KEY` |
| gemini | `GEMINI_API_KEY` |
| edge | 无 |

缺密钥就停，用 secret-request 补；永不写入仓库。

## 流程

1. 规范化脚本（去舞台指示；按 provider 切块：Qwen3≈600 字；Seed Audio≈2k–3k / ≤120s；Gemini 按段）
2. 选语言与风格串（中/英）
3. 按下方模板组请求 → 逐段落盘 `01.mp3`…
4. 多段 ffmpeg concat；ffprobe 实测时长
5. 交付：分段 + 可选整轨 + 清单（provider、模型、音色、style 原文、段数、时长）

## Provider 提示词模板（必用）

### A. Seed Audio 1.0（干声代码旁白）

中文 `text_prompt`：

```text
Clean dry studio narration only. No music, no sound effects, no ambience bed.
Language: Chinese.
Narrator: adult, clear Mandarin, warm professional coding instructor, medium-low pitch, calm measured pace, precise diction.
Read exactly: "{SCRIPT}"
```

英文同理，`Language: English`，Narrator 改为 clear American English / senior engineer explaining a PR。

要点：方向在引号外；只念引号内；禁止给教程加 BGM/SFX。

### B. Doubao Seed-TTS 2.0（推荐干声）

- `text` = 仅旁白
- `additions.context_texts` = `["清晰沉稳的教学旁白，中等偏慢语速，吐字清楚，语气耐心专业，适合代码教程。"]`（只生效第一个）
- `explicit_language`：`zh-cn` / `en`
- 默认音色示例（控制台核实）：中文 `zh_female_vv_uranus_bigtts`；英文 `en_female_dacey_uranus_bigtts`

### C. Qwen

优先 `qwen3-tts-instruct-flash` 或 CosyVoice 3.5（有 instruct 时）：

```text
instructions = 清晰沉稳的教学旁白，中等偏慢语速，吐字清楚，语气耐心专业，像编程老师讲解代码，不要夸张。
language_type = Chinese | English
voice = Cherry | Serena | Elias | Neil
optimize_instructions = true
```

仅 `qwen-audio-3.0-tts-*` 才在正文用 `[serious]` / `[curious]`；教程少用笑声类标签。

### D. Gemini 3.8 Flash TTS

- model：`gemini-3.8-flash-tts`（或 lite）
- `speech_metadata.style`：`calm, clear, medium-paced educational narrator; warm professional coding instructor; precise diction`
- 中文可用中文 style 短句；**不要**把 style 写进 `text`
- 音色：`Kore` / `Charon` / `Rasalgethi` / `Sadaltager`；回避 `Fenrir`/`Puck`
- 工作流：先空 style → 再复用同一短 style

### E. edge 回退

仅调试；正式成片回 Seed/Qwen/Gemini。

## 与 Opus 代码视频衔接

1. 上游：分镜完成 + 旁白稿（带 scene id）
2. 本 skill：文→音；默认不重剪视频
3. 文件名对齐场景（`scene-03.mp3`）
4. 不擅自改措辞；朗读灾难先标出再问

## 失败处理

401/403→密钥/地域；429→单段退避；字段变更→查官方 docs。保留成功段。

## 完成标准

- [ ] 风格在指令字段，正文无可念舞台指示
- [ ] 使用了对应语言的优化旁白 style
- [ ] Seed Audio 路径强制干声
- [ ] 分段齐全 + 时长实测；密钥未进仓库
