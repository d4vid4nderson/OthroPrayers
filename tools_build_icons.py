#!/usr/bin/env python3
"""Build the app's alternate icons: style x background x mark, independently.

    python3 tools_build_icons.py <scratch-dir> ios/App/Resources/AltIcons \
                                 ios/alticons.yml

The three axes are free of each other, which is the point: a black mark on the
Sunrise gradient is a combination, not a palette someone had to think of in
advance. 3 x 8 x 4 = 96 icons.

Three styles, all of them vector. There were two more — a block-print icon of
the Mother of God and the Christ medallion cut from its centre — and they are
gone, which is worth saying plainly: they were raster engravings, they were
the only part of this that could not be rebuilt from the repository, and at
60pt they asked a lot of a home screen. Everything here now comes from the
two SVGs in assets/icons, so a clean checkout can regenerate the whole set.

They ship as loose 120px and 180px files rather than 1024px asset-catalog
entries. A home-screen icon is never drawn above 180px — 1024 is for the App
Store listing, which only the default icon needs — so the large versions were
costing tens of megabytes to show detail no one ever sees.

The same files serve the picker's thumbnails, because UIImage(named:) finds a
loose bundle file by name. There is no second copy of anything.

Needs Pillow and node with playwright.
"""
import pathlib
import subprocess
import sys

from PIL import Image

MASTER = "assets/icons/app-icon.svg"
ORTHODOX = "assets/icons/orthodox-cross.svg"

# what iOS actually draws on a home screen: 60pt at @2x and @3x. Rendered at
# 1024 and downsampled, so the edges stay clean.
SCALES = {2: 120, 3: 180}

BACKGROUNDS = {
    "black":   "#000000",
    "slate":   "#1C1C1E",
    "paper":   "#FAF6EE",
    "vellum":  "#F0E4C8",
    "aurora":  ("#3E8E5A", "#5B8DD9"),
    "nebula":  ("#5B8DD9", "#9B7BD4"),
    "vespers": ("#9B7BD4", "#B3322A"),
    "sunrise": ("#FFB454", "#B3322A"),
}

MARKS = {
    "gold":     "#D9B36C",
    "ivory":    "#F5F5F5",
    "black":    "#140F0A",
    "phosphor": "#9BE89B",
}

STYLES = ["mark", "cross", "orthodox"]

