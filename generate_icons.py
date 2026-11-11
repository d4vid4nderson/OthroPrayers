"""App-icon generator.

Draws the IC XC NIKA mark as vector art and renders every size the app needs:
the web favicons and PWA icons, and the Xcode asset catalog with all three
iOS appearances.

The mark is a pattée cross with the nomina sacra in Uncial Antiqua — the same
hand the Manuscript style uses — flanking the arms, with titlo bars over IC and
XC. The lettering is converted to outlines here, so the SVG master carries no
font dependency and renders identically anywhere.

This replaces a pipeline that cut the icon out of a 356px screenshot, which
meant every size above that was an upscale. Nothing is upscaled now.

    python3 -m venv /tmp/venv
    /tmp/venv/bin/pip install fonttools brotli
    /tmp/venv/bin/python generate_icons.py          # web icons
    /tmp/venv/bin/python generate_icons.py --ios    # + the Xcode catalog

Rasterising uses Playwright's Chromium (PLAYWRIGHT_BROWSERS_PATH).
"""
import json
import os
import struct
import subprocess
import sys
import tempfile

OUT = "assets/icons"
SVG_MASTER = f"{OUT}/app-icon.svg"
IOS_SET = "ios/AppIcon.appiconset"
IOS_XCODE = "ios/App/Resources/Assets.xcassets/AppIcon.appiconset"
FONT = "fonts/uncial-antiqua.woff2"

# ---- palettes, taken from the stylesheets so the icon cannot drift ---------
DARK = ("#0C0D10", "#D9B36C")      # Sanctuary ground, Sanctuary gold
LIGHT = ("#FAF6EE", "#8A6B16")     # Paper stock, a deeper gold that holds on it
TINTED = ("#1C1C1E", "#C9C9CE")    # greyscale; iOS recolours it

# ---- geometry -------------------------------------------------------------
# A pattée cross on a 1024 canvas: narrow at the waist, flaring to a slightly
# concave tip.
CROSS = ("M 486 486 "
         "Q 486 356, 450 312 Q 512 326, 574 312 Q 538 356, 538 486 "
         "Q 668 486, 712 450 Q 698 512, 712 574 Q 668 538, 538 538 "
         "Q 538 668, 574 712 Q 512 698, 450 712 Q 486 668, 486 538 "
         "Q 356 538, 312 574 Q 326 512, 312 450 Q 356 486, 486 486 Z")

# "Tighter": the words flank the arms rather than sitting out in the corners.
DX, DY_TOP, DY_BOT, LETTER = 258, 330, 762, 150
# the bar sits clear above the letters: at 104 it touched their cap line,
# which reads as a mistake rather than a scribal mark
TITLO_HALF, TITLO_DROP, TITLO_W = 88, 122, 9


def letter_paths(text, size, cx, baseline):
    """The glyph outlines for `text`, centred on `cx`, as one SVG group.

    Converting to outlines is what makes the master self-contained: no
    @font-face, no font file at render time, and no chance of a substituted
    face quietly changing the mark.
    """
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen

    font = TTFont(FONT)
    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    hmtx = font["hmtx"]
    scale = size / upem

    commands, advance = [], 0
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            sys.exit(f"{ch!r} is not in {FONT}")
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        d = pen.getCommands()
        if d:
            commands.append(f'<path d="{d}" transform="translate({advance} 0)"/>')
        advance += hmtx[name][0]

    width = advance * scale
    x = cx - width / 2
    # font space is y-up, SVG is y-down, hence the negative vertical scale
    return (f'<g transform="translate({x:.2f} {baseline:.2f}) '
            f'scale({scale:.6f} {-scale:.6f})">' + "".join(commands) + "</g>")


def mark(ground, ink, *, letters=True, scale=1.0):
    """The whole icon as SVG, in a given palette."""
    art = [f'<path d="{CROSS}"/>']
    if letters:
        left, right = 512 - DX, 512 + DX
        for cx, baseline, text in ((left, DY_TOP, "IC"), (right, DY_TOP, "XC"),
                                   (left, DY_BOT, "NI"), (right, DY_BOT, "KA")):
            art.append(letter_paths(text, LETTER, cx, baseline))
        # the titlo: the bar marking a contracted holy name. Not decoration.
        y = DY_TOP - TITLO_DROP
        for cx in (left, right):
            art.append(f'<rect x="{cx - TITLO_HALF}" y="{y - TITLO_W / 2}" '
                       f'width="{TITLO_HALF * 2}" height="{TITLO_W}" rx="{TITLO_W / 2}"/>')
    inner = "".join(art)
    if scale != 1.0:
        inner = (f'<g transform="translate(512 512) scale({scale}) '
                 f'translate(-512 -512)">{inner}</g>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" '
            'width="1024" height="1024">'
            f'<rect width="1024" height="1024" fill="{ground}"/>'
            f'<g fill="{ink}">{inner}</g></svg>')


# ---- rasterising ----------------------------------------------------------
RENDER_JS = r"""
import { chromium } from "/opt/node22/lib/node_modules/playwright/index.mjs";
import { readFileSync, writeFileSync } from "node:fs";
const jobs = JSON.parse(readFileSync(process.argv[2], "utf8"));
const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
const page = await b.newPage();
for (const job of jobs) {
  await page.setViewportSize({ width: job.size, height: job.size });
  await page.setContent(`<!doctype html><style>html,body{margin:0}
    svg{display:block;width:${job.size}px;height:${job.size}px}</style>${job.svg}`);
  writeFileSync(job.out, await page.screenshot({ omitBackground: false }));
}
await b.close();
console.log("rendered " + jobs.length);
"""


