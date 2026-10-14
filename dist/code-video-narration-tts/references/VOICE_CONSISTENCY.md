# 旁白音色一致性（长视频）

> Seed / Qwen / Gemini 锁声方式不同，见下文分节。

> 适用：`seed-audio-1.0` + openspeech `POST /api/v3/tts/create`  
> 问题：长旁白必须切段（`text_prompt` ≤3000 字、单次 `original_duration` ≤120s），但各段若只靠纯文本风格描述，**每次请求会重新采样音色**，听感会跳变。

## 为什么会漂？

| 做法 | 结果 |
|------|------|
| 每段只传 `text_prompt`（干声模板 + 台词），无 `references` | 模型按文字描述**自由生成**音色；段与段之间无硬约束 → 容易换声 |
| 段间改风格形容词 / 语速 / 音调 | 即使有参考，表现力也会漂 |
| 同时传 `speaker` 与参考音频 | 官方互斥，请求失败或行为未定义 |

官方产品能力里提到：通过**参考音频做音色复刻 / 延展**，可在长音频与多次延长场景保持角色音色一致。openspeech 的落地方式就是 `references` + prompt 里的 `@音频N`。

## 官方字段（锁定音色）

`speaker` / `audio_data` / `audio_url` 写在 **`references[]` 每一项里**，三项**互斥**（每项只传一个）。

```json
{
  "model": "seed-audio-1.0",
  "text_prompt": "Use the exact same voice timbre as @音频1. ... Read exactly: \"台词\"",
  "references": [
    { "audio_data": "<Base64>" }
  ],
  "audio_config": {
    "format": "mp3",
    "sample_rate": 44100,
    "speech_rate": -15,
    "loudness_rate": 0,
    "pitch_rate": 0
  }
}
```

等价写法：

```json
"references": [{ "audio_url": "https://example.com/voice-lock.mp3" }]
```

或固定豆包 2.0 / 复刻音色 ID：

```json
"references": [{ "speaker": "zh_female_vv_uranus_bigtts" }]
```

### `@音频N` 规则

- 编号从 **1** 起，与 `references` **数组顺序**一一对应：`@音频1`、`@音频2`、`@音频3`
- 最多 **3** 条参考音频；单条 **≤30 秒**、**≤10 MB**；格式 wav / mp3 / pcm / ogg_opus
- 有音频参考时，`text_prompt` 里应引用对应 `@音频N`（本仓库 CLI 会自动补 `@音频1`）
- **不可**与图片参考混用

## 推荐工作流 A：首段锁声（适合 Seed Audio 自由音色）

适合：不想挑 speaker ID、想保留「教学旁白」那种自由生成的音色，又要跨很多段一致。

```bash
# ① 一次性「音色锁」短句（建议 8–20 秒，干声、吐字清楚）
python scripts/synthesize.py \
  --text "大家好，这是本片统一的教学旁白音色锁定样本。" \
  --speech-rate -15 \
  --save-as-voice-lock ./voice-refs/project-voice.mp3

# ② 以后每一段都必须带同一锁文件（语速/音量/音调保持一致）
python scripts/synthesize.py \
  --file script.txt \
  --ref-audio ./voice-refs/project-voice.mp3 \
  --speech-rate -15 \
  --out-dir ./narration-audio \
  --concat
```

要点：

1. 锁文件尽量**短而干净**（无人声以外噪音）；超 30s 不能当参考。
2. 所有段用**同一** `--ref-audio`、同一套 `speech_rate` / `pitch_rate` / `loudness_rate`、同一干声模板。
3. `--concat` 用 ffmpeg 拼成 `narration-audio/narration-full.mp3`。
4. 也可先听满意第 1 段旁白，再 `--save-as-voice-lock` 把它存成锁（注意时长 ≤30s）。

### 请求体示意（CLI 已封装）

```json
{
  "model": "seed-audio-1.0",
  "text_prompt": "Clean dry studio narration only. ...\nUse the exact same voice timbre, pitch, and delivery as @音频1. ...\nRead exactly: \"接下来我们打开终端，输入 N-P-M install。\"",
  "references": [{ "audio_data": "<project-voice.mp3 的 Base64>" }],
  "audio_config": { "format": "mp3", "sample_rate": 44100, "speech_rate": -15 }
}
```

