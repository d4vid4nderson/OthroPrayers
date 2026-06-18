#!/usr/bin/env python3
"""Create and use a reusable ElevenLabs voice.

This builds a reusable AI voice with ElevenLabs and lets you synthesize any
text with it. It uses Instant Voice Cloning (IVC), which is fully scriptable;
for Professional Voice Cloning (PVC) — the higher-fidelity, *trained* model —
see `pvc-guide` (it needs the Creator plan and an identity-verification step
that must be done in the dashboard).

Setup (macOS):
    python3 -m pip install requests
    export ELEVENLABS_API_KEY="sk_...your key..."

Examples:
    # 1) Clone a reusable voice from one or more clean samples (~1-3 min total)
    python3 elevenlabs_voice.py clone --name "Reader" --files sample1.mp3 sample2.wav

    # 2) See your account's voices / models
    python3 elevenlabs_voice.py voices
    python3 elevenlabs_voice.py models

    # 3) Synthesize text with the cloned voice (uses the saved voice id)
    python3 elevenlabs_voice.py say --text "Glory to Thee, O Lord." --out test.mp3
    python3 elevenlabs_voice.py say --text-file passage.txt --out passage.mp3

The created voice's id is saved to voice.json (next to this script) and reused
by `say`. The voice id is the reusable "model" — usable here or anywhere.

NOTE: only clone voices you own or have explicit permission to use. Generating
audio of copyrighted prayer translations is a separate rights consideration.
"""
import argparse, json, mimetypes, os, pathlib, sys

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: run  python3 -m pip install requests")

API = "https://api.elevenlabs.io"
HERE = pathlib.Path(__file__).resolve().parent
VOICE_FILE = HERE / "voice.json"


def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        sys.exit("Set your key first:  export ELEVENLABS_API_KEY=\"sk_...\"")
    return k


def hdr(extra=None):
    h = {"xi-api-key": api_key()}
    if extra:
        h.update(extra)
    return h


def die(resp, what):
    try:
        detail = json.dumps(resp.json(), indent=2)
    except Exception:
        detail = resp.text
    sys.exit(f"{what} failed [HTTP {resp.status_code}]:\n{detail}")


def save_voice(voice_id, name):
    VOICE_FILE.write_text(json.dumps({"voice_id": voice_id, "name": name}, indent=2) + "\n")
    print(f"Saved voice id to {VOICE_FILE}")


def saved_voice_id():
    if VOICE_FILE.exists():
        return json.loads(VOICE_FILE.read_text()).get("voice_id")
    return None


def cmd_clone(args):
    # read sample bytes up front so the request can be retried on a fallback path
    parts = []
    for p in args.files:
        if not os.path.exists(p):
            sys.exit(f"Sample not found: {p}")
        ctype = mimetypes.guess_type(p)[0] or "audio/mpeg"
        parts.append(("files", (os.path.basename(p), open(p, "rb").read(), ctype)))
    data = {"name": args.name, "remove_background_noise": str(args.denoise).lower()}
    if args.description:
        data["description"] = args.description

    resp = None
    for path in ("/v1/voices/ivc/create", "/v1/voices/add"):   # new path, then legacy
        resp = requests.post(API + path, headers=hdr(), data=data, files=parts, timeout=300)
        if resp.status_code not in (404, 405):
            break
    if resp.status_code >= 400:
        die(resp, "Voice clone")
    voice_id = resp.json().get("voice_id")
    print("Created voice:", args.name)
    print("voice_id:", voice_id)
    save_voice(voice_id, args.name)


def cmd_voices(args):
    resp = requests.get(API + "/v1/voices", headers=hdr(), timeout=60)
    if resp.status_code >= 400:
        die(resp, "List voices")
    for v in resp.json().get("voices", []):
        print(f"{v.get('voice_id')}  {v.get('category','?'):12}  {v.get('name')}")


def cmd_models(args):
    resp = requests.get(API + "/v1/models", headers=hdr(), timeout=60)
    if resp.status_code >= 400:
        die(resp, "List models")
    for m in resp.json():
        tts = m.get("can_do_text_to_speech")
        print(f"{m.get('model_id'):28}  tts={tts}  {m.get('name')}")


def cmd_say(args):
    voice_id = args.voice_id or saved_voice_id()
    if not voice_id:
        sys.exit("No voice id. Run `clone` first, or pass --voice-id.")
    text = args.text
    if args.text_file:
        text = pathlib.Path(args.text_file).read_text(encoding="utf-8")
    if not text or not text.strip():
        sys.exit("Provide --text or --text-file.")
    payload = {
        "text": text,
        "model_id": args.model,
        "voice_settings": {
            "stability": args.stability,
            "similarity_boost": args.similarity,
            "style": args.style,
            "use_speaker_boost": True,
        },
    }
    resp = requests.post(
        f"{API}/v1/text-to-speech/{voice_id}",
        headers=hdr({"Content-Type": "application/json", "Accept": "audio/mpeg"}),
        json=payload, timeout=300,
    )
    if resp.status_code >= 400:
        die(resp, "Text-to-speech")
    pathlib.Path(args.out).write_bytes(resp.content)
    print(f"Wrote {args.out} ({len(resp.content):,} bytes)")


def cmd_pvc_guide(args):
    print(__doc__.split("Setup")[0].strip())
    print("\nProfessional Voice Cloning (the 'trained' / fine-tuned model):\n"
          "  PVC trains a dedicated model on a larger dataset (~30 min-3 hrs of clean\n"
          "  audio) and takes a few hours to fine-tune. The API requires the Creator\n"
          "  plan and an identity-verification CAPTCHA, so start it in the dashboard:\n"
          "    https://elevenlabs.io/app/voice-lab  (Add Voice -> Professional)\n"
          "  Once it finishes training you'll have a voice_id you can use here:\n"
          "    python3 elevenlabs_voice.py say --voice-id <pvc_voice_id> --text \"...\" --out out.mp3\n"
          "  Docs: https://elevenlabs.io/docs/cookbooks/voices/professional-voice-cloning")


def main():
    ap = argparse.ArgumentParser(description="Create and use a reusable ElevenLabs voice.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("clone", help="create a reusable voice from sample audio (Instant Voice Cloning)")
    c.add_argument("--name", required=True)
    c.add_argument("--files", nargs="+", required=True, help="one or more clean sample audio files")
    c.add_argument("--description", default="")
    c.add_argument("--denoise", action="store_true", help="ask ElevenLabs to remove background noise")
    c.set_defaults(func=cmd_clone)

    sub.add_parser("voices", help="list voices in your account").set_defaults(func=cmd_voices)
    sub.add_parser("models", help="list available models").set_defaults(func=cmd_models)

    s = sub.add_parser("say", help="synthesize text with the voice")
    s.add_argument("--text")
    s.add_argument("--text-file")
    s.add_argument("--voice-id", help="override the saved voice id")
    s.add_argument("--model", default="eleven_multilingual_v2")
    s.add_argument("--out", default="out.mp3")
    s.add_argument("--stability", type=float, default=0.5)
    s.add_argument("--similarity", type=float, default=0.85)
    s.add_argument("--style", type=float, default=0.0)
    s.set_defaults(func=cmd_say)

    sub.add_parser("pvc-guide", help="how to make a trained Professional Voice Clone").set_defaults(func=cmd_pvc_guide)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
