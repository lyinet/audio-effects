---
name: 代码视频旁白 TTS
description: >-
  在代码讲解视频（如 Claude Opus 片子）做完后，用火山 openspeech Seed Audio 1.0
  （及 Qwen / Gemini）把旁白脚本合成音频时使用。
---
# 代码视频旁白 TTS

默认：**Seed Audio 1.0**，端点 `POST https://openspeech.bytedance.com/api/v3/tts/create`，鉴权头 `X-Api-Key`。可选 Qwen / Gemini。语言跟脚本走。

仓库实现：`scripts/synthesize.py`；字段说明：`docs/API_SEED_AUDIO.md`；提示词：`prompts/`。

## 何时运行

片子/分镜完成，需要旁白；或用户说配旁白 / TTS / SeedAudio。

## 官方约束（必须遵守）

- `model`: `seed-audio-1.0`
- `text_prompt` ≤ **3000** 字符；单次音频 ≤ **120** 秒（`original_duration` 计费）
- `speaker` / `audio_data` / `audio_url` **三选一**；图片参考不可与音频参考混用
- 参考音频在 prompt 里写 **`@音频1`…`@音频3`**（与 `references` 顺序一致）
- `audio_config`：`format`（旁白默认 `mp3`）、`sample_rate`、`speech_rate`（-50..100）、`loudness_rate`、`pitch_rate`、`enable_subtitle`
- 响应：`audio`（Base64）或 `url`（约 2h）；排障看 `X-Tt-Logid`

## 默认策略

1. 风格与正文分离：干声方向在引号外，台词在 `Read exactly: "..."` 内（见 `prompts/seed-audio-dry-*.txt`）。
2. 强制干声：No music / No SFX / No ambience。
3. 教学旁白可设 `speech_rate=-15` 左右略慢。
4. 要对齐视频：`enable_subtitle=true`，保存返回的字级时间戳。
5. 需要固定豆包 2.0 音色：传 `speaker=<音色ID>`，不要同时传参考音频。
6. 念稿预处理：去舞台指示与 Markdown；`npm install`→「N-P-M install」等（脚本已做基础替换）。

## 推荐执行方式

密钥：`BYTEPLUS_SEED_API_KEY` 或 `VOLC_TTS_API_KEY`。

```bash
python scripts/synthesize.py --text "旁白原文" --speech-rate -15 --subtitle
# 或多段：
python scripts/synthesize.py --file script.txt --out-dir ./narration-audio
```

无仓库检出时，按 `docs/API_SEED_AUDIO.md` 用同一 JSON 自行请求。

## 其它 provider

- **Qwen / Gemini**：见 `docs/TTS_PROMPTING_BEST_PRACTICES.md`；密钥 `DASHSCOPE_API_KEY` / `GEMINI_API_KEY`。
- **edge**：仅无密钥调试。

## 与 Opus 片子衔接

1. 输入带 `scene_id` 的分段旁白。
2. 输出 `NN.mp3` + `manifest.json`（含 duration / subtitle）。
3. 用 subtitle 时间戳挂轨道；默认不重剪画面。

## 完成标准

- [ ] 使用 openspeech + `seed-audio-1.0`
- [ ] 干声模板，风格未被念出
- [ ] 未超 3000 字 / 120s；超长已切段
- [ ] 交付音频 + manifest；密钥未入库
