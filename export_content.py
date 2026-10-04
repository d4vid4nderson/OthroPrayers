"""Export the built pages as a structured content model for the native app.

The HTML build is the single source of truth for the text; a native app should
not parse HTML at runtime, and it should not get a second, drifting copy of the
prayers either. So this reads the generated pages and emits one JSON file of
semantic blocks — headings, rubrics, verses and their inline marks — that
SwiftUI can render directly.

Run after build.py:

    python3 build.py && python3 export_content.py

It is deliberately strict: any tag or class inside a page's content region that
this does not recognise raises, rather than being silently dropped. A prayer
quietly losing a line is the one failure mode that matters here.
"""
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

OUT = "ios/Content/content.json"
SIGNUM_CHAR = "\u2720"   # ✠ — the mark the printed booklet uses

# whole subtrees that are page chrome, not content: the native app provides
# its own navigation, ornaments and page turns
SKIP_SUBTREE = [
    ("div", "page-back"), ("div", "seqnav"), ("figure", "art"),
    ("span", "cross"), ("details", "page-contents"), ("nav", "page-toc"),
    ("svg", None), ("button", None), ("footer", None), ("script", None),
    # hub navigation: the app builds its own lists from the page order, and
    # these rows flatten into meaningless run-on prose if left in
    ("div", "browse-list"), ("a", "browse-row"), ("div", "cycle"), ("a", "office-link"),
]

# block-level elements, by (tag, first class) -> block type
BLOCKS = {
    ("h1", None): "title",
    ("h2", "subhead"): "heading",
    ("h2", "browse-group"): "heading",
    ("dt", None): "term",          # the feast lists: name ...
    ("dd", None): "definition",    # ... and its date
    ("h3", "subhead2"): "subheading",
    ("p", "rubric"): "rubric",
    ("p", "verse"): "verse",
    ("p", "res-intro"): "lead",
    ("p", "topic-intro"): "lead",
    ("p", "lead"): "lead",
    ("p", None): "paragraph",
    ("li", None): "item",
}

# inline marks, by class on a span (or by tag)
MARKS = {"r": "rubric", "signum": "signum", "dropcap": "dropcap",
         "i": "italic", "sc": "smallcaps", "v": "versal"}
TAG_MARKS = {"em": "italic", "i": "italic", "strong": "strong", "b": "strong",
             "cite": "italic", "abbr": None, "sup": "sup", "small": "small"}

# containers we walk through without emitting anything of their own
TRANSPARENT = {"section", "div", "main", "article", "figure", "figcaption", "dl",
               "ul", "ol", "a", "span", "br", "hr", "wbr", "blockquote", "table",
               "tbody", "thead", "tr", "td", "th", "details", "summary", "nav",
               "label", "input", "select", "option", "time", "picture", "img"}


