---
name: code-video-narration-tts
description: >
  Use after a Claude Opus (or similar) code-explanation video is drafted, to
  synthesize dry educational narration audio via Volcengine openspeech Seed
  Audio 1.0 (optional Qwen/Gemini). Triggers: 旁白, TTS, SeedAudio, narration,
  配音, voiceover for coding tutorials.
---

# Code video narration TTS

Generate **dry** tutorial voiceover (no BGM/SFX) for coding videos. Default provider: **Seed Audio 1.0** on openspeech.

## When to use

- Opus / coding video scenes are ready and you have a narration script.
- User asks for 旁白 / TTS / SeedAudio / voiceover.

## Official API (must follow)

- `POST https://openspeech.bytedance.com/api/v3/tts/create`
- Headers: `X-Api-Key` (required), `X-Api-Request-Id` (UUID recommended)
- Body:
  - `model`: `seed-audio-1.0` (required)
  - `text_prompt`: ≤ **3000** chars (required)
  - `speaker` | `audio_data` | `audio_url`: mutually exclusive
  - Do not mix image refs with audio refs
  - In prompts, reference clips as `@音频1` … `@音频3`
  - `audio_config`: `format` (prefer `mp3`), `sample_rate`, `speech_rate` (-50..100), `loudness_rate`, `pitch_rate`, `enable_subtitle`
- Response: `audio` (base64) and/or `url` (~2h TTL); bill on `original_duration` (max **120s**); debug with `X-Tt-Logid`
- Auth key from Volcengine **new** console API Key page (not legacy App-Id pair)

Env: `BYTEPLUS_SEED_API_KEY` or `VOLC_TTS_API_KEY`. Optional `SEED_TTS_URL` (default openspeech URL above).

## Default narration strategy

1. Keep **style outside** quoted lines; spoken text only inside `Read exactly: "..."`.
2. Force dry VO: no music, SFX, or ambience.
3. Teaching pace: try `speech_rate=-15`.
4. For A/V sync: `enable_subtitle=true` and keep word timestamps.
5. Fixed Doubao 2.0 timbre: pass `speaker=<voice_id>` only (no ref audio).
6. Preprocess script: strip stage directions/markdown; rewrite code for speech (`npm install` → `N-P-M install`).

### Dry prompt templates

Chinese — also in `prompts/seed-audio-dry-zh.txt`:

```text
Clean dry studio narration only. No music, no sound effects, no ambience bed.
Language: Chinese.
Narrator: adult, clear Mandarin, warm professional coding instructor, medium-low pitch, calm measured pace, precise diction.
Read exactly: "{SCRIPT}"
```

English — `prompts/seed-audio-dry-en.txt`:

```text
Clean dry studio narration only. No music, no sound effects, no ambience.
Language: English.
Narrator: adult, clear American English, warm professional coding instructor, medium pace, crisp consonants, calm and confident.
Read exactly: "{SCRIPT}"
```

Shared style strings (map into other providers' instruction fields): see `prompts/qwen-*.txt`, `prompts/gemini-*.txt`, `prompts/doubao-context-*.txt`.

## Run (preferred)

From this skill folder (or repo root that contains `scripts/`):

```bash
pip install requests
export BYTEPLUS_SEED_API_KEY='...'
python scripts/synthesize.py --text "接下来我们打开终端，输入 npm install。" --speech-rate -15
python scripts/synthesize.py --file script.txt --out-dir ./narration-audio --subtitle
```

Outputs: `NN.mp3`, `NN.mp3.json`, `manifest.json`.

If you cannot run shell, call the same JSON HTTP API yourself and save the audio.

## Opus video handoff

1. Accept segmented script with scene ids.
2. One request per segment if near 120s / 3000 chars.
3. Deliver audio + manifest (durations / subtitles); do not re-edit video unless asked.
4. Never commit API keys.

## Optional providers

Qwen / Gemini prompting notes: `references/TTS_PROMPTING_BEST_PRACTICES.md`. Keys: `DASHSCOPE_API_KEY`, `GEMINI_API_KEY`.

## Done when

- [ ] openspeech + `seed-audio-1.0`
- [ ] dry template; style not spoken aloud
- [ ] under 3000 chars / 120s per call (or split)
- [ ] audio + manifest delivered; secrets not written to files
