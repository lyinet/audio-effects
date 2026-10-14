# 维护文档

## 谁改什么

| 路径 | 改动触发 |
|------|----------|
| `docs/TTS_PROMPTING_BEST_PRACTICES.md` | 官方 API / 提示词规范变更、实测得到更好 style |
| `docs/VOICE_CONSISTENCY.md` | 参考音色 / 锁声流程 / `@音频N` 规则变更 |
| `docs/API_SEED_AUDIO.md` | openspeech 字段或互斥规则变更 |
| `docs/API_QWEN_TTS.md` | DashScope Qwen TTS 端点 / 600 字限制 / voice |
| `docs/API_GEMINI_TTS.md` | Gemini Interactions TTS 模型 / style / voice |
| `prompts/*` | 默认旁白风格或 Seed 干声模板调整 |
| `skills/code-video-narration-tts/SKILL.md` | 合成流程、切块上限、默认 provider / 音色变更 |
| `scripts/synthesize.py` / `scripts/providers/` | 合成 CLI、provider 实现 |
| `scripts/install-claude-skill.py` / `pack-claude-skill.py` | Claude 安装路径、zip 布局、插件清单变更 |
| `CHANGELOG.md` | **每次**有用户可见改动时追加条目 |
| `README.md` | 结构、快速开始、默认策略变化时同步 |

## 发布检查清单

1. 提示词改动是否仍满足「风格 ≠ 正文」。
2. Seed Audio 路径是否仍强制干声（No music / No SFX）。
3. 文档中的模型 ID、音色 ID 是否标注「以控制台为准」。
4. 更新 `CHANGELOG.md`（Added / Changed / Fixed）。
5. 推送到 `main`：`git push origin main`（本仓库约定：每次更改都推送）。
6. 若改了 skill 内容：运行 `python scripts/pack-claude-skill.py（含 providers/ 与 API_QWEN/GEMINI）`，再推送。

## 与 Grok Bot 技能同步

本仓库的 `skills/code-video-narration-tts/SKILL.md` 是源文件。若助手侧还有一份同名 skill（如 id `tts`），改完仓库后应同步更新助手 skill，避免两处漂移。

## 密钥与安全

- 仅用环境变量；禁止把 key 写入示例、commit、issue。
- 示例脚本用 `os.environ[...]`，失败时提示缺哪个变量。

## 验证建议

- 中文短旁白、英文短旁白各合成一段，听吐字与语速。
- 同一脚本分别走 Seed / Qwen / Gemini，对比 style 是否生效且未被念出。
- 多段后 ffmpeg concat，用 ffprobe 核对总时长。
- 长片：用同一 `--ref-audio` 或 `--speaker` 跑两段，听是否同声；锁文件须 ≤30s。

## 实测端点（2026-10-14）

- 国内 openspeech：`POST https://openspeech.bytedance.com/api/v3/tts/create` + `X-Api-Key` → 对当前 Seed Audio 干声旁白可用。
- BytePlus `voice.ap-southeast-1.bytepluses.com`：同密钥返回 `Invalid X-Api-Key`，勿当作默认。
- 默认环境变量：`SEED_TTS_URL=https://openspeech.bytedance.com/api/v3/tts/create`。
