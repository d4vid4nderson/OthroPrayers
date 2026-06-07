#!/usr/bin/env python3
"""Generate the web version of "Prayers for Morning, Day & Night" directly from
the source PDF, deriving every bit of structure and styling from the document.

Output: prayers.content.html  (a fragment inserted into index.html by build.py)
"""
import fitz, re, html

doc = fitz.open("source.pdf")
LEFT_MARGIN = 32.0
INDENT_X    = 40.0     # first-line indent => new paragraph
TOP_DROP    = 26.0     # above this y: running headers
BOT_DROP    = 388.0    # below this y: folios / footers
PAGE_CX     = 153.0    # horizontal centre of the page


def is_red(c):
    r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    return r > 150 and g < 140 and b < 140 and (r - g) > 40


def span_role(font):
    base = font.split("+")[-1]
    if "Display" in base:    return "dropcap"
    if base == "liturgy":    return "response"
    if "Hirmos" in base:     return "cross"
    if "Sava" in base:       return "bullet"
    return "text"


def line_obj(l):
    spans = []
    for s in l["spans"]:
        t = s["text"].replace("­", "")   # mark soft-hyphens, strip later
        if t == "":
            continue
        spans.append({
            "t": t,
            "role": span_role(s["font"]),
            "italic": "Italic" in s["font"],
            "sm": "SmText" in s["font"],          # optical small-caps run
            "red": is_red(s["color"]),
            "size": round(s["size"], 1),
        })
    text = "".join(s["t"] for s in spans)
    nonspace = [s for s in spans if s["t"].strip()]
    return {
        "y": round(l["bbox"][1], 1),
        "x0": round(l["bbox"][0], 1),
        "x1": round(l["bbox"][2], 1),
        "cx": round((l["bbox"][0] + l["bbox"][2]) / 2, 1),
        "w": round(l["bbox"][2] - l["bbox"][0], 1),
        "spans": spans,
        "text": text,
        "maxsize": max((s["size"] for s in spans), default=0),
        "all_red": bool(nonspace) and all(s["red"] for s in nonspace),
        "has_dropcap": any(s["role"] == "dropcap" for s in spans),
        "has_cross": any(s["role"] == "cross" for s in spans),
        "has_bullet": any(s["role"] == "bullet" for s in spans),
    }


# ---- 1. harvest genuine hyphenated compounds (hyphen interior, not a wrap) ----
compounds = set()
for pno in range(doc.page_count):
    for b in doc[pno].get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            t = "".join(s["text"] for s in l["spans"]).rstrip()
            for m in re.finditer(r"([A-Za-z]+)-([A-Za-z]+)", t):
                if m.end() < len(t):
                    compounds.add(m.group(0).lower())


# ---- 2. ordered stream of lines, with icon markers ----
ICON_PAGES = {14: "christ", 20: "banner"}
stream = []
for pno in range(1, doc.page_count):
    page_lines = []
    for b in doc[pno].get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            lo = line_obj(l)
            if not lo["text"].strip():
                continue
            if lo["y"] < TOP_DROP and lo["maxsize"] < 14:
                continue
            if lo["y"] > BOT_DROP and lo["maxsize"] < 14:
                continue
            page_lines.append(lo)
    # bucket y into ~4pt rows so two-column rows (label x≈33 + response x≈71,
    # whose tops differ by ~0.1pt) order left-to-right rather than by tiny y gaps
    page_lines.sort(key=lambda o: (round(o["y"] / 4), o["x0"]))
    if pno in ICON_PAGES:
        rects = []
        for img in doc.get_page_images(pno):
            rects += doc[pno].get_image_rects(img[0])
        iy = min((r.y0 for r in rects), default=0)
        page_lines.append({"image": ICON_PAGES[pno], "y": iy})
        page_lines.sort(key=lambda o: (round(o.get("y", 0) / 4), o.get("x0", 0)))
    stream.extend(page_lines)


# ---- 3. rendering helpers ----
def esc(t):
    return html.escape(t.replace("", ""), quote=False)


