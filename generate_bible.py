#!/usr/bin/env python3
"""Build the in-app Bible: Brenton's Septuagint (LXX, 1851) for the Old Testament
(incl. the deuterocanon) + the World English Bible (WEB) for the New Testament.
Both are public domain.

Sources (fetched from GitHub at generate time only — NOT a deploy/build input):
  OT  ctatum20/brenton-septuagint-data  _complete_brenton.json  {book:{chap:[{v,t}]}}
  NT  TehShrike/world-english-bible      json/<book>.json        [ {verseNumber,value}... ]

Output (committed, served statically, lazy-loaded by bible.js):
  bible/<id>.json        per-book: {"n":name,"g":group,"t":testament,"dc":0/1,"c":[[[v,"text"],...], ...]}
  bible-index.js         window.BIBLE = {groups:{...}, books:[{id,n,g,t,dc,ch}]}

Run once (or when the canon/sources change); the text is static so it is not
regenerated on every site build.
"""
import json
import os
import re
import subprocess

BRENTON_URL = "https://raw.githubusercontent.com/ctatum20/brenton-septuagint-data/main/_complete_brenton.json"
WEB_BASE = "https://raw.githubusercontent.com/TehShrike/world-english-bible/master/json/"

# canon order: (id, display, group, testament, deuterocanonical, source, source_key)
#   source "b" = Brenton (key = exact key in the Brenton JSON)
#   source "w" = WEB     (key = TehShrike json filename, no extension)
OT = [
    ("genesis", "Genesis", "law", "ot", 0, "b", "Genesis"),
    ("exodus", "Exodus", "law", "ot", 0, "b", "Exodus"),
    ("leviticus", "Leviticus", "law", "ot", 0, "b", "Leviticus"),
    ("numbers", "Numbers", "law", "ot", 0, "b", "Numbers"),
    ("deuteronomy", "Deuteronomy", "law", "ot", 0, "b", "Deuteronomy"),
    ("joshua", "Joshua", "history", "ot", 0, "b", "Joshua"),
    ("judges", "Judges", "history", "ot", 0, "b", "Judges"),
    ("ruth", "Ruth", "history", "ot", 0, "b", "Ruth"),
    ("1samuel", "I Samuel", "history", "ot", 0, "b", "I Samuel"),
    ("2samuel", "II Samuel", "history", "ot", 0, "b", "II Samuel"),
    ("1kings", "I Kings", "history", "ot", 0, "b", "I Kings"),
    ("2kings", "II Kings", "history", "ot", 0, "b", "II Kings"),
    ("1chronicles", "I Chronicles", "history", "ot", 0, "b", "I Chronicles"),
    ("2chronicles", "II Chronicles", "history", "ot", 0, "b", "II Chronicles"),
    ("1esdras", "I Esdras", "history", "ot", 1, "b", "I Esdras"),
    ("ezra", "Ezra", "history", "ot", 0, "b", "Ezra"),
    ("nehemiah", "Nehemiah", "history", "ot", 0, "b", "Nehemiah"),
    ("tobit", "Tobit", "history", "ot", 1, "b", "Tobit"),
    ("judith", "Judith", "history", "ot", 1, "b", "Judith"),
    ("esther", "Esther (Greek)", "history", "ot", 1, "b", "Esther (Greek)"),
    ("1maccabees", "I Maccabees", "history", "ot", 1, "b", "I Maccabees"),
    ("2maccabees", "II Maccabees", "history", "ot", 1, "b", "II Maccabees"),
    ("job", "Job", "wisdom", "ot", 0, "b", "Job"),
    ("psalms", "Psalms", "wisdom", "ot", 0, "b", "Psalms"),
    ("proverbs", "Proverbs", "wisdom", "ot", 0, "b", "Proverbs"),
    ("ecclesiastes", "Ecclesiastes", "wisdom", "ot", 0, "b", "Ecclesiastes"),
    ("song", "Song of Songs", "wisdom", "ot", 0, "b", "Song of Songs"),
    ("wisdom", "Wisdom of Solomon", "wisdom", "ot", 1, "b", "Wisdom of Solomon"),
    ("sirach", "Sirach", "wisdom", "ot", 1, "b", "Sirach"),
    ("hosea", "Hosea", "prophets", "ot", 0, "b", "Hosea"),
    ("amos", "Amos", "prophets", "ot", 0, "b", "Amos"),
    ("micah", "Micah", "prophets", "ot", 0, "b", "Micah"),
    ("joel", "Joel", "prophets", "ot", 0, "b", "Joel"),
    ("obadiah", "Obadiah", "prophets", "ot", 0, "b", "Obadiah"),
    ("jonah", "Jonah", "prophets", "ot", 0, "b", "Jonah"),
    ("nahum", "Nahum", "prophets", "ot", 0, "b", "Nahum"),
    ("habakkuk", "Habakkuk", "prophets", "ot", 0, "b", "Habakkuk"),
    ("zephaniah", "Zephaniah", "prophets", "ot", 0, "b", "Zephaniah"),
    ("haggai", "Haggai", "prophets", "ot", 0, "b", "Haggai"),
    ("zechariah", "Zechariah", "prophets", "ot", 0, "b", "Zechariah"),
    ("malachi", "Malachi", "prophets", "ot", 0, "b", "Malachi"),
    ("isaiah", "Isaiah", "prophets", "ot", 0, "b", "Isaiah"),
    ("jeremiah", "Jeremiah", "prophets", "ot", 0, "b", "Jeremiah"),
    ("baruch", "Baruch", "prophets", "ot", 1, "b", "Baruch"),
    ("lamentations", "Lamentations", "prophets", "ot", 0, "b", "Lamentations"),
    ("epjeremiah", "Letter of Jeremiah", "prophets", "ot", 1, "b", "Letter of Jeremiah"),
    ("ezekiel", "Ezekiel", "prophets", "ot", 0, "b", "Ezekiel"),
    ("daniel", "Daniel (Greek)", "prophets", "ot", 0, "b", "Daniel (Greek)"),
    ("susanna", "Susanna", "prophets", "ot", 1, "b", "Susanna"),
    ("bel", "Bel and the Dragon", "prophets", "ot", 1, "b", "Bel and the Dragon"),
    ("manasseh", "Prayer of Manasseh", "prophets", "ot", 1, "b", "Prayer of Manasseh"),
]
NT = [
    ("matthew", "Matthew", "gospels", "nt", 0, "w", "matthew"),
    ("mark", "Mark", "gospels", "nt", 0, "w", "mark"),
    ("luke", "Luke", "gospels", "nt", 0, "w", "luke"),
    ("john", "John", "gospels", "nt", 0, "w", "john"),
    ("acts", "Acts", "acts", "nt", 0, "w", "acts"),
    ("romans", "Romans", "epistles", "nt", 0, "w", "romans"),
    ("1corinthians", "I Corinthians", "epistles", "nt", 0, "w", "1corinthians"),
    ("2corinthians", "II Corinthians", "epistles", "nt", 0, "w", "2corinthians"),
    ("galatians", "Galatians", "epistles", "nt", 0, "w", "galatians"),
    ("ephesians", "Ephesians", "epistles", "nt", 0, "w", "ephesians"),
    ("philippians", "Philippians", "epistles", "nt", 0, "w", "philippians"),
    ("colossians", "Colossians", "epistles", "nt", 0, "w", "colossians"),
    ("1thessalonians", "I Thessalonians", "epistles", "nt", 0, "w", "1thessalonians"),
    ("2thessalonians", "II Thessalonians", "epistles", "nt", 0, "w", "2thessalonians"),
    ("1timothy", "I Timothy", "epistles", "nt", 0, "w", "1timothy"),
    ("2timothy", "II Timothy", "epistles", "nt", 0, "w", "2timothy"),
    ("titus", "Titus", "epistles", "nt", 0, "w", "titus"),
    ("philemon", "Philemon", "epistles", "nt", 0, "w", "philemon"),
    ("hebrews", "Hebrews", "epistles", "nt", 0, "w", "hebrews"),
    ("james", "James", "epistles", "nt", 0, "w", "james"),
    ("1peter", "I Peter", "epistles", "nt", 0, "w", "1peter"),
    ("2peter", "II Peter", "epistles", "nt", 0, "w", "2peter"),
    ("1john", "I John", "epistles", "nt", 0, "w", "1john"),
    ("2john", "II John", "epistles", "nt", 0, "w", "2john"),
    ("3john", "III John", "epistles", "nt", 0, "w", "3john"),
    ("jude", "Jude", "epistles", "nt", 0, "w", "jude"),
    ("revelation", "Revelation", "revelation", "nt", 0, "w", "revelation"),
]
CANON = OT + NT

