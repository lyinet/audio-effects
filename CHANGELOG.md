# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 风格，版本号采用语义化版本。

## [0.2.1] - 2026-10-14

### Added

- Claude 安装包：`dist/code-video-narration-tts-claude.zip`（含 SKILL.md、scripts、prompts、API 参考与 INSTALL_CLAUDE.md）。

## [0.2.0] - 2026-10-14

### Added

- 按火山 openspeech 官方文档对齐：`docs/API_SEED_AUDIO.md`（字段、互斥规则、120s/3000 字、字幕、语速音量音调）。
- 可运行 CLI：`scripts/synthesize.py`（干声模板、代码读法预处理、`--subtitle` / `--speech-rate` / `--speaker`）。
- `.env.example`（`BYTEPLUS_SEED_API_KEY` / `VOLC_TTS_API_KEY` 别名）。

### Changed

- 默认路径明确为 **Seed Audio 1.0 + openspeech**（与当前可用密钥一致）；Doubao Seed-TTS 2.0 音色可通过同接口 `speaker` 选用。
- README 增加一键试听命令。

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
