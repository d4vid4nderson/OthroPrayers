# Voice tool — reusable ElevenLabs voice

A small script to build a **reusable AI voice** with [ElevenLabs](https://elevenlabs.io)
and synthesize speech with it. The cloned voice's `voice_id` is your reusable
"model" — usable from this script (or anywhere in your ElevenLabs account).

This is a **local developer tool**; it is not part of the deployed site.

## Setup (macOS)

```bash
python3 -m pip install requests
export ELEVENLABS_API_KEY="sk_...your key..."   # from elevenlabs.io → Profile → API Keys
```

## Use

```bash
# 1) Create a reusable voice from clean sample audio (Instant Voice Cloning).
#    Use ~1–3 minutes of clear, single-speaker audio (mp3/wav/m4a).
#    Need something to read? See recording-script.md.
python3 elevenlabs_voice.py clone --name "Reader" --files sample1.mp3 sample2.wav --denoise

# 2) Inspect your account
python3 elevenlabs_voice.py voices
python3 elevenlabs_voice.py models

# 3) Synthesize text with the voice (uses the saved voice id from step 1)
python3 elevenlabs_voice.py say --text "Glory to Thee, O Lord." --out test.mp3
python3 elevenlabs_voice.py say --text-file passage.txt --out passage.mp3 --model eleven_multilingual_v2
```

`clone` saves the id to `voice.json` next to the script, and `say` reuses it
(override with `--voice-id`). Tune `--stability`, `--similarity`, `--style` on `say`.

## Two kinds of clone

| | Instant (IVC) | Professional (PVC) |
|---|---|---|
| Data needed | ~1–3 min sample | ~30 min – 3 hrs clean audio |
| How | `clone` command here | dashboard (Creator plan, identity verification) |
| "Training" | no — reference clip | yes — a dedicated fine-tuned model |
| Quality | good | highest |

PVC is the actual *trained* model but its API requires a verification CAPTCHA,
so start it in the dashboard (`elevenlabs_voice.py pvc-guide` prints the steps).
Once trained, use its `voice_id` here with `say --voice-id ...`.

## When you're ready to wire audio into the app

Generate one clip per prayer and have the web player use those MP3s instead of
the device voice. The player is already structured for this — say the word and
I'll add the build step (and a small manifest the player reads).

## Notes / rights

- Only clone voices you own or have **explicit permission** to use.
- Generating audio of the prayer **translation** (© St. Tikhon's Monastery
  Press) is a separate rights consideration — worth confirming before publishing
  generated prayer audio.
