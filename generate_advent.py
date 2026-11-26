#!/usr/bin/env python3
"""Generate the Advent booklet's content from its source PDF.

    python3 generate_advent.py            # advent-source.pdf -> advent.content.html

"Lay Devotions for the Season of Advent" arrives as a saddle-stitched booklet
imposed two pages to a sheet, each page in two columns — so the PDF's page 2
holds booklet pages 2 and 31 side by side, and nothing in it reads in order.
This puts it back together and emits the markup build.py already speaks.

It reads the PDF through `pdftohtml -xml`, which gives each run of text its
position, size, face and colour. Colour is what carries the structure here:
the booklet prints its directions, citations and headings in red and the
prayers in black, so the rubrics can be recovered exactly rather than guessed
at from wording.

The awkward parts, each of which was a wrong transcription first:

  * The sheet's two booklet pages are read as separate pages, and lines are
    grouped within a column. Grouping by vertical position alone welds a line
    of page 2 to the line of page 31 beside it.
  * A page is not always one run of two columns. Where a full-width head rules
    across it — OPENING PRAYERS, DAILY READINGS — the columns below are a
    fresh pair, and reading the left column straight down walks out of the
    prayers and into the readings.
  * The folios are old-style figures in a private-use block, which is how the
    imposition is checked rather than assumed.
  * The face puts the Th ligature on "!", '"' and "+". It is only a ligature
    where a letter follows: "Rejoice!" is an exclamation mark.
  * Spacing is decided from geometry, because a drop cap's box overlaps the
    small-caps remainder of its own word ("O" + "ur" + "Father,") while
    standing clear of a separate one ("O" + "Lord,").

Needs `pdftohtml` (poppler-utils). Nothing else.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SRC = os.environ.get("ADVENT_PDF", "advent-source.pdf")
OUT = os.environ.get("ADVENT_OUT", "advent.content.html")
ART = os.environ.get("ADVENT_ART", "ios/App/Resources/Art")

S = 1.5                      # px per pt: the XML is 1188px wide for 792pt
COLS = [206 * S, 396 * S, 587 * S, 1e9]          # column right edges
COLX = [(43 * S, 201 * S), (210 * S, 367 * S),
        (425 * S, 582 * S), (591 * S, 749 * S)]  # column left/right margins
RED = "#c00000"

FIG = {chr(0xF643 + i): str(i) for i in range(10)}   # old-style figures 0-9
LIG = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl",
       "ﬃ": "ffi", "ﬄ": "ffl"}

# The illuminated capitals are glyphs of an embedded ornamental face, and the
# woodcut at the end is the booklet's one raster image.
ARABESQUE = "ArabesqueInitialen"
BANNER = "adv-nativitas"

SPAN_HEAD = re.compile(r'^(OPENI\s*NG|CONCLUDI\s*NG|DAILY READINGS)')
NOISE = re.compile(r'^(Lay Devotions for the Season of Advent|OPENI\s*NG PRAYERS'
                   r'|CONCLUDI\s*NG PRAYERS|DAILY READINGS|\d{1,2})$')
DATE = re.compile(r'^(November|December) \d{1,2}$')
CITE = re.compile(r'^(?:[123] )?[A-Z][a-z]+ \d+:[\d–,\s]+$')
REFL = re.compile(r'^(A )?[Rr]eflection from St\.'
                  r'|^From the St\. Andrew Daily Missal$')
HYMN = re.compile(r'^Hymn [IV]+:')
STANZA = re.compile(r'^(?:[ivx]+\.|\[doxology\])$', re.I)
MONTH = {"November": "nov", "December": "dec"}


# ---- the PDF, as positioned runs -------------------------------------------

def read_runs(path):
    xml = subprocess.run(["pdftohtml", "-xml", "-i", "-stdout", path],
                         capture_output=True, text=True, check=True).stdout
    fonts = {int(i): (int(sz), fam, col) for i, sz, fam, col in re.findall(
        r'<fontspec id="(\d+)" size="(\d+)" family="([^"]+)" color="([^"]+)"/>',
        xml)}
    pages = []
    for body in re.findall(r'<page number="\d+"[^>]*>(.*?)</page>', xml, re.S):
        runs = []
        for top, left, w, _h, f, txt in re.findall(
                r'<text top="(-?\d+)" left="(-?\d+)" width="(-?\d+)" '
                r'height="(-?\d+)" font="(\d+)">(.*?)</text>', body, re.S):
            t = html.unescape(re.sub(r"<[^>]+>", "", txt))
            if not t.strip():
                continue
            size, fam, col = fonts[int(f)]
            runs.append({"top": int(top), "left": int(left), "w": int(w),
                         "h": int(_h), "t": t, "size": size, "fam": fam,
                         "red": col == RED, "page": len(pages) + 1})
        pages.append(runs)
    return pages


def glyphs(t):
    for k, v in FIG.items():
        t = t.replace(k, v)
    for k, v in LIG.items():
        t = t.replace(k, v)
    # The Th ligature sits on these three, but only where a letter follows:
    # "Rejoice!" is an exclamation mark, and replacing it wholesale turned the
    # refrain into "RejoiceTh RejoiceTh".
    return re.sub(r'[!"+](?=[A-Za-z])', "Th", t)


def col_of(x):
    return next(i for i, b in enumerate(COLS) if x < b)


# ---- runs into lines -------------------------------------------------------

def line_of(L):
    """One line's text and its red segments, spaced from the geometry."""
    L.sort(key=lambda r: r["left"])
    parts, flags = [], []
    for i, r in enumerate(L):
        lig = r["t"].strip() in ("!", '"', "+")
        t = "Th" if lig else (r["t"].rstrip() if r["size"] >= 40 else r["t"])
        if i:
            prev = L[i - 1]
            gap = r["left"] - (prev["left"] + prev["w"])
            tail = parts[-1]
            # Not `lig` itself: a ligature glues to what FOLLOWS it (the
            # endswith below), but a real space can precede it — without this
            # "2 Thessalonians" lost its space and the whole day mis-parsed.
            glue = (
                # a drop cap's box overlaps the rest of its own word, and
                # stands clear of a separate one, so the gap decides
                (prev["size"] >= 40 and gap < 2)
                # a superscript ordinal belongs to its number
                or (t.strip() in ("th", "st", "nd", "rd")
                    and r["size"] < prev["size"])
                or tail.rstrip().endswith(("Th", "(", "‘", "–", "—"))
                or t.lstrip()[:1] in ",.;:!?)]’–—")
            # Some lines are set tight enough that a word space is a 1px gap.
            # At that width a mid-word change of face looks the same — the
            # middle e of "every" is set in another subset — so a 1px gap is
            # only a space when the face does not change across it.
            if not (tail.endswith(" ") or t.startswith(" ")) and not glue \
                    and (gap >= 2 or (gap >= 1 and r["fam"] == prev["fam"])):
                parts.append(" ")
                flags.append(r["red"])
        parts.append(t)
        flags.append(r["red"])

    segs = []
    for piece, red in zip(parts, flags):
        piece = glyphs(piece)
        if segs and segs[-1]["red"] == red:
            segs[-1]["t"] += piece
        else:
            segs.append({"t": piece, "red": red})
    for sg in segs:
        sg["t"] = re.sub(r"\s+", " ", sg["t"])
    segs = [sg for sg in segs if sg["t"].strip()]
    txt = re.sub(r"\s+", " ", "".join(sg["t"] for sg in segs)).strip()

    # The decorative initials come from a display face whose letters arrive
    # lowercase, so "For with the heart" read as "for with the heart".
    if txt[:1].islower() and any(r["size"] >= 40 for r in L):
        txt = txt[0].upper() + txt[1:]
        for sg in segs:
            if sg["t"].strip():
                first = sg["t"].strip()[0]
                sg["t"] = sg["t"].replace(first, first.upper(), 1)
                break
    return txt, segs


