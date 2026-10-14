# audio-effects

为代码讲解视频（尤其 Claude Opus 片子）生成**教学旁白**的工具与提示词库。

默认声音路线：字节 **Seed**（干声优先；Seed Audio 1.0 强制无 BGM/SFX），并支持 **Qwen TTS**、**Gemini Flash TTS**。语言跟脚本文本走（中/英）。

## 仓库结构

```
docs/
  TTS_PROMPTING_BEST_PRACTICES.md   # 三家模型提示词调研与对照表
  MAINTENANCE.md                    # 维护说明
prompts/                            # 可直接粘贴的旁白 style / 场景模板
skills/
  code-video-narration-tts/SKILL.md # Cursor / Grok Bot 可复用技能
CHANGELOG.md
```

## 快速开始

1. 准备旁白脚本（按场景分段）。
2. 配置密钥（勿提交到仓库）：
   - Seed / 豆包：`BYTEPLUS_SEED_API_KEY`
   - Qwen：`DASHSCOPE_API_KEY`
   - Gemini：`GEMINI_API_KEY`
3. 打开 `skills/code-video-narration-tts/SKILL.md`，按其中流程合成。
4. 风格串优先用 `prompts/` 下对应文件；完整原理见 `docs/TTS_PROMPTING_BEST_PRACTICES.md`。

## 共用旁白风格（默认）

- **中文**：清晰沉稳的教学旁白，中等偏慢语速，吐字清楚，语气耐心专业，适合代码教程。
- **英文**：Calm clear educational narration, medium-slow pace, precise diction, warm professional coding instructor.

## 原则

1. **风格与正文分离**——指令字段放风格，念稿字段只放要说的话。
2. **代码视频用干声**——不要默认加音乐/音效。
3. **语言跟脚本**——不要整篇强行指定错误语言。
4. **密钥不出库**。

## 许可证

私有仓库；未另行声明前仅供仓库所有者使用。
