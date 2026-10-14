# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 风格，版本号采用语义化版本。

## [0.1.1] - 2026-10-14

### Changed

- 实测：火山/openspeech 风格的 `X-Api-Key` 可用端点为 `https://openspeech.bytedance.com/api/v3/tts/create`；BytePlus 东南亚端点对该密钥返回 Invalid X-Api-Key。
- 干声旁白试听通过（中文 npm install 示例，约 11s）。

## [0.1.0] - 2026-10-14

### Added

- 初始化仓库：README、维护文档、更新日志。
- 收录 Seed Audio / Doubao Seed-TTS、Qwen TTS、Gemini Flash TTS 旁白提示词最佳实践调研文档。
- 增加可复用提示词模板目录 `prompts/`。
- 增加 Cursor 技能 `skills/code-video-narration-tts`（默认 Seed 干声旁白，可选 Qwen / Gemini）。