# Which ornament a glyph code draws. The face carries alternates: the
# lowercase codes are second designs for the same letters, so "a" draws
# another A and "f" draws an F. Keyed so two designs of one letter cannot
# collide on a case-insensitive filesystem.
_ART_UPPER = set("AHINOTWY")

def art_key(code):
    c = code.strip()
    if not c:
        return None
    return c if c.isupper() else (c.upper() + "2" if c.upper() in _ART_UPPER
                                  else c.upper())


def folio(lines):
    """The printed page number: the bottom-most line that is just a numeral."""
    for l in sorted(lines, key=lambda l: -l["top"]):
        if re.fullmatch(r"\d{1,2}", l["t"].strip()):
            return int(l["t"].strip())
    return None


def booklet_pages(sheets):
    """The sheets unpicked into booklet pages, in reading order."""
    out = {}
    for n, runs in enumerate(sheets, 1):
        grouped = []
        for c in range(4):
            col = sorted((r for r in runs if col_of(r["left"]) == c),
                         key=lambda r: (r["top"], r["left"]))
            cur = []
            for r in col:
                if cur and abs(r["top"] - cur[0]["top"]) > 5:
                    grouped.append(cur)
                    cur = []
                cur.append(r)
            if cur:
                grouped.append(cur)

        built = []
        for L in grouped:
            txt, segs = line_of(L)
            if not txt:
                continue
            art = next((art_key(r["t"]) for r in L
                        if ARABESQUE in r["fam"] and r["red"] and r["t"].strip()),
                       None)
            built.append({"t": txt, "segs": segs, "top": L[0]["top"],
                          "col": col_of(min(r["left"] for r in L)),
                          "dc": any(r["size"] >= 40 for r in L), "art": art})

        for half, cols in ((0, (0, 1)), (1, (2, 3))):
            sel = [l for l in built if l["col"] in cols]
            if not sel:
                continue
            # Banded per booklet page, not per sheet: the two pages share a
            # sheet, and page 31's CONCLUDING PRAYERS was cutting page 2 in
            # half and stranding the Hail Mary.
            heads = sorted(l["top"] for l in sel if SPAN_HEAD.match(l["t"]))
            for l in sel:
                l["band"] = sum(1 for h in heads if l["top"] >= h - 2)
            sel.sort(key=lambda l: (l["band"], l["col"], l["top"]))
            out[folio(sel) if folio(sel) is not None else f"sheet{n}h{half}"] = sel
    return out


