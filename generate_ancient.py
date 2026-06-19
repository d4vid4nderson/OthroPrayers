#!/usr/bin/env python3
"""Convert the Ancient Faith Prayer Book EPUB into ancient.content.html, in the
same HTML idiom build.py already uses for the St. Tikhon's booklet (rubrics,
sub-heads, drop caps, verses). The EPUB is a build input the user supplies and
has permission to use; it is not committed or deployed (only the rendered
prayer fragments are). Point AFPB_EPUB at the .epub and run this, then build.py.

Usage:  AFPB_EPUB=/path/to/book.epub python3 generate_ancient.py
"""

import html
import os
import re
import zipfile

EPUB = os.environ.get(
    "AFPB_EPUB",
    "/tmp/claude-0/-home-user-OthroPrayers/d1c1668a-c13f-57a2-8512-ce1cd7b8fcb7/"
    "scratchpad/epub/book.epub")

# (slug, source file, divider title) — the daily cycle then the sacramental /
# occasional offices
SECTIONS = [
    ("af-morning",      "morning.xhtml",          "Morning Prayers"),
    ("af-midday",       "afternoon.xhtml",        "Midday Prayers"),
    ("af-meals",        "mealtime.xhtml",         "Prayers at Meals"),
    ("af-evening",      "evening.xhtml",          "Evening Prayers"),
    ("af-night",        "late_eve.xhtml",         "Prayers at the Close of Day"),
    ("af-precommunion", "before-communion.xhtml", "Preparation for Holy Communion"),
    ("af-communion",    "communion.xhtml",        "Holy Communion"),
    ("af-thanksgiving", "thanks_communion.xhtml", "Thanksgiving After Communion"),
    ("af-confession",   "confession.xhtml",       "Before Confession"),
    ("af-departed",     "departed.xhtml",         "Prayers for the Departed"),
    ("af-occasions",    "occasions.xhtml",        "Prayers for Various Occasions"),
    ("af-saints",       "saints.xhtml",           "Prayers to the Saints"),
]


def _inline(s):
    """Reduce the publisher's inline markup to the app's small set."""
    # footnote markers / cross-refs
    s = re.sub(r'<sup\b[^>]*>.*?</sup>', '', s, flags=re.S)
    s = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', s, flags=re.S)
    # drop cap (first letter) — keep as the app's .dropcap span
    s = re.sub(r'<span[^>]*class="(?:dropcap|Initial-Cap|prayer-initial)"[^>]*>\s*(.)[^<]*</span>',
               r'<span class="dropcap">\1</span>', s)
    # the styled first words -> small caps run (the app pairs dropcap + .sc)
    s = re.sub(r'<span[^>]*class="prayer-firstline"[^>]*>(.*?)</span>',
               r'<span class="sc">\1</span>', s, flags=re.S)
    # no gap between the drop cap and the small-caps run
    s = re.sub(r'(</span>)\s+(<span class="sc">)', r'\1\2', s)
    # italics / emphasis kept; everything else unwrapped
    s = re.sub(r'<(?:i|em)\b[^>]*>', '<em>', s)
    s = re.sub(r'</(?:i|em)>', '</em>', s)
    s = re.sub(r'<(?:b|strong)\b[^>]*>', '<strong>', s)
    s = re.sub(r'</(?:b|strong)>', '</strong>', s)
    s = re.sub(r'<br\b[^>]*>', '<br>', s)
    # strip any other tag (leftover spans, etc.) but keep our kept ones
    s = re.sub(r'</?(?!span|em|strong|br\b)[a-zA-Z][^>]*>', '', s)
    # leftover spans that aren't dropcap/sc -> unwrap
    s = re.sub(r'<span(?![^>]*class="(?:dropcap|sc)")[^>]*>', '', s)
    s = re.sub(r'<span class="(dropcap|sc)">', lambda m: f'<span class="{m.group(1)}">', s)
    s = s.replace('</span>', '</span>')  # keep
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _text(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()


def convert(raw):
    body = re.search(r'<body[^>]*>(.*)</body>', raw, re.S)
    body = body.group(1) if body else raw
    # unwrap structural containers so the block scan sees the leaf paragraphs
    body = re.sub(r'</?(?:div|blockquote|section|article)\b[^>]*>', '', body)

    out, title = [], None
    for m in re.finditer(r'<(h1|h2|h3|h4|p)\b([^>]*)>(.*?)</\1>', body, re.S):
        tag, attr, inner = m.group(1), m.group(2), m.group(3)
        cls = (re.search(r'class="([^"]*)"', attr) or [None, ""])[1].lower()
        txt = _text(inner)
        if not txt:
            continue
        if tag == "h1" and title is None:
            title = txt
            continue
        if tag in ("h1", "h2"):
            out.append(f'<h2 class="subhead">{_inline(inner)}</h2>')
        elif tag in ("h3", "h4") or "prayer-title" in cls:
            out.append(f'<h3 class="subhead minor">{_inline(inner)}</h3>')
        elif "rubric" in cls or "red" in cls:
            out.append(f'<p class="rubric">{_inline(inner)}</p>')
        elif "psalm" in cls:
            out.append(f'<p class="psalm">{_inline(inner)}</p>')
        elif cls.strip() == "amen" or txt.upper().rstrip(".") == "AMEN":
            out.append('<p class="amen">Amen.</p>')
        else:
            out.append(f'<p>{_inline(inner)}</p>')
    return title, "\n".join(out)


def main():
    pieces = []
    with zipfile.ZipFile(EPUB) as z:
        names = {os.path.basename(n): n for n in z.namelist()}
        for slug, fname, deftitle in SECTIONS:
            if fname not in names:
                print("!! missing", fname)
                continue
            raw = z.read(names[fname]).decode("utf-8", "replace")
            title, content = convert(raw)
            title = title or deftitle
            # normalise the publisher's ALL-CAPS h1 to title case for the divider
            disp = deftitle
            pieces.append(
                f'<section class="divider afpb" id="{slug}">'
                f'<span class="cross">✠</span><h1>{html.escape(disp)}</h1></section>\n'
                + content)
            print(f"  {slug:16} {len(content):6d} bytes  ({_text(content).count('.')} sentences)")
    open("ancient.content.html", "w").write("\n\n".join(pieces))
    print("wrote ancient.content.html")


if __name__ == "__main__":
    main()
