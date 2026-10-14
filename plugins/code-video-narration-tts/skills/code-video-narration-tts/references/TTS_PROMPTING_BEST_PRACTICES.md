# TTS Prompting Best Practices — Code Tutorial Narration (旁白)

> Research compiled 2026-10-14 (CST). For skill + README paste-in.
> Focus: calm, clear educational narration for code videos (zh-CN + en).

---

## Important product split (ByteDance)

| Product | What it is | Best for code-video旁白? |
|---------|------------|--------------------------|
| **Seed Audio 1.0** | Full-scene audio creation (speech + optional BGM/SFX/ambience) from one text prompt | Only if you force **dry voice** (no music/SFX) |
| **Doubao / Volcengine Seed-TTS 2.0** | Classic TTS: `speaker` + `text` + optional `context_texts` | **Preferred** for clean tutorial VO |

Sources: [ByteDance Seed Audio](https://seed.bytedance.com/en/seedaudio1_0), [Volcengine Doubao Voice](https://www.volcengine.com/docs/6561/1354862), [Scenario Seed Audio essentials](https://help.scenario.com/articles/7490394523-seed-audio-1-0-the-essentials).

---

## 1. ByteDance Seed Audio 1.0 / Seed-TTS / Volcengine Doubao

### 1A. Seed Audio 1.0 (scene model)

**Official params (common hosting names):** `prompt` / `text_prompt` (provider-dependent). Dialogue goes in **quotes**; everything else is direction.

**Prompt template — dry educational旁白 (recommended for code videos):**

```text
Clean dry studio narration only. No music, no sound effects, no ambience bed, no applause, no crowd.
Language: Chinese.
Narrator: adult, clear Mandarin, warm but professional instructor, medium-low pitch, calm and measured pace, precise diction, slight smile in the voice but never playful or dramatic.
Read exactly: "接下来我们打开终端，输入 npm install。注意依赖安装完成后，再启动开发服务器。"
```

English:

```text
Clean dry studio narration only. No music, no sound effects, no ambience.
Language: English.
Narrator: adult, clear American English, warm professional coding instructor, medium pace, crisp consonants, calm and confident. Like a senior engineer explaining a PR, not a movie trailer.
Read exactly: "Next, open the terminal and run npm install. Wait until dependencies finish, then start the dev server."
```

**Single-voice template (Scenario / BytePlus pattern):**

```text
In the warm, clear, medium-paced voice of a [30–40]-year-old [gender] coding instructor with [Mandarin / American English], calm educational tone, read the following: '[SCRIPT]'
```

**Long-form voice consistency:** Pure text_prompt without `references` samples a new timbre each request. For multi-segment lessons, lock with `references[{audio_data|audio_url|speaker}]` + `@音频1` (see `docs/VOICE_CONSISTENCY.md`). Official product copy: reference-audio extension keeps character voice stable across ~2 min generations / continuations.

**Anti-patterns (Seed Audio):**
- Do **not** put style directions inside the quoted script (model may speak them).
- Do **not** request music/SFX for tutorial VO — they compete with screen audio.
- Do **not** overload: one voice + dry room > cinematic five-part battle scene.
- Avoid vague casting: prefer “late thirties, clear, calm instructor” over “nice young voice”.
- Prompt length limits often ~2,048–3,000 chars; stitch long lessons.

**Timing (Multilingual sibling):** `Total duration: exactly N seconds` + `[0:00-0:05] "line"` windows — useful when syncing to video beats. *(Confirm Multilingual vs base model on your host.)*

Sources: [Scenario essentials](https://help.scenario.com/articles/7490394523-seed-audio-1-0-the-essentials), [fal prompt guide](https://fal.ai/learn/tools/how-to-use-seed-audio), [seedaudio.co prompt guide](https://seedaudio.co/seed-audio-1-0-prompt-guide), [Seed blog](https://seed.bytedance.com/en/blog/from-speech-to-audio-creation-introducing-the-seed-audio-1-0-audio-creation-model).

### 1B. Volcengine Doubao Seed-TTS 2.0 (classic TTS)

**Key params:**

| Param | Role |
|-------|------|
| `speaker` | Voice ID from console (e.g. `zh_female_vv_uranus_bigtts`) |
| `text` | **Only** words to speak |
| `additions.context_texts` | Natural-language style/emotion instruction (array; **only first element used**) |
| `explicit_language` | e.g. `zh-cn`, `en` |
| `X-Api-Resource-Id` | `seed-tts-2.0` for 2.0 voices |
| `model` | For clones: `seed-tts-2.0-expressive` to enable style; `standard` = lower latency, no `context_texts` |

**`context_texts` examples (旁白):**

```json
{"context_texts": ["请用清晰、沉稳、中等语速的教学旁白语气说话，像耐心的编程老师，不要夸张情绪。"]}
```

```json
{"context_texts": ["Speak in a calm, clear, medium-paced tutorial instructor voice. Educational, precise, not dramatic."]}
```

Other official exploration examples: `你可以说慢一点吗？` / `你可以用特别特别痛心的语气说话吗?` / volume/timbre asks — adapt to teaching, not drama.

**Voice ID recommendations (2.0 `*_uranus_bigtts`) — community + catalog names; verify in console:**

| Use | Speaker ID | Notes |
|-----|------------|-------|
| zh default旁白 | `zh_female_vv_uranus_bigtts` (Vivi) | Common default, multi-lang |
| zh clear instructor ♀ | `zh_female_cancan_uranus_bigtts` (知性灿灿) | Knowledgeable female |
| zh crisp / lively | `zh_female_shuangkuaisisi_uranus_bigtts` (爽快思思) | Often default in SDKs |
| zh teaching-oriented | `zh_female_yingyujiaoxue_uranus_bigtts` (Tina老师) | English-teaching persona — good for tutorials *(confirm ID in console)* |
| zh male calm | `zh_male_m191_uranus_bigtts` (云舟) | General male |
| en ♀ | `en_female_dacey_uranus_bigtts` | English |
| en ♂ | `en_male_tim_uranus_bigtts` | English |

**Emotion enum (some wrappers):** `narrator`, `storytelling`, plus happy/sad/… — prefer `narrator` or `context_texts` for tutorials.

**Anti-patterns:**
- Never put `context_texts` content into `text`.
- Don’t mix 1.0 and 2.0 speakers with wrong `X-Api-Resource-Id`.
- Per-sentence emotion → **separate API calls**, then ffmpeg concat (style applies to whole call).
- Only first `context_texts[]` entry is effective.

Sources: [Volcengine unidirectional TTS](https://docs.volcengine.com/docs/6561/1598757), [Task submission](https://docs.volcengine.com/docs/DoubaoVoice/Tasksubmission), [Voice list hub](https://www.volcengine.com/docs/6561/1354862), [SoundDesign text_prompt](https://docs.volcengine.com/docs/DoubaoVoice/SoundDesignAPI) (`prompt.text_prompt` for voice design, ≤200字), [ax0x Doubao runbook](https://blog.ax0x.ai/doubao-tts-runbook), [OpenMinis doubao-tts skill](https://github.com/OpenMinis/MinisSkills/blob/main/doubao-tts/SKILL.md).

**Sound Design `text_prompt` example (voice creation, not runtime TTS):** `女性，语速中等偏快，语调低沉有力` → for旁白 prefer: `女性，语速中等偏慢，吐字清晰，语气沉稳耐心，适合教学讲解`.

---

## 2. Alibaba Qwen3-TTS / CosyVoice / Qwen-Audio-TTS

### Model matrix (style control)

| Model | Style mechanism | Notes |
|-------|-----------------|-------|
| `qwen3-tts-flash` | `voice` + `language_type` | No free-form instructions on basic flash *(per QwenCloud api-guide skill notes)* |
| `qwen3-tts-instruct-flash` | `instructions` + `optimize_instructions` | Natural-language style; CN/EN instructions; max ~1600 tokens |
| `cosyvoice-v3.5-plus` / `v3.5-flash` | `instructions` / `instruction` | Strong instruction control; v3.5 system voices limited — often clone/design only |
| `qwen-audio-3.0-tts-plus` / `flash` | Inline tags in `text` | `[excited]`, `[serious]`, `[laughing]`, etc. |

Docs: [Non-realtime TTS](https://docs.qwencloud.com/developer-guides/speech/tts), [API ref](https://docs.qwencloud.com/api-reference/speech-synthesis/qwen-tts), [Realtime / tags](https://www.alibabacloud.com/help/en/model-studio/realtime-tts-user-guide), [Voice list](https://docs.qwencloud.com/developer-guides/speech/voice-list/qwen-tts).

### Official params

- `model`, `text`, `voice`
- `language_type`: `Auto` | `Chinese` | `English` | … — **set explicitly when monolingual** (quality >> Auto)
- `instructions` / `instruction` (model-dependent)
- `optimize_instructions`: `true` to rewrite instructions for better synthesis

### Instruction writing rules (official CosyVoice / QwenCloud)

1. Specific, not vague (“deep/crisp/medium-slow” not “nice”)
2. Multi-dimensional: pitch + speed + emotion + use-case
3. Objective physical descriptors
4. No celebrity imitation
5. Concise

**Dimension table:** Pitch | Speed | Emotion | Characteristics | Usage (news / documentary / audiobook / ad / assistant)

### Ready-to-use旁白 `instructions`

Chinese:

```text
清晰沉稳的教学旁白，中等偏慢语速，吐字清楚，语气耐心专业，像编程老师讲解代码，不要夸张或播音腔过重。适合教程与纪录片式解说。
```

English:

```text
Clear, calm educational narration; medium-slow pace; precise diction; warm professional coding instructor; documentary-style explainer; no hype, no ad energy.
```

With optimize:

```python
model="qwen3-tts-instruct-flash"  # or cosyvoice-v3.5-plus per region
text="接下来我们打开终端，输入 npm install。"
voice="Cherry"  # or Serena / Elias / Neil — see below
language_type="Chinese"
instructions="清晰沉稳的教学旁白，中等偏慢语速，吐字清楚，语气耐心专业。"
optimize_instructions=True
```

### Inline tags (`qwen-audio-3.0-tts-*` only)

For tutorials prefer:

```text
[serious]请注意这一步的顺序。[excited]好，依赖安装成功，我们继续。
```

Avoid overusing `[laughing]` / `[shouting]` in code VO.

Control tags include: `[sad]` `[excited]` `[serious]` `[curious]` `[very slowly]` `[very fast]` `[whispers]` …  
Rich (point-in-time): `[laughing]` `[sighing]` `[clears throat]` …

### Voice recommendations (Qwen3-TTS system voices)

| Locale / vibe | `voice` | Why |
|---------------|---------|-----|
| zh/en friendly default ♀ | `Cherry` | Sunny, natural young woman — common default |
| zh/en gentle ♀ | `Serena` | Softer instructional |
| zh/en intellectual ♀ | `Maia` / `Elias` | Elias described as academic + storytelling learning modules |
| zh/en news-clear ♂ | `Neil` | Professional news-anchor clarity |
| zh energetic ♂ | `Ethan` | Warm Mandarin; may be too lively for calm VO |
| en cinematic ♀ | `Jennifer` | Premium AmE |
| Calm elder ♂ | `Eldric Sage` | Wise/calm — optional for slow deep dives |

*(CosyVoice system IDs differ, e.g. `longanyang`, `longanhuan_v3` — see CosyVoice voice list.)*

### Anti-patterns (Qwen family)
- Leaving `language_type=Auto` on single-language scripts
- Putting style prose into `text` when you have `instructions`
- Using `[excited]` tags on CosyVoice / plain Qwen3-TTS-Flash (wrong model)
- Celebrity clone requests in instructions
- Instruction >100 chars on some CosyVoice realtime paths (check product limits)

---

## 3. Google Gemini Flash TTS

### Models (as of 2026-10 docs)

| Model ID | Notes |
|----------|-------|
| `gemini-3.8-flash-tts` | Current high-fidelity; **style in `speech_metadata.style`** |
| `gemini-3.8-flash-lite-tts` | Faster/cheaper workhorse |
| `gemini-2.5-flash-preview-tts` / Cloud `gemini-2.5-flash-tts` | Older path: style often in **prompt** field or inline text |
| `gemini-3.1-flash-tts-preview` | Preview bridge |

Primary docs: [Gemini API speech generation](https://ai.google.dev/gemini-api/docs/speech-generation), [Cloud Gemini-TTS](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts), [2.5 Flash Preview TTS](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-preview-tts).

### Gemini 3.8 — split style from transcript (critical)

| Place | Content |
|-------|---------|
| `text` | **Verbatim** words only (+ optional `<short pause>` / `<laugh>` tags) |
| `speech_metadata.style` | Sustained delivery: emotion, pace, prosody |
| `speech_config` voice | `Kore`, `Charon`, … |

**Do not** put “speak slowly like a teacher” in `text` on 3.8 — it may be read aloud.

### Style prompts for code-tutorial旁白

```text
calm, clear, medium-paced educational narrator; warm professional coding instructor; precise diction; documentary explainer tone
```

```text
清晰沉稳的教学旁白，中等语速，吐字清楚，耐心专业，像资深工程师讲解代码
```

Cloud Media Studio example pattern: `Narrate in a calm, professional tone for a documentary.`

Cloud older `prompt`+`text` pattern (2.5 / Cloud TTS):

```json
{
  "input": {
    "prompt": "Narrate in a calm, authoritative tone of a technical documentary narrator. Medium pace, clear pronunciation.",
    "text": "Next, open the terminal and run npm install."
  },
  "voice": { "name": "Charon", "model_name": "gemini-2.5-flash-tts", "languageCode": "en-US" }
}
```

### Inline tags (3.8 prefers angle brackets)

- Pacing: `<short pause>` `<medium pause>` `<long pause>`
- Vocal bursts: `<laugh>` `<sigh>` `<cough>` …
- Cloud 2.5 also documents `[short pause]`, `[extremely fast]`, `[whispering]` — **test per model**; adjectives like `[scared]` may be **spoken** (Mode 3 — avoid for旁白)

### Voice recommendations (prebuilt)

| Goal | Voice | Doc label |
|------|-------|-----------|
| Firm clear ♀ | `Kore` | Firm — strong default |
| Informative ♂ | `Charon` | Informative |
| Informative ♂ alt | `Rasalgethi` | Informative |
| Knowledgeable ♂ | `Sadaltager` | Knowledgeable |
| Clear ♂ | `Iapetus` | Clear |
| Clear ♀ | `Erinome` | Clear |
| Mature ♀ | `Gacrux` | Mature |
| Soft ♀ | `Achernar` | Soft |
| Warm ♀ | `Sulafat` | Warm |
| Avoid for calm VO | `Fenrir` (excitable), `Puck` (upbeat), `Sadachbia` (lively) | Too energetic |

Multi-speaker: up to 2; match `speech_metadata.speaker` names to `speech_config.speakers`.

### Anti-patterns (Gemini)
- Long “Audio Profile / Director’s Notes” blocks every turn → voice drift (use Voice Design once)
- Age/gender/accent changes inside `style` (immutable traits → pick another voice)
- Sound-effect tags (applause, thud)
- Asking “maintain identical timbre” in style
- Putting sustained emotion in transcript on 3.8

### Recommended workflow (official)
1. Pick/design voice once  
2. Write natural spoken transcript  
3. Synthesize with **empty style** first  
4. Add short style only if needed; reuse the exact same short string  

---

## Cross-provider templates for this skill

### Shared旁白 style string (map into each provider’s style field)

**ZH:** `清晰沉稳的教学旁白，中等偏慢语速，吐字清楚，语气耐心专业，适合代码教程。`

**EN:** `Calm clear educational narration, medium-slow pace, precise diction, warm professional coding instructor.`

### Mapping

| Provider | Style field | Spoken script field |
|----------|-------------|---------------------|
| Seed Audio 1.0 | Unquoted direction + “No music/SFX” | Quoted `"..."` |
| Doubao Seed-TTS 2.0 | `context_texts[0]` | `text` |
| Qwen instruct / CosyVoice 3.5 | `instructions` (+ `optimize_instructions`) | `text` |
| Qwen-Audio-TTS 3.0 | Optional `[serious]` tags | `text` |
| Gemini 3.8 | `speech_metadata.style` | `text` |
| Gemini 2.5 / Cloud | `prompt` | `text` |

### Spoken-text anti-patterns (all providers)

Do **not** put in the narration script:

- Stage directions: `(平静地说)` / `[speak slowly]` / `用温柔的语气`
- Markdown: `**bold**`, code fences, `# headings`
- Unspeakable tokens: raw URLs, giant hashes, `=====`
- File paths read character-by-character unless you rewrite (`slash`, `dot`)
- Emoji / decorative punctuation spam
- Language tags like `ZH:` / `EN:`
- Provider style strings duplicated into script

**Do** rewrite code for speech: `npm install` → “N-P-M install”; `src/index.ts` → “src slash index dot T-S”; `O(n)` → “O of n”.

---

## Community / template sources

- Seed Audio structured T2A briefs: [fal](https://fal.ai/learn/tools/how-to-use-seed-audio), [Scenario](https://help.scenario.com/articles/7490394523-seed-audio-1-0-the-essentials), [seedaudio.co](https://seedaudio.co/seed-audio-1-0-prompt-guide)
- Doubao `context_texts` + per-sentence emotion: [ax0x runbook](https://blog.ax0x.ai/doubao-tts-runbook)
- Qwen instruction dimensions + examples: [QwenCloud TTS guide](https://docs.qwencloud.com/developer-guides/speech/tts)
- Gemini three levers (prompt / text / markup): [Cloud Gemini-TTS prompting tips](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts)
- Gemini 3.8 style vs tags: [ai.google.dev speech-generation](https://ai.google.dev/gemini-api/docs/speech-generation)

---

## Uncertainty / verify before shipping

1. Exact Seed Audio API field name (`prompt` vs `text_prompt`) varies by host (BytePlus / fal / Scenario / Runware).
2. Whether user “SeedAudio” means **Seed Audio 1.0** or **Doubao Seed-TTS** — skill should support both; default dry TTS path to Seed-TTS if available.
3. Tina老师 / full Doubao voice table: confirm IDs live in [Volcengine 音色列表](https://www.volcengine.com/docs/6561/1354862).
4. `qwen3-tts-instruct-flash` availability vs region (Singapore vs Beijing Model Studio).
5. Gemini model ID in user’s key: `gemini-3.8-flash-tts` vs still on `gemini-2.5-flash-preview-tts` — prompting API differs.
6. Seed Audio “English+Chinese only” on some hosts vs Multilingual 20-language sibling — check endpoint.

---

## Minimal skill defaults (suggested)

```yaml
default_provider: seed_tts   # Doubao Seed-TTS 2.0 if key present; else seed_audio dry
style_zh: "清晰沉稳的教学旁白，中等偏慢语速，吐字清楚，语气耐心专业，适合代码教程。"
style_en: "Calm clear educational narration, medium-slow pace, precise diction, warm professional coding instructor."
voices:
  seed_tts:
    zh: zh_female_vv_uranus_bigtts
    en: en_female_dacey_uranus_bigtts
  qwen:
    zh: Cherry   # or Serena / Elias
    en: Cherry   # or Jennifer / Neil
  gemini:
    zh: Kore
    en: Charon   # or Kore / Rasalgethi
language_follow_script: true
strip_stage_directions_from_text: true
seed_audio_force_dry: true
```