# ---- lines into blocks -----------------------------------------------------

def blocks(lines):
    """Lines into paragraphs, keeping inline rubric marks inside them.

    A paragraph breaks where a whole line turns red (a direction standing on
    its own) or where a decorative initial begins a new one. A red phrase
    *within* a line stays put: "(here mention your request)" is an instruction
    inside the St Andrew Prayer, not a paragraph of its own.
    """
    groups, cur = [], None
    for l in lines:
        red = bool(l["segs"]) and all(sg["red"] for sg in l["segs"])
        if cur is None or red != cur["red"] or l.get("dc"):
            if cur:
                groups.append(cur)
            cur = {"red": red, "segs": []}
        for n, sg in enumerate(l["segs"]):
            # Only at a line boundary. Segments within one line already carry
            # the spacing the page gave them, and inserting more put a gap
            # inside the decorative initials: "H ail", "A men."
            if cur["segs"] and n == 0:
                tail = cur["segs"][-1]
                if tail["t"].rstrip().endswith("-"):
                    tail["t"] = tail["t"].rstrip()[:-1]   # word split by a line
                elif not tail["t"].endswith(" ") and not sg["t"].startswith(" "):
                    tail["t"] += " "
            if cur["segs"] and cur["segs"][-1]["red"] == sg["red"]:
                cur["segs"][-1]["t"] += sg["t"]
            else:
                cur["segs"].append(dict(sg))
        if cur:
            cur["dc"] = cur.get("dc") or l.get("dc")
            cur["art"] = cur.get("art") or l.get("art")
    if cur:
        groups.append(cur)

    out = []
    for g in groups:
        segs = [{"t": re.sub(r"\s+", " ", sg["t"]), "red": sg["red"]}
                for sg in g["segs"] if sg["t"].strip()]
        if not segs:
            continue
        segs[0]["t"] = segs[0]["t"].lstrip()
        segs[-1]["t"] = segs[-1]["t"].rstrip()
        out.append({"kind": "rubric" if g["red"] else "para", "segs": segs,
                    "art": g.get("art")})
    return out


