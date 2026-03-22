---
name: sag
description: ElevenLabs text-to-speech via the sag CLI. Use when asked to speak, narrate, do voice replies, storytelling, or generate audio.
metadata: {"clawdbot":{"emoji":"🗣️","requires":{"bins":["sag"]}}}
---

# sag - ElevenLabs TTS

Use `sag` for ElevenLabs text-to-speech. Generates audio files (this is a headless server — no local speakers).

## Setup

- Binary: `~/go/bin/sag` (Go install)
- API key file: `~/.config/sag/api-key`
- Env var: `ELEVENLABS_API_KEY_FILE` (set in `~/.bashrc`)

## Quick reference

| Task | Command |
|------|---------|
| Generate speech | `sag speak -o /tmp/output.mp3 "Hello there"` |
| List voices | `sag voices` |
| Specific voice | `sag speak -v "Roger" -o /tmp/out.mp3 "Hello"` |
| Prompting tips | `sag prompting` |

## Important: always use `-o <file>`

This is a headless server with no audio output. Always write to a file:

```bash
sag speak -o /tmp/voice-reply.mp3 "Your message here"
```

Then include in reply: `# MEDIA:/tmp/voice-reply.mp3`

## Models

| Model | Use case |
|-------|----------|
| `eleven_v3` (default) | Expressive, best quality |
| `eleven_multilingual_v2` | Stable, multilingual |
| `eleven_flash_v2_5` | Fast, cheap |

Select with `--model-id <model>`.

## v3 audio tags

Put at the start of a line for expressive delivery:

`[whispers]`, `[shouts]`, `[sings]`, `[laughs]`, `[starts laughing]`, `[sighs]`, `[exhales]`, `[sarcastic]`, `[curious]`, `[excited]`, `[crying]`, `[mischievously]`

Example: `sag speak -o /tmp/out.mp3 "[whispers] keep this quiet. [short pause] ok?"`

## Pronunciation + delivery

- First fix: respell (e.g. "key-note"), add hyphens, adjust casing
- Numbers/units/URLs: `--normalize auto` (or `off` if it harms names)
- Language bias: `--lang en|de|fr|...`
- v3: no SSML `<break>` — use `[pause]`, `[short pause]`, `[long pause]`
- v2/v2.5: SSML `<break time="1.5s" />` works

## Voice storytelling

For stories, movie summaries, "storytime" moments — use voice! Way more engaging than walls of text.

```bash
# Pick a voice that fits the character
sag speak -v "George" -o /tmp/story.mp3 "[excited] Once upon a time..."

# Include in reply
# MEDIA:/tmp/story.mp3
```

Voice character tips:
- Crazy/excited: `[excited]` tags, dramatic `[short pause]`s
- Calm/soothing: `[whispers]` or slower pacing
- Dramatic narrator: `[sings]` or `[shouts]` sparingly
- Spooky: `[whispers]` + long pauses

## Confirm voice + speaker before long output

Don't burn API credits on a 5-minute narration without checking the voice choice first.