GLOW = 0.22          # the radial wash behind the mark
TILT = 0.10          # lit from above


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(h, f):
    r, g, b = rgb(h)
    if f >= 0:
        r, g, b = (round(c + (255 - c) * f) for c in (r, g, b))
    else:
        r, g, b = (round(c * (1 + f)) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def lum(h):
    r, g, b = rgb(h)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def ground_lum(background):
    """One number for a ground, whether it is flat or a gradient."""
    if isinstance(background, str):
        return lum(background)
    return (lum(background[0]) + lum(background[1])) / 2


def shade_to(h, target):
    """Move a colour to a target lightness, keeping its hue.

    Exact rather than iterative: `shade` scales every channel by the same
    factor, and luminance is a weighted sum of the channels, so it moves the
    luminance by that factor too.
    """
    i = lum(h)
    t = min(0.97, max(0.03, target))
    f = (t - i) / max(1e-3, 1 - i) if t > i else t / max(1e-3, i) - 1
    return shade(h, max(-0.95, min(0.95, f)))


# How far, in lightness, a figure has to stand off its ground to be read at
# 60pt, and how wide its own ramp is under that.
CLEAR, SPAN = 0.30, 0.26


def ink_pair(ink, bg):
    """The mark's sheen: which way it runs, and how far it has to go.

    A fixed light-to-dark ramp reads as metal on black and dissolves on
    cream, so the sheen runs away from the ground. But "away" is not enough
    on its own. The grounds that failed hardest were the mid-lightness
    gradients — nebula and sunrise sit right at the middle, where gold and
    ivory and phosphor all live, and a ramp that merely leans away still
    straddles them.

    So the figure is moved until it clears the ground by a fixed margin,
    and no further. Two things fall out of saying it that way. A mark that
    is already clear is left exactly as it was: black on cream, and black on
    any of the gradients, do not move at all — which matters, because that
    pairing is the reason the axes were separated. And when a mark does have
    to move, it moves whichever way is nearer, so gold on nebula pales
    rather than turning to bronze. The hue is the choice; the lightness is
    what it costs to still see it.
    """
    g, i = ground_lum(bg), lum(ink)
    clear, span = CLEAR, SPAN

    def pair(lighter, darker):
        return shade_to(ink, lighter), shade_to(ink, darker)

    if abs(i - g) >= clear:
        # Already clear of its ground, so the mark does not move at all: the
        # ramp simply straddles the lightness it was chosen as. Extending it
        # away from the ground instead would push an already-bright mark off
        # the end — gold on black came out white, which is not gold.
        if i > g:
            return pair(min(0.97, i + span * 0.55),
                        max(i - span * 0.45, g + clear))
        return pair(min(i + span * 0.55, g - clear),
                    max(0.03, i - span * 0.45))

    # Too close to its ground to be read, so it has to move — whichever way
    # is nearer, and only as far as it must. Going up from a mid gradient
    # pales gold; going down would turn it to bronze, which is further from
    # what was asked for.
    up, down = min(0.97, g + clear), max(0.03, g - clear)
    if up - g >= clear - 1e-6 and (g - down < clear - 1e-6 or up - i <= i - down):
        return pair(min(0.97, up + span), up)
    return pair(down, max(0.03, down - span))


def glow_strength(ink, bg):
    """No halo when it would only blur the edge it is meant to separate.

    The halo is the mark's own colour, which lifts a gold cross off black.
    Paint the same halo under ivory on vellum and it fills the gap between
    figure and ground with more of the colour they already share. Measured
    from the ink as drawn, not as chosen, since that is what is on the plate.
    """
    drawn = ink_pair(ink, bg)
    near = min(abs(lum(c) - ground_lum(bg)) for c in drawn)
    return GLOW * min(1.0, near * 2.2)


def ramp(a, b, size):
    """A diagonal two-stop gradient, top-left to bottom-right."""
    ca, cb = rgb(a), rgb(b)
    n = max(8, size // 2)
    g = Image.new("RGB", (n, n))
    px = g.load()
    for y in range(n):
        for x in range(n):
            f = (x + y) / (2 * n - 2)
            px[x, y] = tuple(round(ca[i] + (cb[i] - ca[i]) * f) for i in range(3))
    return g.resize((size, size), Image.BILINEAR)


def plate(background, mark, size):
    """The ground, its gradients, and the wash of the mark's colour over it."""
    if isinstance(background, str):
        base = Image.new("RGB", (size, size), rgb(background))
    else:
        base = ramp(background[0], background[1], size)

    lin = Image.linear_gradient("L").resize((size, size), Image.BILINEAR)
    base.paste(Image.new("RGB", (size, size), rgb(mark)), (0, 0),
               Image.eval(lin, lambda v: int((255 - v) * TILT)))
    base.paste(Image.new("RGB", (size, size), (0, 0, 0)), (0, 0),
               Image.eval(lin, lambda v: int(v * TILT * 0.9)))
    g = glow_strength(mark, background)
    rad = Image.radial_gradient("L").resize((size, size), Image.BILINEAR)
    base.paste(Image.new("RGB", (size, size), rgb(mark)), (0, 0),
               Image.eval(rad, lambda v: int(max(0, 255 - v * 1.6) * g)))
    return base


def svg_defs(background, mark):
    lo, hi = ink_pair(mark, background)
    g = glow_strength(mark, background)
    bg = (f'<rect width="1024" height="1024" fill="{background}"/>'
          if isinstance(background, str) else
          '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
          f'<stop offset="0%" stop-color="{background[0]}"/>'
          f'<stop offset="100%" stop-color="{background[1]}"/></linearGradient></defs>'
          '<rect width="1024" height="1024" fill="url(#bg)"/>')
    washes = (
        '<defs><linearGradient id="t" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{mark}" stop-opacity="{TILT}"/>'
        f'<stop offset="55%" stop-color="{mark}" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="#000000" stop-opacity="{TILT*0.9:.3f}"/>'
        '</linearGradient>'
        f'<radialGradient id="g" cx="50%" cy="50%" r="62%">'
        f'<stop offset="0%" stop-color="{mark}" stop-opacity="{g:.3f}"/>'
        f'<stop offset="55%" stop-color="{mark}" stop-opacity="{g*0.3:.3f}"/>'
        f'<stop offset="100%" stop-color="{mark}" stop-opacity="0"/></radialGradient>'
        # bottom-left to top-right, against the ground's top-left to
        # bottom-right. Parallel was the quiet mistake: the figure's light end
        # landed on the ground's light end and its dark end on the ground's
        # dark end, so the one place the two could have separated was the one
        # place they matched.
        f'<linearGradient id="ink" x1="0" y1="1" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{lo}"/>'
        f'<stop offset="100%" stop-color="{hi}"/></linearGradient></defs>'
        '<rect width="1024" height="1024" fill="url(#t)"/>'
        '<rect width="1024" height="1024" fill="url(#g)"/>')
    return bg + washes


def cross_only(svg):
    """The master's first <path> is the cross; the rest is the lettering."""
    o = svg.index("<g fill=")
    a = svg.index("<path", o)
    b = svg.index("/>", a) + 2
    return (svg[:o] + "__DEFS__"
            + '<g transform="translate(512,512) scale(1.42) translate(-512,-512)">'
            + '<g fill="url(#ink)">' + svg[a:b] + "</g></g></svg>")


def name(background, style, mark):
    return f"alt-{background}-{style}-{mark}"


def main():
    scratch, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    renderer = scratch / "render_one.js"

    master = pathlib.Path(MASTER).read_text()
    ortho = pathlib.Path(ORTHODOX).read_text()
    svgs = {
        "mark": master.replace('<rect width="1024" height="1024" fill="#0C0D10"/>',
                               "__DEFS__").replace('fill="#D9B36C"', 'fill="url(#ink)"'),
        "cross": cross_only(master),
        "orthodox": ortho.replace('<rect width="1024" height="1024" fill="__G__"/>',
                                  "__DEFS__").replace('fill="__I__"', 'fill="url(#ink)"'),
    }

    made = []
    for bg_name, bg in BACKGROUNDS.items():
        for mk_name, mk in MARKS.items():
            for style in STYLES:
                stem = name(bg_name, style, mk_name)
                art = svgs[style].replace("__DEFS__", svg_defs(bg, mk))
                tmp = scratch / f"_{stem}.svg"
                tmp.write_text(art)
                big = scratch / f"_{stem}.png"
                subprocess.run(["node", str(renderer), str(tmp), str(big),
                                bg if isinstance(bg, str) else bg[0], mk],
                               check=True)
                full = Image.open(big).convert("RGB")
                for scale, px in SCALES.items():
                    full.resize((px, px), Image.LANCZOS).save(
                        out / f"{stem}@{scale}x.png", optimize=True)
                made.append(stem)

    print(f"  {len(made)} icons, {len(made) * len(SCALES)} files")
    total = sum(p.stat().st_size for p in out.glob("*.png"))
    print(f"  {total / 1e6:.1f} MB")

    if len(sys.argv) > 3:
        write_spec(pathlib.Path(sys.argv[3]), made)
        print(f"  wrote {sys.argv[3]}")


def write_spec(path, names):
    """The XcodeGen fragment that declares these icons to iOS.

    Written here rather than kept by hand in project.yml because the two have
    to agree exactly: an icon with no declaration cannot be chosen, and a
    declaration with no icon is a blank home screen. Generating both from one
    loop is the only way they stay in step.

    Loose files and an Info.plist entry, not asset-catalog appiconsets. Those
    carry a 1024px image apiece, which is the size the App Store listing
    wants and about eight times what a home screen ever draws — 160 of them
    came to roughly 40MB of detail nobody sees. Only the default icon, which
    stays in the catalogue, needs the large one.
    """
    lines = [
        "# Generated by tools_build_icons.py. Do not edit.",
        "#",
        "# Merged into project.yml through its `include`. One entry per",
        "# alternate icon: the key is the name passed to",
        "# setAlternateIconName, and CFBundleIconFiles names the loose PNGs",
        "# (<name>@2x.png and <name>@3x.png) at the bundle root.",
        "targets:",
        "  Prayers:",
        "    info:",
        "      properties:",
        "        CFBundleIcons:",
        "          CFBundleAlternateIcons:",
    ]
    for n in names:
        lines.append(f"            {n}:")
        lines.append(f"              CFBundleIconFiles: [{n}]")
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