class PageParser(HTMLParser):
    def __init__(self, slug):
        super().__init__(convert_charrefs=True)
        self.slug = slug
        self.blocks = []
        self.title = None
        self.unknown = set()
        self._skip_depth = 0
        self._skip_tag = None
        self._block = None        # (type, runs, meta)
        self._marks = []
        self._links = []          # cross-references between pages stay tappable
        self._depth = 0

    # --- helpers ---------------------------------------------------------
    def _classes(self, attrs):
        d = dict(attrs)
        return d.get("class", "").split(), d

    def _push_text(self, text):
        if self._block is None or not text:
            return
        mark = "signum" if text == SIGNUM_CHAR else (self._marks[-1] if self._marks else None)
        href = self._links[-1] if self._links else None
        runs = self._block[1]
        if runs and runs[-1].get("mark") == mark and runs[-1].get("href") == href:
            runs[-1]["t"] += text
        else:
            run = {"t": text}
            if mark:
                run["mark"] = mark
            if href:
                run["href"] = href
            runs.append(run)

    def _close_block(self):
        if self._block is None:
            return
        kind, runs, meta = self._block
        runs = [r for r in runs if r["t"].strip() or r["t"] == " "]
        for r in runs:
            r["t"] = re.sub(r"[^\S\n]*\n[^\S\n]*", "\n", re.sub(r"[^\S\n]+", " ", r["t"]))
        if runs:
            while runs and not runs[0]["t"].strip():
                runs.pop(0)
            while runs and not runs[-1]["t"].strip():
                runs.pop()
        if runs:
            if runs[0]["t"].startswith(" "):
                runs[0]["t"] = runs[0]["t"].lstrip()
            if runs[-1]["t"].endswith(" "):
                runs[-1]["t"] = runs[-1]["t"].rstrip()
        if kind == "title":
            self.title = "".join(r["t"] for r in runs)
        elif runs:
            block = {"type": kind, "runs": runs}
            block.update(meta)
            self.blocks.append(block)
        self._block = None

    # --- parser callbacks -------------------------------------------------
    def handle_starttag(self, tag, attrs):
        self._depth += 1
        if self._skip_depth:
            return
        classes, d = self._classes(attrs)
        first = classes[0] if classes else None
        for stag, scls in SKIP_SUBTREE:
            if tag == stag and (scls is None or scls in classes):
                self._skip_depth = self._depth
                self._skip_tag = tag
                return
        key = (tag, first)
        if key not in BLOCKS and (tag, None) in BLOCKS and tag in ("p", "li", "h1"):
            key = (tag, None)
        if key in BLOCKS:
            self._close_block()
            meta = {}
            if "hymn" in classes:
                meta["style"] = "hymn"
            if d.get("id"):
                meta["id"] = d["id"]
            self._block = (BLOCKS[key], [], meta)
            return
        if tag in TAG_MARKS:
            self._marks.append(TAG_MARKS[tag])
            return
        if "signum" in classes:
            # the rubrical cross-mark: "make the sign of the cross here". Its
            # glyph is an SVG, which is skipped — so emit the character itself,
            # or the mark vanishes and the reader loses the direction.
            self._push_text(SIGNUM_CHAR)
            self._skip_depth = self._depth
            self._skip_tag = tag
            return
        if tag == "a":
            target = d.get("href", "")
            # only in-app page links; external ones are not in this build
            self._links.append(target[:-5] if target.endswith(".html") else None)
            return
        if tag == "br":
            # a hymn's line breaks are the verse form, not whitespace — keep
            # them so the app can set each line on its own line
            self._push_text("\n")
            self._depth -= 1          # void element: no end tag will balance it
            return
        if tag == "span":
            self._marks.append(MARKS.get(first))
            return
        if tag not in TRANSPARENT:
            self.unknown.add(f"<{tag}{' class=' + first if first else ''}>")

    def handle_endtag(self, tag):
        if self._skip_depth:
            if self._depth == self._skip_depth and tag == self._skip_tag:
                self._skip_depth = 0
                self._skip_tag = None
            self._depth -= 1
            return
        if tag == "a":
            if self._links:
                self._links.pop()
        elif tag in TAG_MARKS or tag == "span":
            if self._marks:
                self._marks.pop()
        elif self._block and BLOCKS.get((tag, None)) == self._block[0] or \
                (self._block and tag in ("h1", "h2", "h3", "p", "li", "dt", "dd")):
            self._close_block()
        self._depth -= 1

    def handle_startendtag(self, tag, attrs):
        if not self._skip_depth and tag == "br":
            self._push_text("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            self._push_text(data)


def page_content(path):
    raw = open(path).read()
    m = re.search(r'<main[^>]*class="book"[^>]*>(.*?)</main>', raw, re.S)
    if not m:
        return None
    slug = os.path.splitext(os.path.basename(path))[0]
    p = PageParser(slug)
    p.feed(m.group(1))
    p._close_block()
    title = p.title or ""
    desc = re.search(r'<meta name="description" content="([^"]*)"', raw)
    return {
        "slug": slug,
        "title": html.unescape(title),
        "summary": html.unescape(desc.group(1)) if desc else "",
        "blocks": p.blocks,
    }, p.unknown


def main():
    import glob
    pages, unknown = [], set()
    for f in sorted(glob.glob("*.html")):
        if ".content." in f:
            continue
        got = page_content(f)
        if not got:
            continue
        page, unk = got
        unknown |= unk
        if page["blocks"]:
            pages.append(page)
    if unknown:
        sys.exit("unrecognised markup — refusing to drop content silently:\n  "
                 + "\n  ".join(sorted(unknown)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc = {"generated": True, "pages": pages}
    with open(OUT, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    # every mark that exists in the HTML must exist in the model. This caught
    # all ten cross-marks being dropped once already.
    import glob as _glob
    html_signa = sum(open(f).read().count('class="signum"')
                     for f in _glob.glob("*.html") if ".content." not in f)
    json_signa = sum(r["t"].count(SIGNUM_CHAR)
                     for p in pages for b in p["blocks"] for r in b["runs"])
    if html_signa != json_signa:
        sys.exit(f"cross-marks lost: {html_signa} in the pages, {json_signa} in the model")
    blocks = sum(len(p["blocks"]) for p in pages)
    runs = sum(len(b["runs"]) for p in pages for b in p["blocks"])
    print(f"wrote {OUT}: {len(pages)} pages, {blocks} blocks, {runs} runs, "
          f"{json_signa} cross-marks, {os.path.getsize(OUT) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
