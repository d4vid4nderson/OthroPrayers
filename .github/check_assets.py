#!/usr/bin/env python3
"""Every image the app declares must actually be in the repository.

The icon picker shipped twice with nothing in it. The second time, the cause
was .gitignore: an unanchored "preview*.png" rule left over from the web build
matched every Assets.xcassets/Preview*.imageset/preview.png, so the imagesets
were committed with a Contents.json naming a file that was not. Checking that
the files existed on disk — which I did — could not see it.

Two declarations to check now. The asset catalogue holds the default icon;
the 160 alternates are loose PNGs named by ios/alticons.yml, where the same
mistake would be quieter still — a name with no file is a home screen with a
blank square on it, and nothing says so until the icon is chosen on a phone.
"""
import json
import pathlib
import re
import subprocess
import sys


def tracked_under(path):
    return set(subprocess.run(["git", "ls-files", str(path)],
                              capture_output=True, text=True).stdout.split())


missing = []

root = pathlib.Path("ios/App/Resources/Assets.xcassets")
tracked = tracked_under(root)
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

spec = pathlib.Path("ios/alticons.yml")
alt = pathlib.Path("ios/App/Resources/AltIcons")
alt_tracked = tracked_under(alt)
# Parsed with a regex rather than a YAML library so the check has no
# dependency of its own; the file is generated, so its shape is known.
names = re.findall(r"^ {14}CFBundleIconFiles: \[(.+)\]$", spec.read_text(),
                   re.M)
for name in names:
    for scale in ("@2x", "@3x"):
        path = alt / f"{name}{scale}.png"
        if not path.exists():
            missing.append((str(path), "declared in alticons.yml, not on disk"))
        elif str(path) not in alt_tracked:
            missing.append((str(path), "on disk but not tracked by git"))

# And the other way: a file nothing declares is dead weight in the bundle.
declared = {f"{n}{s}.png" for n in names for s in ("@2x", "@3x")}
for path in sorted(alt.glob("*.png")):
    if path.name not in declared:
        missing.append((str(path), "shipped but declared by nothing"))

if missing:
    print(f"{len(missing)} image files are declared but will not ship, "
          "or ship for nothing:\n")
    for path, why in missing[:20]:
        print(f"  {path}  — {why}")
    sys.exit(1)
print(f"{root}: every referenced file is present and tracked")
print(f"{spec}: {len(names)} alternate icons, all present and tracked")