GROUPS = [
    ("law", "The Law", "ot"),
    ("history", "History", "ot"),
    ("wisdom", "Wisdom", "ot"),
    ("prophets", "Prophets", "ot"),
    ("gospels", "The Gospels", "nt"),
    ("acts", "Acts", "nt"),
    ("epistles", "The Epistles", "nt"),
    ("revelation", "Revelation", "nt"),
]


def _get(url):
    # curl handles the agent proxy reliably (urllib truncates large bodies);
    # --retry covers transient proxy hiccups
    out = subprocess.run(
        ["curl", "-sS", "--fail", "--retry", "3", "--retry-delay", "1", url],
        capture_output=True, timeout=120)
    if out.returncode != 0:
        raise SystemExit(f"download failed ({out.returncode}) for {url}: {out.stderr.decode()[:200]}")
    return out.stdout


def _clean(s):
    return re.sub(r"[ \t]+", " ", (s or "").replace("¶", "")).strip()


def brenton_chapters(book):
    """Brenton book dict {chap:[{v,t}]} -> ordered [ [[v,text],...], ... ]."""
    out = []
    for ch in sorted(book.keys(), key=lambda x: int(x)):
        verses = [[vs["v"], _clean(vs["t"])] for vs in book[ch]]
        out.append(verses)
    return out


