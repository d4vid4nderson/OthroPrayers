#!/usr/bin/env python3
"""Build the worship manifest and stage the recordings for the iOS bundle.

The recordings themselves are the monastery's work and are deliberately not in
this repository (see .gitignore). Drop the album folder in beside this script
and run:

    python3 export_music.py

It normalises the filenames, reads each duration, copies the audio to
ios/Music/ where project.yml picks it up as a folder reference, and writes the
manifest the app decodes at launch.
"""

import json
import os
import re
import shutil
import subprocess
import sys

SRC = "All-Merciful Savior Monistery"
DST = "ios/Music"
MANIFEST = "ios/Content/music.json"
COLLECTION = "All-Merciful Saviour Monastery"
PREFIX = COLLECTION + " - "


def slug(title: str) -> str:
    t = title.lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def duration(path: str) -> int:
    """Seconds, via afinfo. Zero if it cannot be read, so one odd file does
    not stop the build — it just shows no length in the list."""
    out = subprocess.run(["afinfo", path], capture_output=True, text=True).stdout
    m = re.search(r"estimated duration: ([\d.]+)", out)
    return round(float(m.group(1))) if m else 0


def main() -> int:
    if not os.path.isdir(SRC):
        print(f"no {SRC}/ here — put the album folder beside this script", file=sys.stderr)
        return 1

    os.makedirs(DST, exist_ok=True)
    tracks = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith(".mp3"):
            continue
        title = fn[:-4]
        if title.startswith(PREFIX):
            title = title[len(PREFIX):]
        name = slug(title) + ".mp3"
        src = os.path.join(SRC, fn)
        shutil.copy2(src, os.path.join(DST, name))
        tracks.append({"file": name, "title": title, "seconds": duration(src)})

    tracks.sort(key=lambda t: t["title"])
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump({"collection": COLLECTION, "tracks": tracks}, f, indent=1, ensure_ascii=False)

    total = sum(t["seconds"] for t in tracks)
    print(f"{len(tracks)} tracks, {total // 60}m {total % 60}s -> {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