def parse(pages):
    """The booklet's three regions: the opening, the days, the conclusion."""
    # From page 2: page 1 is the cover, which is the booklet's title set
    # large and belongs on no page of the app.
    lines = [l for key in range(2, 33) if key in pages
             for l in pages[key] if not NOISE.match(l["t"].strip())]

    i_first = next(i for i, l in enumerate(lines) if DATE.match(l["t"].strip()))
    i_close = next(i for i, l in enumerate(lines)
                   if l["t"].strip().startswith("After the readings appointed"))
    opening, body, closing = lines[:i_first], lines[i_first:i_close], lines[i_close:]

    days, cur, part = [], None, None
    for l in body:
        t = l["t"].strip()
        if DATE.match(t):
            if cur:
                days.append(cur)
            cur = {"date": t, "feast": [], "cite": None, "attrib": None,
                   "scripture": [], "reflection": [], "antiphon": [], "collect": []}
            part = "feast"
        elif cur is None:
            continue
        elif CITE.match(t) and cur["cite"] is None:
            cur["cite"] = t
            part = "scripture"
        elif REFL.match(t):
            cur["attrib"] = t
            part = "reflection"
        elif t in ("Antiphon", "Collect"):
            part = t.lower()
        else:
            cur[part].append(l)
    if cur:
        days.append(cur)
    for d in days:
        d["feast"] = " ".join(l["t"].strip() for l in d["feast"]) or None
        for k in ("scripture", "reflection", "antiphon", "collect"):
            d[k] = blocks(d[k])

    close, stanza, in_hymn = [], None, False
    for l in closing:
        t = l["t"].strip()
        if HYMN.match(t) or t == "The Saint Andrew Prayer":
            if stanza:
                close.append(stanza)
                stanza = None
            in_hymn = HYMN.match(t) is not None
            close.append({"kind": "hymn", "text": t})
        elif STANZA.match(t) and in_hymn:
            if stanza:
                close.append(stanza)
            stanza = {"kind": "verse", "label": t, "lines": []}
        elif stanza is not None:
            stanza["lines"].append(t)
        else:
            close.append({"kind": "line", "line": l})
    if stanza:
        close.append(stanza)

    folded, buf = [], []
    for b in close:
        if b["kind"] == "line":
            buf.append(b["line"])
        else:
            if buf:
                folded += blocks(buf)
                buf = []
            folded.append(b)
    if buf:
        folded += blocks(buf)
    return {"opening": blocks(opening), "days": days, "closing": folded}


# ---- blocks into the markup build.py reads ---------------------------------

def esc(t):
    return (html.escape(t, quote=False)
            .replace("’", "&rsquo;").replace("‘", "&lsquo;")
            .replace("–", "&ndash;").replace("—", "&mdash;")
            .replace("…", "&hellip;"))


def inline(segs):
    """Segments to markup: a lone red letter is an initial, red prose a rubric."""
    out = []
    for i, sg in enumerate(segs):
        t = sg["t"]
        if not sg["red"]:
            out.append(esc(t))
            continue
        bare = t.strip()
        if len(bare) == 1 and bare.isalpha():
            cls = "dropcap" if i == 0 else "versal"
            out.append(f'<span class="{cls}">{esc(bare)}</span>')
            if t.endswith(" "):
                out.append(" ")
        else:
            lead = " " if t.startswith(" ") else ""
            tail = " " if t.endswith(" ") else ""
            out.append(f'{lead}<span class="r">{esc(bare)}</span>{tail}')
    return "".join(out).strip()


# The booklet sets the versicle and response marks in red in the opening
# prayers and in black in the concluding ones. They are the same thing either
# way, so this matches the pattern rather than the colour.
_VR = r'(?:<span class="r">%s\.</span>|%s\.)'
CUE = re.compile(r'^\s*' + (_VR % ("V", "V")) + r'\s*(.*?)\s*'
                 + (_VR % ("R", "R")) + r'\s*(.*)$', re.S)


def render(bs):
    out = []
    for b in bs:
        s = inline(b["segs"])
        if b.get("art"):
            # The illuminated capital set into the paragraph it opens, as the
            # booklet sets it: the ornament *is* the first letter, so that
            # letter leaves the text and the opening lines are laid around the
            # ornament rather than beneath it. The image carries the letter in
            # its alt text, so nothing is lost to a reader who cannot see it.
            letter = b["art"].rstrip("2")
            s = re.sub(r'^<span class="dropcap">.</span>', "", s)
            out.append(f'<p><img src="adv-initial-{b["art"]}.png" '
                       f'alt="Illuminated {letter}">{s}</p>')
            continue
        if b["kind"] == "rubric":
            if not (s.startswith('<span class="r">') and s.endswith("</span>")):
                s = f'<span class="r">{s}</span>'
            out.append(f'<p class="rubric">{s}</p>')
            continue
        m = CUE.match(s)
        if m:
            out.append(f'<p class="svc-cue"><span class="r">V.</span> {m.group(1)}</p>')
            out.append(f'<p class="svc-say"><span class="r">R.</span> {m.group(2)}</p>')
        else:
            out.append(f"<p>{s}</p>")
    return out


def section(slug, title, parts):
    return (f'<section class="divider advent" id="{slug}">'
            f'<span class="cross">✠</span><h1>{esc(title)}</h1></section>\n'
            + "\n".join(parts))


