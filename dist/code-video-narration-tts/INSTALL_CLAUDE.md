# 在 Claude 中安装

## Claude Code / Claude app Skills

1. 解压本包，得到文件夹 `code-video-narration-tts/`。
2. 复制到 Claude skills 目录（任选其一，以你本机 Claude 版本为准）：
   - 项目级：`你的项目/.claude/skills/code-video-narration-tts/`
   - 用户级：`~/.claude/skills/code-video-narration-tts/`
3. 确认目录内有 `SKILL.md`、`scripts/synthesize.py`、`prompts/`、`references/VOICE_CONSISTENCY.md`。
4. 配置环境变量 `BYTEPLUS_SEED_API_KEY`（火山新版控制台 API Key）。
5. **长片旁白**：先按 `references/VOICE_CONSISTENCY.md` 生成 `voice-refs/project-voice.mp3`，再对每段加 `--ref-audio`。
6. 在对话里说「用旁白 TTS skill 合成这段…」或 `@code-video-narration-tts`。

## 仅作 Project 知识库

把整个文件夹上传到 Claude Project 知识库；生成旁白时让 Claude 先读 `SKILL.md` 与 `references/VOICE_CONSISTENCY.md`，再调 `scripts/synthesize.py`。

## 不要打包进包的内容

- 真实 API Key、`.env`、生成的 `*.mp3`、`voice-refs/`
