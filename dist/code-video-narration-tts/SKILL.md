---
name: code-video-narration-tts
description: >
  Use after a Claude Opus (or similar) code-explanation video is drafted, to
  synthesize dry educational narration audio via Volcengine openspeech Seed
  Audio 1.0 (optional Qwen/Gemini). Triggers: 旁白, TTS, SeedAudio, narration,
  配音, voiceover, 音色一致 for coding tutorials.
---

# Code video narration TTS

Generate **dry** tutorial voiceover (no BGM/SFX) for coding videos. Default provider: **Seed Audio 1.0** on openspeech.

## When to use

- Opus / coding video scenes are ready and you have a narration script.
- User asks for 旁白 / TTS / SeedAudio / voiceover / consistent voice across segments.

## Official API (must follow)

- `POST https://openspeech.bytedance.com/api/v3/tts/create`
- Headers: `X-Api-Key` (required), `X-Api-Request-Id` (UUID recommended)
- Body:
  - `model`: `seed-audio-1.0` (required)
  - `text_prompt`: ≤ **3000** chars (required)
  - `references[]`: each item exactly one of `speaker` | `audio_data` | `audio_url` (or image fields; do not mix image with audio)
  - In prompts, cite refs as `@音频1` … `@音频3` (order matches `references`)
  - Ref clip limits: ≤30s, ≤10MB each; max 3
  - `audio_config`: `format` (prefer `mp3`), `sample_rate`, `speech_rate` (-50..100), `loudness_rate`, `pitch_rate`, `enable_subtitle`
- Response: `audio` (base64) and/or `url` (~2h TTL); bill on `original_duration` (max **120s**); debug with `X-Tt-Logid`

Env: `BYTEPLUS_SEED_API_KEY` or `VOLC_TTS_API_KEY`. Optional `SEED_TTS_URL`.

## Voice consistency (long videos)

Pure text without `references` **re-samples timbre every request** → multi-segment drift.

**Recommended lock workflow:**

```bash
python scripts/synthesize.py --text "Short lock line for this project." \
  --save-as-voice-lock ./voice-refs/project-voice.mp3 --speech-rate -15
python scripts/synthesize.py --file script.txt \
  --ref-audio ./voice-refs/project-voice.mp3 --speech-rate -15 --concat
```

Alternative: same `--speaker=<Doubao 2.0 or clone ID>` on every chunk (no ref audio).

Keep identical `speech_rate` / `pitch_rate` / `loudness_rate` across chunks. Details: `references/VOICE_CONSISTENCY.md`.

## Default narration strategy

1. Keep **style outside** quoted lines; spoken text only inside `Read exactly: "..."`.
2. Force dry VO: no music, SFX, or ambience.
3. Teaching pace: try `speech_rate=-15` (same value for all segments).
4. For A/V sync: `enable_subtitle=true` and keep word timestamps.
5. Preprocess script: strip stage directions/markdown; rewrite code for speech (`npm install` → `N-P-M install`).

### Dry prompt templates

See `prompts/seed-audio-dry-zh.txt` / `seed-audio-dry-en.txt`. With a reference lock use `seed-audio-dry-ref-*.txt` (or let the CLI inject `@音频1`).

## Run (preferred)

```bash
pip install requests
export BYTEPLUS_SEED_API_KEY='...'
python scripts/synthesize.py --text "接下来我们打开终端，输入 npm install。" --speech-rate -15
python scripts/synthesize.py --file script.txt --ref-audio ./voice-refs/project-voice.mp3 --concat
```

Outputs: `NN.mp3`, `NN.mp3.json`, `manifest.json`, optional `narration-full.mp3`.

## Done checklist

- [ ] openspeech + `seed-audio-1.0`
- [ ] dry template; style not spoken
- [ ] under 3000 chars / 120s per request; long script split
- [ ] multi-segment: same `--ref-audio` or same `--speaker`
- [ ] deliver audio + manifest; no secrets committed
