"""App-icon generator.

Cuts the two IC XC NIKA medallion icons — bronze for light mode, steel for
dark — out of the supplied mock-up, masks them to the iOS squircle so the
corners come away clean, and writes every size the app needs.

Nothing here runs at page-build time; the icons are committed. Re-run it only
when the artwork changes, with Pillow available:

    python3 -m venv /tmp/venv && /tmp/venv/bin/pip install pillow
    /tmp/venv/bin/python generate_icons.py

Sources are the two masters in assets/icons (app-icon.png / app-icon-dark.png).
Pass the original mock-up as an argument to re-cut them:

    ... generate_icons.py path/to/mockup.png
"""
import io
import os
import struct
import sys

from PIL import Image, ImageFilter

OUT = "assets/icons"
MASTER_LIGHT = f"{OUT}/app-icon.png"
MASTER_DARK = f"{OUT}/app-icon-dark.png"

# where the two icons sit in the supplied 1024x1024 mock-up (left = light mode,
# right = dark); both are 356px square
CUTS = {MASTER_LIGHT: (84, 322, 440, 678), MASTER_DARK: (592, 322, 948, 678)}

SS = 4          # supersampling for the mask edge
EXP = 5.0       # superellipse exponent — the iOS "squircle"
INSET = 1.5     # px trimmed off the edge, so no background fringe survives


def squircle(size, inset=INSET):
    """An anti-aliased iOS-style rounded-square alpha mask."""
    n = size * SS
    half = n / 2.0
    r = half - inset * SS
    mask = Image.new("L", (n, n), 0)
    px = mask.load()
    for y in range(n):
        dy = abs((y + 0.5) - half) / r
        if dy > 1:
            continue
        # x where |x/r|^EXP + dy^EXP = 1
        rem = 1.0 - dy ** EXP
        dx = rem ** (1.0 / EXP)
        x0 = int(half - dx * r)
        x1 = int(half + dx * r)
        for x in range(max(0, x0), min(n, x1)):
            px[x, y] = 255
    return mask.resize((size, size), Image.LANCZOS)


def cut(mockup):
    """Re-cut both masters out of the mock-up."""
    src = Image.open(mockup).convert("RGB")
    for path, box in CUTS.items():
        icon = src.crop(box)
        icon.putalpha(squircle(icon.width))
        icon.save(path)
        print("cut", path, icon.size)


def edge_colour(im):
    """The icon's own border tone — what a flattened icon's background is
    filled with, so the squircle sits on something that belongs to it."""
    w = im.width
    ring = []
    for t in range(6):
        ring += [im.getpixel((x, w // 2 + t - 3)) for x in (t, w - 1 - t)]
        ring += [im.getpixel((w // 2 + t - 3, y)) for y in (t, w - 1 - t)]
    ring = [p for p in ring if p[3] > 200]
    n = len(ring)
    return tuple(sum(p[i] for p in ring) // n for i in range(3)) + (255,)


def render(master, size, scale=1.0, opaque=False, backdrop=False):
    """One icon at one size. `opaque` flattens onto the icon's own border tone;
    `backdrop` instead fills behind it with a blown-up, blurred copy of the same
    metal, so a shrunken icon doesn't read as a plaque sitting on flat mud."""
    im = Image.open(master).convert("RGBA")
    inner = max(1, round(size * scale))
    art = im.resize((inner, inner), Image.LANCZOS)
    if backdrop:
        big = round(size * 1.35)
        out = im.resize((big, big), Image.LANCZOS).convert("RGB")
        crop = (big - size) // 2
        out = out.crop((crop, crop, crop + size, crop + size))
        out = out.filter(ImageFilter.GaussianBlur(size / 22.0)).convert("RGBA")
    else:
        out = Image.new("RGBA", (size, size), edge_colour(im) if opaque else (0, 0, 0, 0))
    off = (size - inner) // 2
    out.paste(art, (off, off), art)
    return out


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
    print("wrote", path, "/".join(str(s) for s in sizes))


def main():
    if len(sys.argv) > 1:
        cut(sys.argv[1])
    for m in (MASTER_LIGHT, MASTER_DARK):
        if not os.path.exists(m):
            sys.exit(f"missing {m} — pass the mock-up to re-cut the masters")

    # the installed-app icons. A manifest cannot switch on colour scheme, so
    # these are the light (bronze) set; the dark artwork is used for the
    # browser tab, where prefers-color-scheme does work.
    for size in (512, 192):
        render(MASTER_LIGHT, size).save(f"{OUT}/icon-{size}.png")
        # maskable: the launcher crops to a circle 80% across, so the medallion
        # is pulled inside that and the icon's own border tone fills the rest
        render(MASTER_LIGHT, size, scale=0.9, backdrop=True).save(f"{OUT}/icon-{size}-maskable.png")
        print("wrote", size, "any / maskable")

    # iOS applies its own mask and ignores alpha, so this one is flattened
    render(MASTER_LIGHT, 180, opaque=True).save(f"{OUT}/apple-touch-icon.png")
    print("wrote apple-touch-icon.png 180")

    for size in (32, 16):
        render(MASTER_LIGHT, size).save(f"{OUT}/favicon-{size}.png")
        render(MASTER_DARK, size).save(f"{OUT}/favicon-{size}-dark.png")
        print("wrote favicon", size, "light / dark")

    sizes = (48, 32, 16)
    blobs = []
    for s in sizes:
        buf = io.BytesIO()
        render(MASTER_LIGHT, s).save(buf, "PNG")
        blobs.append(buf.getvalue())
    ico(blobs, sizes, "favicon.ico")


if __name__ == "__main__":
    main()
