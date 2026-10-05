#!/usr/bin/env python3
"""Build the worship manifest and stage the recordings for the iOS bundle.

The recordings are other people's published work and are deliberately not in
this repository (see .gitignore). Put them in hymns/ and run:

    python3 export_music.py

hymns/ is read as the shelf it looks like. A folder of recordings is a
collection, and gets its own page in the app; a loose file beside the folders
is a single, and sits on the worship screen itself. The script normalises the
filenames, reads each duration, copies the audio to ios/Music/ where
project.yml picks it up as a folder reference, and writes the manifest the app
decodes at launch.
"""

import json
import os
import re
import shutil
import subprocess
import sys

SRC = "hymns"
DST = "ios/Music"
MANIFEST = "ios/Content/music.json"


def slug(title: str) -> str:
    t = title.lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def duration(path: str) -> int:
    """Seconds, via afinfo. Zero if it cannot be read, so one odd file does
    not stop the build — it just shows no length in the list."""
    out = subprocess.run(["afinfo", path], capture_output=True, text=True).stdout
    m = re.search(r"estimated duration: ([\d.]+)", out)
    return round(float(m.group(1))) if m else 0


def artist(path: str) -> str | None:
    """Whoever the file's own tags say recorded it, read through Spotlight so
    the script keeps to tools that ship with the Mac. Only the singles need
    this: a collection's tracks are all attributed to the collection."""
    out = subprocess.run(["mdls", "-raw", "-name", "kMDItemAuthors", path],
                         capture_output=True, text=True).stdout
    m = re.search(r'"(.+?)"', out)
    return m.group(1) if m else None


def mp3s(folder: str) -> list[str]:
    return sorted(f for f in os.listdir(folder) if f.lower().endswith(".mp3"))


def name_of(folder: str, files: list[str]) -> str:
    """What to call a collection. When every file in it is named
    "<Name> - <Title>.mp3" the recordings name themselves, which is the better
    source: a folder name is typed once, in a hurry, and may be misspelled."""
    split = [f[:-4].split(" - ", 1) for f in files]
    if all(len(p) == 2 for p in split):
        names = {p[0] for p in split}
        if len(names) == 1:
            return names.pop()
    return os.path.basename(folder)


def stage(folder: str, filename: str, prefix: str, strip: str | None,
          source: str | None) -> dict:
    """Copy one recording into the bundle's Music/ and describe it.

    Music/ stays flat — the app looks tracks up by name in that one directory —
    so a collection's files carry its slug to keep two "The Great Doxology"s
    from landing on each other."""
    title = filename[:-4]
    if strip and title.startswith(strip):
        title = title[len(strip):]
    src = os.path.join(folder, filename)
    name = prefix + slug(title) + ".mp3"
    shutil.copy2(src, os.path.join(DST, name))
    track = {"file": name, "title": title, "seconds": duration(src)}
    if source:
        track["source"] = source
    return track


def main() -> int:
    if not os.path.isdir(SRC):
        print(f"no {SRC}/ here — put the recordings in {SRC}/", file=sys.stderr)
        return 1

    os.makedirs(DST, exist_ok=True)

    singles = [stage(SRC, fn, "", None, artist(os.path.join(SRC, fn)))
               for fn in mp3s(SRC)]
    singles.sort(key=lambda t: t["title"])

    collections = []
    for entry in sorted(os.listdir(SRC)):
        folder = os.path.join(SRC, entry)
        if not os.path.isdir(folder):
            continue
        files = mp3s(folder)
        if not files:
            continue
        name = name_of(folder, files)
        tracks = [stage(folder, fn, slug(name) + "--", name + " - ", name)
                  for fn in files]
        tracks.sort(key=lambda t: t["title"])
        collections.append({"name": name, "tracks": tracks})

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump({"singles": singles, "collections": collections}, f,
                  indent=1, ensure_ascii=False)

    # Clear out whatever an earlier run left behind, so a recording that has
    # been renamed or taken out of hymns/ does not linger in the bundle.
    keep = {t["file"] for t in singles}
    keep |= {t["file"] for c in collections for t in c["tracks"]}
    for fn in os.listdir(DST):
        if fn.lower().endswith(".mp3") and fn not in keep:
            os.remove(os.path.join(DST, fn))

    every = singles + [t for c in collections for t in c["tracks"]]
    total = sum(t["seconds"] for t in every)
    print(f"{len(every)} tracks — {len(collections)} collection(s), "
          f"{len(singles)} single(s) — {total // 60}m {total % 60}s -> {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