def web_chapters(items):
    """WEB list of typed items -> ordered [ [[v,text],...], ... ]."""
    chapters = {}        # chap -> {verse -> text}
    for it in items:
        if "verseNumber" not in it or "value" not in it:
            continue
        if "note" in (it.get("type") or ""):
            continue
        ch = it["verseNumber"] and it.get("chapterNumber")
        if ch is None:
            continue
        c = it["chapterNumber"]; v = it["verseNumber"]
        chapters.setdefault(c, {}).setdefault(v, "")
        chapters[c][v] += it["value"]
    out = []
    for c in sorted(chapters.keys()):
        verses = [[v, _clean(chapters[c][v])] for v in sorted(chapters[c].keys())]
        out.append(verses)
    return out


def main():
    os.makedirs("bible", exist_ok=True)
    print("downloading Brenton LXX…")
    brenton = json.loads(_get(BRENTON_URL))

    index = []
    for bid, name, group, testament, dc, src, key in CANON:
        if src == "b":
            if key not in brenton:
                raise SystemExit(f"missing Brenton book: {key!r}")
            chapters = brenton_chapters(brenton[key])
        else:
            items = json.loads(_get(WEB_BASE + key + ".json"))
            chapters = web_chapters(items)
        rec = {"n": name, "g": group, "t": testament, "dc": dc, "c": chapters}
        with open(f"bible/{bid}.json", "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, separators=(",", ":"))
        index.append({"id": bid, "n": name, "g": group, "t": testament,
                      "dc": dc, "ch": len(chapters)})
        print(f"  {name:24s} {len(chapters):3d} chapters")

    payload = {"groups": [{"id": g, "n": n, "t": t} for g, n, t in GROUPS], "books": index}
    with open("bible-index.js", "w", encoding="utf-8") as f:
        f.write("window.BIBLE=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"wrote bible-index.js + {len(index)} book files")


if __name__ == "__main__":
    main()
