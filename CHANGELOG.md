# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 风格，版本号采用语义化版本。

## [0.5.0] - 2026-10-14

### Added

- 多 provider CLI：`--provider auto|qwen|gemini|seed`（auto 优先 Qwen → Gemini → Seed）。
- Qwen（DashScope）HTTP 实现：`qwen3-tts-flash`，单次 ≤600 字自动切段，`--voice` 锁声。
- Gemini Flash TTS Interactions API：默认 `gemini-3.8-flash-lite-tts` + `Kore`，短 `speech_metadata.style`，~1800 字切段。
- 文档：`docs/API_QWEN_TTS.md`、`docs/API_GEMINI_TTS.md`；`VOICE_CONSISTENCY.md` 补充 Qwen/Gemini。
- `scripts/providers/` 模块；`--list-voices`、`--model`、`--style`。

### Changed

- 默认 provider 改为 **auto**（有 DashScope/Gemini 密钥时不再强行走无额度的 Seed）。
- Seed 专用：`--ref-audio` / `--save-as-voice-lock` / `--subtitle` / `speech_rate`；用在其它 provider 上会明确报错或忽略。
- `.env.example`、README、SKILL、Claude 包同步至 v0.5.0。

## [0.4.0] - 2026-10-14

### Added

- Claude 技能 CLI 安装器：`scripts/install-claude-skill.py`（及 `.sh` 包装），支持 `--scope user|project`、`--from` zip/目录、`--force`、`--dry-run`、`--uninstall`。
- 打包脚本：`scripts/pack-claude-skill.py`；zip 根目录自带安装器，解压即可安装。
- 可选 Claude 插件：`plugins/code-video-narration-tts/` + 仓库根 `.claude-plugin/marketplace.json`。
- `INSTALL_CLAUDE.md`：CLI 优先说明，并标明 Claude app / Cowork 不读 `~/.claude/skills/`。

### Changed

- `SKILL.md`（源与 Claude 包）命令示例改用 `${CLAUDE_SKILL_DIR}/scripts/synthesize.py`；长片默认仍为路线 A（锁文件 + `--ref-audio`）。
- 重建 `dist/code-video-narration-tts-claude.zip`。

## [0.3.0] - 2026-10-14

### Added

- 长片音色一致性文档：`docs/VOICE_CONSISTENCY.md`（参考音频锁 / 固定 speaker / 反模式 / ffmpeg）。
- CLI：`--ref-audio`、`--ref-url`、`--save-as-voice-lock`、`--concat`；参考资源按官方写入 `references[]`，prompt 自动含 `@音频1`。
- 带参考锁的干声模板：`prompts/seed-audio-dry-ref-zh.txt`、`prompts/seed-audio-dry-ref-en.txt`。

### Changed

- `docs/API_SEED_AUDIO.md`：澄清 `speaker`/`audio_data`/`audio_url` 在 `references[]` 内互斥，并补充参考音频 JSON 示例。
- `skills/code-video-narration-tts/SKILL.md`、README：长片默认走音色锁流程。
- 重建 `dist/code-video-narration-tts-claude.zip`。

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
