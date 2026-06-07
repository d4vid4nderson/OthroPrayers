# Prayers for Morning, Day & Night — web edition

A faithful web reproduction of the booklet **_Prayers for Morning, Day &
Night_** (St. Tikhon's Monastery Press, 2019; made available by the Orthodox
Church in America at
[oca.org](https://www.oca.org/files/PDF/Music/Daily/morning-evening-prayers.pdf)).

The page is a single, self-contained static site (`index.html` + `styles.css`
+ images) that mirrors the printed booklet: white pages, classical serif type,
red rubrics, drop-caps, the illuminated initial, the three red line-icons, the
priest/layman table at meals, and the tapering colophon at the end.

```
open index.html        # or serve the folder with any static host
```

## How it's built

Rather than retyping the prayers (and risking transcription errors), the page
is **generated directly from the source PDF**, so the wording, the red/black
styling, the drop-caps and the small-caps lead-ins are taken from the document
itself.

| file | purpose |
|------|---------|
| `source.pdf` | the original OCA / St. Tikhon's booklet (build input) |
| `generate.py` | parses `source.pdf` → `prayers.content.html` (structure + styling derived from the PDF's fonts, colours and geometry) |
| `build.py` | wraps the content fragment in the cover + page shell → `index.html` |
| `styles.css` | typography and layout matching the booklet |
| `prayers.content.html` | generated body fragment (checked in so the site works without a build step) |
| `assets/img/` | the three red icons + the illuminated “T”, extracted from the PDF |

To rebuild after changing anything:

```bash
pip install PyMuPDF pillow
python3 generate.py     # PDF  -> prayers.content.html
python3 build.py        # cover + content -> index.html
```

### How the generator works (notes)

- **Drop-caps** are the Arno Pro *Display* glyphs; the small-caps lead-in after
  them (e.g. `R`+`ising`) is reconstructed from the source layout.
- **Rubrics / red text** are detected by colour (`#e54e62`); body ink is
  `#231f20`; the cover links are the PDF's blue `#1e5e9e`.
- **Running heads and folios** are dropped by position; **paragraphs** are
  recovered from first-line indents; **wrapped words** are de-hyphenated using a
  whitelist of genuine compounds harvested from the document.
- The **priest / layman** instructions are a two-column table in the PDF; the
  generator re-assembles the interleaved rows into hanging label + response.
- The ornamental **“Through the prayers…” initial** has no text glyph in the
  PDF (it's drawn), so it is extracted as a transparent PNG and re-placed.

## Fonts

The booklet is set in **Adobe Arno Pro**, a *licensed* typeface that cannot be
redistributed for the web. This edition therefore uses **EB Garamond** (SIL
Open Font License) — the closest freely-licensed Aldine/Garalde serif — loaded
from Google Fonts.

If you own an Arno Pro web licence, drop the font files in a `fonts/` folder,
add an `@font-face`, and put `"Arno Pro"` at the front of the `--serif`
variable in `styles.css`; the page will use it automatically.

### Reader settings

The top-bar gear (⚙) opens a settings menu with **text size**, **light / dark
theme** (sun & moon icons; dark is a dark-gray page with light + red text), and
a **dyslexia-friendly** reading mode that switches to **OpenDyslexic** with
left-aligned, loosened spacing. Choices persist in `localStorage` and the theme
follows the OS setting by default. Both EB Garamond and OpenDyslexic are
self-hosted under the SIL Open Font License (`fonts/OFL.txt`,
`fonts/OpenDyslexic-LICENSE.txt`) — no third-party font requests.

## Attribution & copyright

These prayers are excerpted from **_Orthodox Christian Prayers_**, edited by
Priest John Mikitish & Hieromonk Herman (Majkrzak) (South Canaan, Penn.:
**St. Tikhon's Monastery Press**, 2019). **© 2019 St. Tikhon's Monastery
Press. All rights reserved.** The original booklet states that permission is
granted for the document to be made available on www.oca.org for those who wish
to use these prayers in their homes.

The translation, the iconographic line-art, and the typesetting are the
property of St. Tikhon's Monastery Press / OCA. This repository reproduces them
for personal/devotional use with attribution preserved. **Review these terms
before publishing this site publicly**, and consider contacting St. Tikhon's
Monastery Press for any use beyond the permission above.
