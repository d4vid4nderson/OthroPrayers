# Western Rite Prayers

A Western Rite Orthodox prayer book as a native iOS app: the four hours of the
day, *A Little Prayer Book*, the St. Peter Pew Missal and the Vicariate's
fasting norms.

Everything is held on the device. **The app makes no network requests at all** —
it works in a basement, on a plane, and in church. It is built for personal use
on your own phone, not for the App Store.

The app is the SwiftUI one in [`ios/`](ios/) — see
[`ios/NATIVE.md`](ios/NATIVE.md) for building, signing and TestFlight.

## How the prayers get into the app

The text is never retyped. It is generated from the source booklet and carried
through to the app by two scripts, so the app cannot drift from the source:

```
source.pdf
  → generate.py          → prayers.content.html   (the text, committed)
  → build.py             → build/*.html           (intermediate, gitignored)
  → export_content.py    → ios/Content/content.json
```

```sh
python3 build.py && python3 export_content.py
```

Only the two ends of that chain are committed: `prayers.content.html` and the
JSON the app reads. The HTML in `build/` is an intermediate step and is served
to nobody.

It is worth knowing *why* the HTML is still in the middle. The pages are the
form the prayers were proof-read in, and they are what the safety checks compare
against:

- `export_content.py` refuses to drop markup it does not recognise, rather than
  silently losing a line of a prayer.
- It counts the ✠ cross-marks in the pages and in the model and fails if the two
  disagree. This has caught all ten of them vanishing once already.
- It refuses to write an empty model if the build directory is missing.

`build.py` also writes `ios/Content/structure.json` — the four hours with their
time windows, and each book's section order — so the native UI gets them as data
instead of a second, drifting copy.

## What's here

| | |
|---|---|
| `ios/` | the SwiftUI app — see [`ios/NATIVE.md`](ios/NATIVE.md) |
| `source.pdf`, `generate.py` | the booklet, and the script that reads it |
| `advent-source.pdf`, `generate_advent.py` | the Advent booklet, and the script that reads it |
| `prayers.content.html` | the prayer text, generated from the PDF |
| `advent.content.html` | the Advent devotions, generated from their PDF |
| `build.py` | assembles the pages (intermediate, into `build/`) |
| `export_content.py` | pages → `ios/Content/content.json` |
| `export_music.py` | recordings → `ios/Content/music.json` |
| `generate_icons.py` | the default app icon, from `assets/icons/app-icon.svg` |
| `tools_build_icons.py` | the 96 alternate icons, and their Info.plist entries |

`build.py` still carries a `WESTERN_ONLY` switch from when this was also a
website covering both rites. It defaults to on, and the Eastern content it
would need is no longer in the repository, so `WESTERN_ONLY=0` will not build.

## The app icon

Vector. `assets/icons/app-icon.svg` is the master, with the lettering converted
to outlines so it carries no font dependency and renders identically at any
size.

```sh
python3 generate_icons.py --ios
```

Needs `fontTools` and a rasterizer, and writes the Xcode asset catalog with all
three iOS appearances. It still emits a few web favicons alongside them, left
over from the website; they are harmless and uncommitted.

### The alternates

The reader can rebuild the icon from three axes that do not constrain each
other — what it shows, what it stands on, and what colour it is drawn in — so
there are 3 × 8 × 4 = 96 of them.

```sh
python3 tools_build_icons.py <scratch> ios/App/Resources/AltIcons ios/alticons.yml
```

Needs Pillow and `node` with Playwright. It writes both the images and
`ios/alticons.yml`, the XcodeGen fragment that declares them, from one loop:
an icon with no declaration cannot be chosen, and a declaration with no icon
is a blank square on a home screen.

Every style is vector, drawn from the two SVGs in `assets/icons`, so a clean
checkout can rebuild the whole set. Two raster styles — a block print of the
Mother of God and the Christ medallion from its centre — were dropped: they
were the only part of this that could not be regenerated from the repository,
and a plate of fine hatching asks a lot of a 60pt square.

They are loose 120 and 180px PNGs rather than asset-catalog appiconsets. An
appiconset holds one 1024px image — the size the App Store listing wants, and
about eight times what a home screen ever draws. The whole set is 2.5MB, less
than a seventh of what 70 appiconsets cost, and the same files are what the
picker in Settings draws its tiles from, so the preview is literally the icon.

Only `AppIcon` stays in the catalog: it is the default, so it is the one the
listing is cut from, and the only one that can carry separate light, dark and
tinted appearances. An alternate is a single image, which is why choosing one
trades that away.

## Vercel

`vercel.json` disables Vercel's Git integration: no deployment on push, no
comment on pull requests. It is here because the repository can say that much
to Vercel, and because this app is not a website.

It does not delete the project. Only its dashboard can do that —
vercel.com/fullstackvibes/othro-prayers → Settings → Delete Project — and
until someone does, the project exists with nothing to serve.

## The worship recordings

`ios/Music/` and `hymns/` are deliberately **not** in this repository — the
recordings are other people's published work and this repo is public. A fresh
clone has the Worship screen's manifest and none of its audio. To restore them
on a machine that has the files, put them in `hymns/` and run `python3
export_music.py`.

## Provenance

The prayers are from the Western Rite Vicariate's booklets. The text is
reproduced from the source document rather than transcribed, so the wording and
the rubrics are the booklet's own.