def render_inline(spans):
    """Render a list of spans (for rubrics / titles) to inline HTML."""
    out = []
    for s in spans:
        if s["role"] == "response":
            out.append('<span class="resp">℟</span>'); continue
        if s["role"] == "cross":
            out.append('<span class="cross">✠</span>'); continue
        if s["role"] == "bullet":
            out.append('<span class="bullet">❧</span>'); continue
        txt = s["t"]
        if not txt.strip():
            out.append(esc(txt)); continue          # whitespace: never wrap
        cls = []
        if s["red"]:    cls.append("r")
        if s["italic"]: cls.append("i")
        seg = esc(txt)
        if cls:
            seg = f'<span class="{" ".join(cls)}">{seg}</span>'
        out.append(seg)
    return "".join(out)


def flush_para(buf_lines):
    """Render one body paragraph (possibly spanning several wrapped lines)."""
    if not buf_lines:
        return None
    # build token list with line index
    tokens = []
    for li, lo in enumerate(buf_lines):
        for s in lo["spans"]:
            tokens.append({"t": s["t"], "role": s["role"], "red": s["red"],
                           "italic": s["italic"], "sm": s.get("sm", False), "line": li})
    # join across line boundaries (de-hyphenate / add spaces)
    merged = []
    for tok in tokens:
        if not merged:
            merged.append(tok); continue
        prev = merged[-1]
        if tok["line"] != prev["line"]:
            ptext = prev["t"]
            # soft hyphen wrap -> splice with no space
            if ptext.endswith(""):
                prev["t"] = ptext[:-1]
                merged.append(tok); continue
            # hard hyphen wrap
            m = re.search(r"([A-Za-z]+)-$", ptext)
            if m and prev["role"] == "text" and tok["role"] in ("text", "dropcap"):
                nm = re.match(r"\s*([A-Za-z]+)", tok["t"])
                cand = (m.group(1) + "-" + (nm.group(1) if nm else "")).lower()
                if cand in compounds:
                    pass                              # keep hyphen, no space
                else:
                    prev["t"] = ptext[:-1]            # drop hyphen, splice
                merged.append(tok); continue
            # ordinary wrap: ensure single separating space
            if prev["role"] != "dropcap" and not ptext.endswith((" ", " ")) \
               and not tok["t"].startswith((" ", " ")):
                tok["t"] = " " + tok["t"]
            merged.append(tok)
        else:
            merged.append(tok)

    # emit
    out = []
    idx = 0
    if merged and merged[0]["role"] == "dropcap":
        dc = merged[0]["t"]
        had_space = dc.endswith((" ", " "))
        letter = dc.strip()
        out.append(f'<span class="dropcap">{esc(letter)}</span>')
        idx = 1
        # small-caps lead-in on the next word
        if idx < len(merged):
            nxt = merged[idx]
            txt = nxt["t"]
            if nxt["role"] == "text" and txt.strip():
                m = re.match(r"^(\s*)(\S+)(.*)$", txt, re.S)
                lead_ws, word, rest = m.groups()
                if had_space and not lead_ws:
                    lead_ws = " "
                cls = "sc" + (" r" if nxt["red"] else "") + (" i" if nxt["italic"] else "")
                out.append(esc(lead_ws) + f'<span class="{cls}">{esc(word)}</span>')
                # push the remainder back as a token
                merged[idx] = {"t": rest, "role": "text",
                               "red": nxt["red"], "italic": nxt["italic"], "line": -1}
                # do not advance idx; fall through to render rest
    for tok in merged[idx:]:
        if tok["role"] == "response":
            out.append('<span class="resp">℟</span>'); continue
        if tok["role"] == "bullet":
            out.append('<span class="bullet">❧</span>'); continue
        if tok["role"] == "cross":
            out.append('<span class="cross">✠</span>'); continue
        txt = tok["t"]
        if not txt.strip():
            out.append(esc(txt)); continue
        cls = []
        if tok["red"]:    cls.append("r")
        if tok["italic"]: cls.append("i")
        seg = esc(txt)
        if cls:
            seg = f'<span class="{" ".join(cls)}">{seg}</span>'
        out.append(seg)
    return "".join(out).strip()


# ---- 4. segment the stream into elements ----
elements = []
body_buf, red_buf, verse_buf = [], [], []
in_shadow = False        # inside the indented "shadow" of a drop-cap / initial
shadow_through = False   # that initial is the ornamental "Through…" T


