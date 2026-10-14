# 在 Claude 中安装

## 推荐：命令行一键安装（Claude Code）

解压 zip 后：

```bash
python3 install-claude-skill.py
```

默认 → `~/.claude/skills/code-video-narration-tts/`。

```bash
python3 install-claude-skill.py --scope project
python3 install-claude-skill.py --from code-video-narration-tts-claude.zip
python3 install-claude-skill.py --force
python3 install-claude-skill.py --uninstall
```

配置 **至少一个** 密钥：`DASHSCOPE_API_KEY` / `GEMINI_API_KEY` / `BYTEPLUS_SEED_API_KEY`。  
Claude Code 新开会话或 `/reload-skills`。

### 合成示例

```bash
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" --provider qwen --voice Cherry --file script.txt --concat
python "${CLAUDE_SKILL_DIR}/scripts/synthesize.py" --provider gemini --voice Kore --file script.txt --concat
```

## Claude Code vs Claude app / Cowork

| 环境 | 本机 `~/.claude/skills/` | 用法 |
|------|--------------------------|------|
| **Claude Code** | ✅ | CLI 安装 |
| **Claude app / Cowork** | ❌ | claude.ai 上传，或项目 `.claude/skills/` |

## 不要打进包的内容

真实 API Key、`.env`、生成的音频、`voice-refs/`。
