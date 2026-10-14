# Seed Audio 1.0 HTTP 非流式接口（官方对齐）

来源：火山引擎 / openspeech 开发文档（用户提供，2026-10-14 对齐入库）。

## 端点

`POST https://openspeech.bytedance.com/api/v3/tts/create`

鉴权（新版控制台）：请求头 `X-Api-Key`（必选）。建议同时传 `X-Api-Request-Id`（UUID）。

旧版 `X-Api-App-Id` + `X-Api-Access-Key` 将下线，本仓库默认只用新版 Key。

## 请求体要点

| 字段 | 必选 | 说明 |
|------|------|------|
| `model` | 是 | 当前：`seed-audio-1.0`（多语种 + 时间轴自然语言控制） |
| `text_prompt` | 是 | 提示词或待合成文本，**≤3000 字符** |
| `references` | 否 | 参考资源列表；纯文本模式不传 |
| `speaker` | 否 | 音色 ID（豆包语音合成 2.0 音色或复刻音色）；与 `audio_data` / `audio_url` **互斥** |
| `audio_data` / `audio_url` | 否 | 参考音频 Base64 或 URL；与 `speaker` 互斥 |
| `image_data` / `image_url` | 否 | 参考图片；**不可与音频参考混用** |
| `audio_config` | 否 | 输出配置，见下 |
| `watermark` | 否 | 显式/隐式水印 |

### `audio_config`

| 字段 | 默认/范围 | 说明 |
|------|-----------|------|
| `format` | 默认 `wav`；可选 `wav`/`mp3`/`pcm`/`ogg_opus` | 成片旁白建议 `mp3` |
| `sample_rate` | mp3 默认 `44100`；wav/pcm 默认 `40000` | 见官方取值表 |
| `speech_rate` | `0`，范围 `[-50,100]` | `-50`=0.5x，`100`=2.0x；教学旁白可试 `-10`～`-20` |
| `loudness_rate` | `0`，范围 `[-50,100]` | 音量 |
| `pitch_rate` | `0`，范围 `[-12,12]` | 音调 |
| `enable_subtitle` | `false` | `true` 时返回字级时间戳（利于视频对齐） |

### 参考音频规则

- `text_prompt` 内用 `@音频1`、`@音频2`、`@音频3`（与上传顺序严格对应）
- 最多 3 条，单条 ≤30s、≤10MB；格式 wav/mp3/pcm/ogg_opus
- 图片最多 1 张，≤10MB；jpeg/png/webp

## 响应体

| 字段 | 说明 |
|------|------|
| `code` / `message` | 错误码与详情 |
| `audio` | Base64 音频 |
| `duration` | 处理后时长（秒） |
| `original_duration` | 原始时长（秒），**计费依据**，上限 120s |
| `url` | 临时下载地址，约 **2 小时**有效 |
| `subtitle` | 仅 `enable_subtitle=true` 时返回 |

响应头 `X-Tt-Logid`：排障用。

## 代码视频旁白推荐用法

1. **纯文本干声**：不传 `references`；`text_prompt` 用干声模板（见 `prompts/seed-audio-dry-*.txt`），台词放在引号内。
2. **固定音色**：传 `speaker`（豆包 2.0 音色 ID），不要同时传参考音频。
3. **对齐剪辑**：`enable_subtitle=true`，用返回的 word timestamps 挂到 Opus 分镜。
4. **语速**：默认 `speech_rate=0`；偏快则设负数（如 `-15`）。
5. **切段**：单次 ≤120s、`text_prompt` ≤3000 字；长旁白按场景拆请求后 ffmpeg concat。

## 环境变量

```bash
export BYTEPLUS_SEED_API_KEY='...'   # 或 VOLC_TTS_API_KEY
export SEED_TTS_URL='https://openspeech.bytedance.com/api/v3/tts/create'  # 默认即此
```