def write_art(sheets):
    """Lift the booklet's ornaments out as alpha masks.

    Masks, not pictures: the initials are printed in one red, and the app has
    five themes to draw them in. Keeping only the ink's coverage lets each
    one be filled with whatever the theme's accent is, the same trick the
    rest of this project's ornaments use.

    Needs Pillow and pdftoppm. Without them the committed art is kept, which
    matters because this runs from a checkout that may have neither.
    """
    try:
        from PIL import Image, ImageChops, ImageOps
    except ImportError:
        print("Pillow not available \u2014 keeping the committed artwork")
        return
    if not shutil.which("pdftoppm"):
        print("pdftoppm not available \u2014 keeping the committed artwork")
        return
    os.makedirs(ART, exist_ok=True)

    def to_mask(im, side=None):
        im = im.convert("RGB")
        r, g, b = im.split()
        mn = ImageChops.darker(ImageChops.darker(r, g), b)   # per-pixel minimum
        alpha = ImageOps.autocontrast(ImageChops.invert(mn))  # ink -> coverage
        out = Image.new("RGBA", im.size, (0, 0, 0, 0))
        out.putalpha(alpha)
        return out.resize(side, Image.LANCZOS) if side else out

    # one crop per distinct ornament, at 400dpi
    DPI, want = 400, {}
    for runs in sheets:
        for r in runs:
            k = art_key(r["t"]) if ARABESQUE in r["fam"] and r["red"] else None
            if k and k not in want:
                want[k] = r
    scale = DPI / 72 / S
    with tempfile.TemporaryDirectory() as tmp:
        rendered = {}
        for k, r in sorted(want.items()):
            pg = r["page"]
            if pg not in rendered:
                base = os.path.join(tmp, f"p{pg}")
                subprocess.run(["pdftoppm", "-f", str(pg), "-l", str(pg), "-r",
                                str(DPI), "-png", "-singlefile", SRC, base],
                               check=True)
                rendered[pg] = Image.open(base + ".png")
            im = rendered[pg]
            box = (round(r["left"] * scale), round(r["top"] * scale),
                   round((r["left"] + r["w"]) * scale),
                   round((r["top"] + r["h"]) * scale))
            to_mask(im.crop(box), (256, 256)).save(
                os.path.join(ART, f"adv-initial-{k}.png"))

        # the one raster image in the booklet: the Nativity woodcut
        if shutil.which("pdfimages"):
            base = os.path.join(tmp, "img")
            subprocess.run(["pdfimages", "-png", "-f", "1", "-l", "1", SRC, base],
                           check=True)
            found = sorted(f for f in os.listdir(tmp) if f.startswith("img"))
            if found:
                im = Image.open(os.path.join(tmp, found[0]))
                to_mask(im).save(os.path.join(ART, f"{BANNER}.png"))
    print(f"wrote {len(want)} initials and the woodcut to {ART}/")


def main():
    if not os.path.exists(SRC):
        sys.exit(f"{SRC} not found")
    sheets = read_runs(SRC)
    write_art(sheets)
    model = parse(booklet_pages(sheets))
    if len(model["days"]) != 28:
        sys.exit(f"expected 28 days, parsed {len(model['days'])}")

    out = [section("adv-opening", "Opening Prayers", render(model["opening"]))]
    for d in model["days"]:
        mon, day = d["date"].split()
        parts = []
        if d["feast"]:
            parts.append(f'<h3 class="subhead2">{esc(d["feast"])}</h3>')
        parts.append(f'<p class="rubric"><span class="r">{esc(d["cite"])}</span></p>')
        parts += render(d["scripture"])
        if d["attrib"]:
            parts.append(f'<h2 class="subhead">{esc(d["attrib"])}</h2>')
        parts += render(d["reflection"])
        for name in ("antiphon", "collect"):
            if d[name]:
                parts.append(f'<h2 class="subhead">{name.capitalize()}</h2>')
                parts += render(d[name])
        out.append(section(f"adv-{MONTH[mon]}-{int(day)}", d["date"], parts))

    parts = []
    for b in model["closing"]:
        if b["kind"] == "hymn":
            parts.append(f'<h2 class="subhead">{esc(b["text"])}</h2>')
        elif b["kind"] == "verse":
            parts.append(f'<p class="rubric"><span class="r">{esc(b["label"])}</span></p>')
            parts.append('<p class="verse">'
                         + "<br>".join(esc(x) for x in b["lines"]) + "</p>")
        else:
            parts += render([b])
    parts.append(f'<p class="art"><img src="{BANNER}.png" '
                 'alt="Woodcut of angels bearing a banner, Nativitas Domini"></p>')
    out.append(section("adv-closing", "Concluding Prayers", parts))

    with open(OUT, "w") as f:
        f.write("\n\n".join(out) + "\n")
    print(f"wrote {OUT}: {len(out)} sections, {len(model['days'])} days "
          f"({model['days'][0]['date']} – {model['days'][-1]['date']})")


if __name__ == "__main__":
    main()