def emit_body():
    global body_buf, in_shadow
    if body_buf:
        h = flush_para(body_buf)
        if h:
            elements.append({"type": "p", "html": h})
    body_buf = []
    in_shadow = False


def emit_red():
    global red_buf
    if red_buf:
        big = max(l["maxsize"] for l in red_buf) >= 15.5
        inner = "<br>".join(render_inline(l["spans"]) for l in red_buf)
        elements.append({"type": "h2" if big else "rubric", "html": inner})
    red_buf = []


def emit_verse():
    global verse_buf
    if verse_buf:
        inner = "<br>".join(render_inline(l["spans"]) for l in verse_buf)
        elements.append({"type": "verse", "html": inner})
    verse_buf = []


def is_verse_line(lo):
    # truly centred couplets are indented from BOTH margins (x0 well past the
    # paragraph indent and the line short & centred)
    return (not lo["all_red"] and not lo["has_dropcap"]
            and lo["x0"] >= 60 and abs(lo["cx"] - PAGE_CX) <= 24 and lo["w"] <= 190)


i, N = 0, len(stream)
while i < N:
    lo = stream[i]
    if "image" in lo:
        emit_body(); emit_red(); emit_verse()
        elements.append({"type": "image", "name": lo["image"]}); i += 1; continue

    if lo["has_cross"]:
        emit_body(); emit_red(); emit_verse()
        j = i + 1; titles = []
        while j < N and "image" not in stream[j] and stream[j]["maxsize"] >= 18:
            titles.append(stream[j]); j += 1
        elements.append({"type": "divider",
                         "title": "<br>".join(render_inline(t["spans"]) for t in titles)})
        i = j; continue

    if lo["maxsize"] >= 18 and not lo["has_dropcap"]:
        emit_body(); emit_red(); emit_verse()
        j = i; titles = []
        while j < N and "image" not in stream[j] and stream[j]["maxsize"] >= 18:
            titles.append(stream[j]); j += 1
        elements.append({"type": "title",
                         "title": "<br>".join(render_inline(t["spans"]) for t in titles)})
        i = j; continue

    if lo["has_bullet"] and len(lo["text"].strip()) <= 2:
        emit_body(); emit_red(); emit_verse()
        elements.append({"type": "ornament"}); i += 1; continue

    # "For a priest:/layman:" two-column table: a red label cell in the left
    # margin (x≈33) and a black response cell in a column at x≈71, interleaved
    # row by row in reading order. Collect the whole block, then split into
    # (label, response) pairs by column.
    if lo["all_red"] and re.match(r"\s*For a\b", lo["text"]):
        emit_body(); emit_red(); emit_verse()
        block, j = [], i
        while j < N and "image" not in stream[j]:
            s = stream[j]
            is_label = s["x0"] < 65 and s["all_red"]
            is_resp  = s["x0"] >= 65 and not s["all_red"]
            if is_label or is_resp:
                block.append(s); j += 1
            else:
                break
        pairs, cur_lbl, cur_resp = [], [], []
        for s in block:
            if s["x0"] < 65:                      # label cell
                if re.match(r"\s*For a\b", s["text"]) and (cur_lbl or cur_resp):
                    pairs.append((cur_lbl, cur_resp)); cur_lbl, cur_resp = [], []
                cur_lbl.append(s["text"].strip())
            else:                                  # response cell
                cur_resp.append(s)
        if cur_lbl or cur_resp:
            pairs.append((cur_lbl, cur_resp))
        for lbl, resp in pairs:
            elements.append({"type": "hang",
                             "label": re.sub(r"\s+", " ", " ".join(lbl)),
                             "body": flush_para(resp) or ""})
        i = j; continue

    if lo["all_red"] and not lo["has_dropcap"]:
        emit_body(); emit_verse()
        red_buf.append(lo); i += 1; continue
    emit_red()

    if is_verse_line(lo):
        emit_body()
        verse_buf.append(lo); i += 1; continue
    emit_verse()

    # body line. A drop-cap (or the ornamental "T" of "Through…", which has no
    # text-layer glyph) opens a paragraph whose first lines are indented to clear
    # the initial; suppress indent-splitting until the text returns flush-left.
    opens_initial = lo["has_dropcap"] or lo["text"].lstrip().startswith("HROUGH")
    if opens_initial:
        emit_body(); body_buf.append(lo)
        # the ornamental "Through…" initial spans up to 3 lines; its prayer is a
        # single sentence ending "Amen." — close there to avoid swallowing the
        # next paragraph that also sits in the tall initial's shadow.
        through = lo["text"].lstrip().startswith("HROUGH")
        if through and "Amen" in lo["text"]:
            emit_body()
        else:
            in_shadow = True
            shadow_through = through
        i += 1; continue
    if in_shadow:
        body_buf.append(lo)
        if shadow_through and "Amen" in lo["text"]:
            emit_body()
        elif lo["x0"] < INDENT_X:
            in_shadow = False
        i += 1; continue
    if lo["x0"] >= INDENT_X:
        emit_body()
    body_buf.append(lo); i += 1

