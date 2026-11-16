#!/usr/bin/env python3
"""Build every app icon and its picker preview.

Five styles across eleven colours, each with a soft glow behind the mark.

The glow is a radial wash of the ink colour over the ground, strongest at the
centre and gone by the corners. It is what stops a flat two-colour plate
looking like a sticker — the mark now sits in a little light rather than on
nothing. Kept low: at 22% it reads as depth, and much above that it reads as
a gradient someone forgot to finish.

Two output kinds, and their Contents.json differ in a way that matters:
an app icon is one 1024 image, and a preview is a *single-scale* imageset —
one entry with no "scale" key at all. Declaring "1x" and leaving 2x and 3x
unfilled, which is what I did the first time, resolves to nothing on a 2x or
3x device and the picker comes back blank.
"""
import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageFilter

SIZE = 1024
PREVIEW = 180
GLOW = 0.22          # peak opacity of the radial wash at the centre
TILT = 0.10          # vertical gradient: lit from above
# the engravings are block prints and were hard to read small. Dilating
# the ink thickens the line work towards the solid areas a block print
# actually has; 0.65 bolds it without flipping it to a solid field.
THICKEN, THICKEN_BLEND = 3, 0.65

COLOURS = {                        # ground, ink
    "Sanctuary":  ("#0C0D10", "#D9B36C"),   # gold, the app's own
    "Paper":      ("#FAF6EE", "#B3322A"),
    "Manuscript": ("#F0E4C8", "#A32A1E"),
    "Terminal":   ("#070A07", "#9BE89B"),
    "Ivory":      ("#000000", "#F5F5F5"),
    "Crimson":    ("#000000", "#B3322A"),
    "Emerald":    ("#000000", "#3E8E5A"),
    "Amber":      ("#000000", "#FFB454"),   # the terminal theme's second phosphor
    "Silver":     ("#000000", "#C9C9CE"),   # the tinted icon's grey
    "Sapphire":   ("#000000", "#5B8DD9"),
    "Violet":     ("#000000", "#9B7BD4"),
}

ICON_CONTENTS = {
    "images": [{"filename": "icon.png", "idiom": "universal",
                "platform": "ios", "size": "1024x1024"}],
    "info": {"author": "xcode", "version": 1},
}
# single scale: no "scale" key. See the note at the top.
PREVIEW_CONTENTS = {
    "images": [{"filename": "preview.png", "idiom": "universal"}],
    "info": {"author": "xcode", "version": 1},
}


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def glow_plate(ground, ink):
    """The ground, a vertical gradient, and a radial wash of the ink.

    Two gradients doing different jobs. The vertical one lifts the top of the
    plate and sinks the bottom, which is what gives a flat colour the sense of
    being lit from above rather than printed. The radial one puts the light
    behind the mark itself.
    """
    plate = Image.new("RGB", (SIZE, SIZE), rgb(ground))

    # vertical: ink over the top, black over the bottom, both weak
    lin = Image.linear_gradient("L").resize((SIZE, SIZE), Image.BILINEAR)
    top = Image.eval(lin, lambda v: int((255 - v) * TILT))
    plate.paste(Image.new("RGB", (SIZE, SIZE), rgb(ink)), (0, 0), top)
    bottom = Image.eval(lin, lambda v: int(v * TILT * 0.9))
    plate.paste(Image.new("RGB", (SIZE, SIZE), (0, 0, 0)), (0, 0), bottom)

    # radial: the light behind the mark
    g = Image.radial_gradient("L").resize((SIZE, SIZE), Image.BILINEAR)
    plate.paste(Image.new("RGB", (SIZE, SIZE), rgb(ink)), (0, 0),
                Image.eval(g, lambda v: int(max(0, 255 - v * 1.6) * GLOW)))
    return plate


