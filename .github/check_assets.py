#!/usr/bin/env python3
"""Every file an asset catalog refers to must actually be in the repository.

The icon picker shipped twice with nothing in it. The second time, the cause
was .gitignore: an unanchored "preview*.png" rule left over from the web build
matched every Assets.xcassets/Preview*.imageset/preview.png, so the imagesets
were committed with a Contents.json naming a file that was not. Checking that
the files existed on disk — which I did — could not see it.
"""
import json
import pathlib
import subprocess
import sys

root = pathlib.Path("ios/App/Resources/Assets.xcassets")
tracked = set(subprocess.run(["git", "ls-files", str(root)],
                             capture_output=True, text=True).stdout.split())

missing = []
for contents in root.rglob("Contents.json"):
    try:
        spec = json.loads(contents.read_text())
    except json.JSONDecodeError as e:
        missing.append((str(contents), f"unreadable: {e}"))
        continue
    for image in spec.get("images", []):
        name = image.get("filename")
        if not name:
            continue
        path = contents.parent / name
        if not path.exists():
            missing.append((str(path), "not on disk"))
        elif str(path) not in tracked:
            missing.append((str(path), "on disk but not tracked by git"))

if missing:
    print(f"{len(missing)} asset files are referenced but will not ship:\n")
    for path, why in missing[:20]:
        print(f"  {path}  — {why}")
    sys.exit(1)
print(f"every file referenced by {root} is present and tracked")