emit_body(); emit_red(); emit_verse()


# ---- 5. serialise ----
def plain(h):
    return re.sub("<[^>]+>", "", h).replace("✠", "").strip()

ICON_FIG = {
    "christ": '<figure class="icon"><img src="assets/img/icon_p15.png" '
              'alt="Icon of Christ the Teacher" width="500" height="598"></figure>',
    "banner": '<figure class="banner"><img src="assets/img/icon_p21.png" '
              'alt="Crucifixion — IC XC NIKA" width="600" height="191"></figure>',
}
SECTION_IDS = {"MORNINGPRAYERS": "morning", "PRAYERSATTABLE": "table",
               "PRAYERSBEFORESLEEP": "sleep"}
# clean display text for the few letter-spaced headings (the tracking in the
# source extracts as stray spaces; CSS recreates the spacing)
DIVIDER_TITLES = {"MORNINGPRAYERS": "Morning Prayers",
                  "PRAYERSATTABLE": "Prayers at Table",
                  "PRAYERSBEFORESLEEP": "Prayers Before Sleep"}
SUBHEADS = {"atthemorningmeal": "At the Morning Meal",
            "atthemiddaymeal": "At the Midday Meal",
            "atsupper": "At Supper"}

def nokey(h):
    return re.sub(r"[^a-z]", "", plain(h).lower())

out = []
for el in elements:
    t = el["type"]
    if t == "p":
        h = el["html"]
        # "Through the prayers…" has no T glyph in the PDF (it was a drawn
        # initial); render it as a plain red drop-cap T so it matches the others
        if h.startswith("HROUGH"):
            h = '<span class="dropcap">T</span><span class="sc">HROUGH</span>' + h[len("HROUGH"):]
        out.append(f"<p>{h}</p>")
    elif t == "verse":
        out.append(f'<p class="verse">{el["html"]}</p>')
    elif t == "rubric":
        out.append(f'<p class="rubric">{el["html"]}</p>')
    elif t == "h2":
        inner = el["html"]
        clean = SUBHEADS.get(nokey(inner))
        if clean:
            inner = f'<span class="r">{clean}</span>'
        out.append(f'<h2 class="subhead">{inner}</h2>')
    elif t == "hang":
        out.append(f'<div class="hang"><span class="label i r">{esc(el["label"])}</span>'
                   f'<p>{el["body"]}</p></div>')
    elif t == "divider":
        key = nokey(el["title"]).upper()
        sid = SECTION_IDS.get(key, "")
        idattr = f' id="{sid}"' if sid else ""
        title = DIVIDER_TITLES.get(key, el["title"])
        out.append(f'<section class="divider"{idattr}><span class="cross">✠</span>'
                   f'<h1>{title}</h1></section>')
    elif t == "title":
        title = re.sub(r"\s{2,}", " ", el["title"])   # collapse tracking gaps
        out.append(f'<section class="divider hours" id="hours"><h1>{title}</h1></section>')
    elif t == "ornament":
        out.append('<div class="ornament">❧</div>')
    elif t == "image":
        out.append(ICON_FIG[el["name"]])

open("prayers.content.html", "w").write("\n".join(out))
print(f"elements: {len(elements)} -> prayers.content.html ({sum(len(o) for o in out)} bytes)")
print("compounds:", len(compounds))
