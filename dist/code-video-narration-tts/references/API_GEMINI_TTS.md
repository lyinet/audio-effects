# Gemini Flash TTS（Interactions API）接入说明

> 默认模型：`gemini-3.8-flash-lite-tts`（便宜量产）  
> 高质量可换：`--model gemini-3.8-flash-tts`  
> 鉴权：`GEMINI_API_KEY` 或 `GOOGLE_API_KEY`  
> CLI：`python scripts/synthesize.py --provider gemini ...`

## 端点

```
POST https://generativelanguage.googleapis.com/v1beta/interactions
Header: x-goog-api-key: $GEMINI_API_KEY
```

## 请求体（单说话人 unary WAV）

```json
{
  "model": "gemini-3.8-flash-lite-tts",
  "input": [{
    "type": "user_input",
    "content": [{
      "type": "text",
      "text": "接下来我们打开终端，输入 npm install。",
      "annotations": [{
        "type": "speech_metadata",
        "style": "清晰沉稳的教学旁白，中等语速，吐字清楚，耐心专业，像资深工程师讲解代码"
      }]
    }]
  }],
  "response_format": { "type": "audio" },
  "generation_config": {
    "speech_config": [{ "voice": "Kore" }]
  }
}
```

关键规则（Gemini 3.8）：

- `text` = **只念正文**（勿把「慢慢说」写进 text，会被念出来）
- 风格放在 `speech_metadata.style`，且**全片用同一短串**
- `speech_config` 数组项指定 `voice`

Unary 默认返回 **WAV（RIFF）**；CLI 可 `--format mp3` 转码。

## 一键命令

```bash
export GEMINI_API_KEY='...'
pip install requests

# 默认 Kore + lite 模型 + prompts/gemini-style-zh.txt
python scripts/synthesize.py --provider gemini --text "接下来我们打开终端，输入 npm install。"

# 长片：同一 voice + 同一 style；自动按约 1800 字切段
python scripts/synthesize.py --provider gemini --voice Kore --file script.txt --concat

# 更高保真
python scripts/synthesize.py --provider gemini --model gemini-3.8-flash-tts --voice Charon --file script.txt --concat
```

## 音色一致性

1. 全程同一 `--voice`（教学推荐 **`Kore`** Firm；讲解向可用 **`Charon`** Informative）
2. 全程同一短 `style`（默认读 `prompts/gemini-style-zh.txt` / `en.txt`；可用 `--style` 覆盖，但不要每段换）
3. **不要**每段重发长「人设 / Director's Notes」——官方明确会导致漂声
4. Seed 的 `--ref-audio` **不适用** Gemini

## 切段

官方输入上限约 **8192 tokens**。CLI 保守按 **~1800 字符**按句切分，再 `--concat`。

## 限制摘要

| 项 | 值 |
|----|----|
| 默认模型 | `gemini-3.8-flash-lite-tts` |
| 输入 | 文本；输出音频 |
| unary 格式 | WAV（可转 mp3） |
| 风格字段 | `speech_metadata.style` |
| 依赖 | `requests`（可选 `google-genai`，CLI 不强制） |

官方：[Speech generation](https://ai.google.dev/gemini-api/docs/speech-generation)。
