# Voice-recording script

Read this aloud to capture a sample for cloning. **Instant Voice Cloning** needs
only ~1–3 minutes of clean audio — reading this once at a calm pace is enough.
For **Professional Voice Cloning**, read it through 2–3 times (or keep going)
to reach ~30+ minutes.

## How to record well
- Quiet room, no echo; phone or laptop mic is fine if it's close and steady.
- Keep a **consistent distance** from the mic (about a hand-span) and a steady volume.
- Record **mono**, save as `.mp3`, `.wav`, or `.m4a`.
- **Read the way you want the app to sound** — calm, measured, reverent. The clone
  copies your *tone and pace*, so this reading is the style you'll get.
- Pause briefly between paragraphs; if you stumble, just pause and re-read the line.

Then:
```bash
python3 voice/elevenlabs_voice.py clone --name "Reader" --files my_recording.mp3 --denoise
python3 voice/elevenlabs_voice.py say --text "Glory to Thee, O Lord." --out test.mp3
```

---

## Part 1 — Warm-up (natural speaking)
Hello. This is my voice, recorded so it can be used to read aloud. I am speaking
clearly and calmly, at a steady, comfortable pace, the way I would want a prayer
to be read.

## Part 2 — Variety of sounds
The quick brown fox jumps over the lazy dog. Pack my box with five dozen jugs.
Bright spring mornings, soft evening shadows, and the slow, warm light of autumn.
She sells thin shells by the shore, while the deep river rolls quietly onward.
Whisper, then speak; murmur, then proclaim — the voice can be both gentle and full.

## Part 3 — Numbers, dates, and pauses
We counted one, two, three, then ten, twenty, and one hundred. On the third of
June, at half past seven in the morning, the bells rang twice. Chapter four,
verse nine. The year was three hundred and twenty-five.

## Part 4 — Questions and emphasis
Are you ready to begin? Listen — do you hear it? Lift up your hearts! Be still,
and be at peace. Truly, this is good; truly, it is right.

## Part 5 — Names and church words (for clear pronunciation)
Theotokos. Trisagion. Cherubim and seraphim. Chrysostom. Athanasius. Irenaeus.
Cappadocia. Nicaea. Chalcedon. Antioch. Alexandria. Hieromonk. Akathist.
Hallowed, blessed, almighty, everlasting.

## Part 6 — Reverent cadence (read slowly)
Let us begin in stillness, with a quiet and attentive heart.
We give thanks for the light of this morning, and for the rest of the night now past.
Guide our steps through the hours of the day, and keep our minds in peace.
When evening comes, we lay down our cares, grateful for mercy and for grace.
Watch over those we love, near and far, and grant rest to all who are weary.
And as the night draws near, let us close the day in thanksgiving, calm and unafraid.

## Part 7 — Closing
Thank you. That is the end of the recording.