def render(jobs):
    """Rasterise a batch of {svg, size, out} in one browser session."""
    for job in jobs:
        os.makedirs(os.path.dirname(job["out"]) or ".", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        spec = os.path.join(tmp, "jobs.json")
        script = os.path.join(tmp, "render.mjs")
        with open(spec, "w") as f:
            json.dump(jobs, f)
        with open(script, "w") as f:
            f.write(RENDER_JS)
        r = subprocess.run(["/opt/node22/bin/node", script, spec],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit("render failed:\n" + r.stdout + r.stderr)


def ico(pngs, sizes, path):
    """PNG-in-ICO — every browser still in use reads it."""
    head = bytearray(6 + 16 * len(pngs))
    struct.pack_into("<HHH", head, 0, 0, 1, len(pngs))
    offset = len(head)
    for i, (blob, s) in enumerate(zip(pngs, sizes)):
        struct.pack_into("<BBBBHHII", head, 6 + 16 * i,
                         s if s < 256 else 0, s if s < 256 else 0, 0, 0,
                         1, 32, len(blob), offset)
        offset += len(blob)
    with open(path, "wb") as f:
        f.write(bytes(head))
        for blob in pngs:
            f.write(blob)
    print(f"  favicon.ico  {'/'.join(str(s) for s in sizes)}")


def main():
    want_ios = "--ios" in sys.argv

    dark = mark(*DARK)
    # at favicon sizes the lettering is mud, so the cross carries it alone
    dark_cross = mark(*DARK, letters=False, scale=1.08)
    light_cross = mark(*LIGHT, letters=False, scale=1.08)

    os.makedirs(OUT, exist_ok=True)
    with open(SVG_MASTER, "w") as f:
        f.write(dark + "\n")

    jobs = [
        {"svg": dark, "size": 512, "out": f"{OUT}/icon-512.png"},
        {"svg": dark, "size": 192, "out": f"{OUT}/icon-192.png"},
        # maskable: the launcher crops to a circle 80% across, so the art is
        # pulled inside it and the ground fills the rest
        {"svg": mark(*DARK, scale=0.74), "size": 512, "out": f"{OUT}/icon-512-maskable.png"},
        {"svg": mark(*DARK, scale=0.74), "size": 192, "out": f"{OUT}/icon-192-maskable.png"},
        {"svg": dark, "size": 180, "out": f"{OUT}/apple-touch-icon.png"},
        # favicons: light browser chrome gets the paper ground, dark gets the
        # app's own
        {"svg": light_cross, "size": 32, "out": f"{OUT}/favicon-32.png"},
        {"svg": light_cross, "size": 16, "out": f"{OUT}/favicon-16.png"},
        {"svg": dark_cross, "size": 32, "out": f"{OUT}/favicon-32-dark.png"},
        {"svg": dark_cross, "size": 16, "out": f"{OUT}/favicon-16-dark.png"},
    ]
    if want_ios:
        jobs += [
            {"svg": dark, "size": 1024, "out": f"{IOS_SET}/AppIcon-1024.png"},
            {"svg": mark(*DARK), "size": 1024, "out": f"{IOS_SET}/AppIcon-1024-dark.png"},
            {"svg": mark(*TINTED), "size": 1024, "out": f"{IOS_SET}/AppIcon-1024-tinted.png"},
        ]
    render(jobs)
    print(f"  {SVG_MASTER}  (self-contained: the lettering is outlines)")
    for job in jobs:
        print(f"  {job['out']}  {job['size']}px")

    with tempfile.TemporaryDirectory() as tmp:
        sizes = (48, 32, 16)
        ico_jobs = [{"svg": dark_cross, "size": s,
                     "out": os.path.join(tmp, f"{s}.png")} for s in sizes]
        render(ico_jobs)
        ico([open(j["out"], "rb").read() for j in ico_jobs], sizes, "favicon.ico")

    if want_ios:
        contents = {"images": [
            {"filename": "AppIcon-1024.png", "idiom": "universal",
             "platform": "ios", "size": "1024x1024"},
            {"appearances": [{"appearance": "luminosity", "value": "dark"}],
             "filename": "AppIcon-1024-dark.png", "idiom": "universal",
             "platform": "ios", "size": "1024x1024"},
            {"appearances": [{"appearance": "luminosity", "value": "tinted"}],
             "filename": "AppIcon-1024-tinted.png", "idiom": "universal",
             "platform": "ios", "size": "1024x1024"},
        ], "info": {"author": "xcode", "version": 1}}
        with open(f"{IOS_SET}/Contents.json", "w") as f:
            json.dump(contents, f, indent=2)
        if os.path.isdir(os.path.dirname(IOS_XCODE)):
            import shutil
            os.makedirs(IOS_XCODE, exist_ok=True)
            for name in os.listdir(IOS_SET):
                shutil.copy2(os.path.join(IOS_SET, name), os.path.join(IOS_XCODE, name))
            print(f"  copied the catalog into {IOS_XCODE}")


if __name__ == "__main__":
    main()