def from_mask(src, ground, ink, margin):
    """A block print: dark figure on a coloured field.

    Inverted from the obvious reading of the source. The engraving is dark
    lines on white paper, so painting the lines in the ink colour over a dark
    ground gives thin bright lines on black — which is what a block print is
    not, and which dies at icon size. Putting the colour on the plate and
    cutting the figure out of it in the dark is both what the print looks like
    and far easier to read small.
    """
    art = Image.open(src).convert("L")
    alpha = Image.eval(art, lambda v: 255 - v)
    alpha = Image.blend(alpha, alpha.filter(ImageFilter.MaxFilter(THICKEN)),
                        THICKEN_BLEND)
    box = SIZE - 2 * margin
    w, h = alpha.size
    s = min(box / w, box / h)
    alpha = alpha.resize((round(w * s), round(h * s)), Image.LANCZOS)
    # the plate takes the colour, and the gradients wash the ground over it —
    # the reverse of the drawn styles, because the roles are reversed
    plate = glow_plate(ink, ground)
    plate.paste(Image.new("RGB", alpha.size, rgb(ground)),
                ((SIZE - alpha.size[0]) // 2, (SIZE - alpha.size[1]) // 2), alpha)
    return plate


def svg_glow(ink):
    """The same wash, for the styles that are drawn rather than masked."""
    return (f'<defs>'
            f'<linearGradient id="t" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="{ink}" stop-opacity="{TILT}"/>'
            f'<stop offset="55%" stop-color="{ink}" stop-opacity="0"/>'
            f'<stop offset="100%" stop-color="#000000" stop-opacity="{TILT * 0.9:.3f}"/>'
            f'</linearGradient>'
            f'<radialGradient id="g" cx="50%" cy="50%" r="62%">'
            f'<stop offset="0%" stop-color="{ink}" stop-opacity="{GLOW}"/>'
            f'<stop offset="55%" stop-color="{ink}" stop-opacity="{GLOW * 0.3:.3f}"/>'
            f'<stop offset="100%" stop-color="{ink}" stop-opacity="0"/>'
            f'</radialGradient></defs>'
            f'<rect width="1024" height="1024" fill="url(#t)"/>'
            f'<rect width="1024" height="1024" fill="url(#g)"/>')


def cross_only(svg):
    o = svg.index("<g fill=")
    g_tag = svg[o:svg.index(">", o) + 1]
    a = svg.index("<path", o)
    b = svg.index("/>", a) + 2
    head = svg[:o].replace("#0C0D10", "__G__")
    return (head + "__GLOW__"
            + '<g transform="translate(512,512) scale(1.42) translate(-512,-512)">'
            + g_tag.replace("#D9B36C", "__I__") + svg[a:b] + "</g></g></svg>")


def main():
    scratch, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    renderer = scratch / "render_one.js"
    master = pathlib.Path("assets/icons/app-icon.svg").read_text()
    mark = master.replace("#0C0D10", "__G__").replace("#D9B36C", "__I__")
    mark = mark.replace('fill="__G__"/>', 'fill="__G__"/>__GLOW__', 1)
    cross = cross_only(master)
    ortho = (scratch / "ortho_user.svg").read_text()
    ortho = ortho.replace('fill="__G__"/>', 'fill="__G__"/>__GLOW__', 1)

    n = 0
    for cname, (ground, ink) in COLOURS.items():
        for sname, svg in (("Mark", mark), ("Cross", cross), ("Orthodox", ortho)):
            art = svg.replace("__GLOW__", svg_glow(ink))
            tmp = scratch / f"_{cname}{sname}.svg"
            tmp.write_text(art)
            d = out / f"AppIcon{cname}{sname}.appiconset"
            d.mkdir(parents=True, exist_ok=True)
            subprocess.run(["node", str(renderer), str(tmp),
                            str(d / "icon.png"), ground, ink], check=True)
            flatten(d / "icon.png")
            (d / "Contents.json").write_text(json.dumps(ICON_CONTENTS, indent=2) + "\n")
            n += 1
        # smaller margins than before: the engravings needed to be bigger as
        # well as bolder to read at icon size
        for sname, src, margin in (("Icon", "recovered/icon_p1.png", 50),
                                   ("Medallion", "medallion.png", 60)):
            d = out / f"AppIcon{cname}{sname}.appiconset"
            d.mkdir(parents=True, exist_ok=True)
            from_mask(scratch / src, ground, ink, margin).save(d / "icon.png")
            (d / "Contents.json").write_text(json.dumps(ICON_CONTENTS, indent=2) + "\n")
            n += 1
    print(f"  {n} icon sets")

    p = 0
    for d in sorted(out.glob("AppIcon*.appiconset")):
        name = d.name.removesuffix(".appiconset").removeprefix("AppIcon")
        pv = out / f"Preview{name}.imageset"
        pv.mkdir(parents=True, exist_ok=True)
        Image.open(d / "icon.png").resize((PREVIEW, PREVIEW), Image.LANCZOS) \
             .save(pv / "preview.png")
        (pv / "Contents.json").write_text(json.dumps(PREVIEW_CONTENTS, indent=2) + "\n")
        p += 1
    print(f"  {p} previews")


def flatten(p):
    im = Image.open(p)
    if im.mode != "RGB":
        im.convert("RGB").save(p)


if __name__ == "__main__":
    main()