## 备选工作流 B：固定 `speaker` ID

适合：接受豆包 2.0 预置音色（或已在控制台复刻好的音色 ID），不需要「自由生成再锁」。

```bash
python scripts/synthesize.py --file script.txt \
  --speaker zh_female_vv_uranus_bigtts \
  --speech-rate -15 --concat
```

- 每段 `references: [{ "speaker": "<ID>" }]`，prompt 仍带 `@音频1`（CLI 自动处理）。
- **不要**再叠加 `--ref-audio`。
- 音色 ID 以火山控制台为准；社区常见如 `zh_female_vv_uranus_bigtts`（Vivi）、`zh_male_m191_uranus_bigtts`（云舟）等。

何时选 A / B：

| | A 参考音频锁 | B 固定 speaker |
|--|-------------|---------------|
| 音色来源 | 你自己首段生成 / 真人参考 | 控制台预置或复刻 ID |
| 一致性 | 强（跨段复刻同一锁） | 强（同一 ID） |
| 灵活性 | 可保留「自由采样」出的满意声 | 只能用目录里的声 |
| 额外资产 | 需要保管 `voice-refs/*.mp3` | 只需记 ID |

## 手工 ffmpeg 拼接（不用 `--concat` 时）

```bash
# filelist.txt
# file '01.mp3'
# file '02.mp3'
ffmpeg -f concat -safe 0 -i filelist.txt -c copy narration-full.mp3
```

## 反模式

- 段与段之间改「沉稳 / 活泼 / 年轻」等风格词
- 有的段用 `--speaker`、有的段用 `--ref-audio`、有的段纯文本
- 没有锁文件就重跑长视频全部段
- 各段 `speech_rate` / `pitch_rate` 不一致
- 把 >30s 的整段旁白当 `--ref-audio`

## 与时长上限的关系

- **单次请求**：`text_prompt` ≤3000 字符；计费/上限看 `original_duration` ≤**120s**
- **参考锁**：每条 ≤**30s** / ≤**10MB**
- 长片 = 切段合成（每段都带同一锁）+ concat；不是一次生成整片

更多字段见 [`API_SEED_AUDIO.md`](./API_SEED_AUDIO.md)。


---

## Qwen（DashScope）：固定 `--voice`

Qwen **不支持** Seed 式参考音频锁。一致性 = **全片同一 `voice` + 同一 `language_type`**。

```bash
export DASHSCOPE_API_KEY='...'
python scripts/synthesize.py --provider qwen --voice Cherry --file script.txt --concat
```

- 单次 ≤ **600** 字符；CLI 自动按句切分后拼接
- 中途换 `Cherry`→`Serena` 会明显换声
- 详见 [`API_QWEN_TTS.md`](./API_QWEN_TTS.md)

## Gemini Flash TTS：固定 `--voice` + 短 `style`

Gemini 3.8 一致性靠：

1. 全程同一 `speech_config.voice`（默认 **`Kore`**）
2. 全程同一短 `speech_metadata.style`（默认 `prompts/gemini-style-*.txt`）
3. **不要**每段贴长人设 / Director's Notes

```bash
export GEMINI_API_KEY='...'
python scripts/synthesize.py --provider gemini --voice Kore --file script.txt --concat
```

- CLI 约按 **1800** 字符切段（低于 8192 token 上限）
- Seed 的 `--ref-audio` / `--save-as-voice-lock` 在 Gemini 上会直接报错
- 详见 [`API_GEMINI_TTS.md`](./API_GEMINI_TTS.md)

## 三方对照

| Provider | 锁声方式 | 切段上限（CLI） |
|----------|----------|-----------------|
| Seed Audio | `--ref-audio` 锁文件（路线 A）或固定 `--speaker` | prompt ≤3000 / ≤120s |
| Qwen | 固定 `--voice`（如 Cherry） | ≤600 字/请求 |
| Gemini | 固定 `--voice` + 同一短 style | ~1800 字/请求 |
