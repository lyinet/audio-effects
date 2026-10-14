# Qwen TTS（DashScope）接入说明

> 模型默认：`qwen3-tts-flash`  
> 鉴权：环境变量 `DASHSCOPE_API_KEY`  
> 可选：`DASHSCOPE_BASE_URL`（默认北京 `https://dashscope.aliyuncs.com/api/v1`）  
> CLI：`python scripts/synthesize.py --provider qwen ...`

## 端点

```
POST {DASHSCOPE_BASE_URL}/services/aigc/multimodal-generation/generation
```

默认完整 URL：

`https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation`

国际站可改：

```bash
export DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/api/v1
```

请求头：

```
Authorization: Bearer $DASHSCOPE_API_KEY
Content-Type: application/json
```

## 请求体（非流式）

```json
{
  "model": "qwen3-tts-flash",
  "input": {
    "text": "接下来我们打开终端，输入 npm install。",
    "voice": "Cherry",
    "language_type": "Chinese"
  }
}
```

| 字段 | 说明 |
|------|------|
| `text` | 要念的正文，**最长 600 字符**（本仓库会自动按句切分） |
| `voice` | 系统音色，全片保持同一名称即可锁声 |
| `language_type` | `Chinese` / `English` / `Auto`（单语建议显式指定） |

响应：`output.audio.url`（约 **24 小时**有效）或流式 Base64。CLI 会下载 URL 并按需转成 `--format`（默认 `wav`）。

## 一键命令

```bash
export DASHSCOPE_API_KEY='sk-...'
pip install requests

# 短句试听（默认 Cherry）
python scripts/synthesize.py --provider qwen --text "接下来我们打开终端，输入 npm install。"

# 长脚本：自动按 ≤600 字切段 + 拼接；音色锁 = 全程同一 --voice
python scripts/synthesize.py --provider qwen --voice Cherry --file script.txt --concat

# 转 mp3
python scripts/synthesize.py --provider qwen --file script.txt --format mp3 --concat
```

`--provider auto` 时，若存在 `DASHSCOPE_API_KEY`，会优先选 Qwen（先于 Gemini / Seed）。

## 音色一致性

Qwen **没有** Seed 那种参考音频锁。长片一致的做法：

1. 全片固定同一个 `--voice`（如 `Cherry`）
2. 固定同一 `language_type`（由 `--lang zh|en` 映射）
3. 不要中途换 voice / model

常用音色（节选）：`Cherry`（默认）、`Serena`、`Elias`、`Neil`、`Jennifer`。完整列表见官方 Voice list；CLI：`python scripts/synthesize.py --list-voices`。

## 与 instruct 模型

`qwen3-tts-instruct-flash` / CosyVoice 可用 `instructions` 控风格；本仓库 **0.5.0 先落地 flash**。风格串见 `prompts/qwen-instructions-*.txt`，后续可加 `--instructions`。

## 限制摘要

| 项 | 值 |
|----|----|
| 单次 `text` | ≤ **600** 字符 |
| 音频 URL TTL | ~24h |
| 依赖 | 仅需 `requests`（可选 dashscope SDK，CLI 不强制） |

官方文档：[Qwen TTS API](https://www.alibabacloud.com/help/en/model-studio/qwen-tts-api)、[QwenCloud TTS](https://docs.qwencloud.com/developer-guides/speech/tts)。
