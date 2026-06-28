#!/usr/bin/env python3
"""Assemble index.html (the prayer booklet) and resources.html (the Resources
area, incl. the Early Church Fathers reading checklist) from a shared shell.
Run `python3 generate.py` first to (re)produce prayers.content.html."""

import glob
import hashlib
import json
import os
import re
from urllib.parse import quote, urlparse

import generate_calendars as gc

content = open("prayers.content.html").read()
# one black, letter-spaced title the generator can't auto-clean (CSS spaces it)
content = re.sub(r"for\s+a\s+n\s+y\s+m\s+e\s+a\s+l", "for any meal", content)
# the Crucifixion banner is no longer displayed in the booklet pages
content = re.sub(r'<figure class="banner">.*?</figure>\s*', "", content, flags=re.S)
# the Christ-the-Teacher icon moves from the foot of Morning Prayers to the top
# of the Ancient Faith Prayer Book hub (added there as CHRIST_FIG)
content = re.sub(r'<figure class="icon">.*?</figure>\s*', "", content, flags=re.S)

LANDING = '''<section class="cover landing" id="top">
  <figure class="coverimg">
    <span class="reframe"><span class="reicon" role="img"
      aria-label="Icon of the Mother of God &ldquo;of the Sign&rdquo; (Znamenie)"
      style="--m:url(assets/img/icon_p1-mask.png); aspect-ratio:760/806"></span></span>
  </figure>
  <h1>PRAYERS <span class="i">for</span> MORNING,<br>DAY &amp; NIGHT</h1>
  <p class="landing-sub">An Orthodox prayer book &amp; companion for the journey</p>
  {rule}

  <section class="pray-now" aria-label="Begin praying">
    <p class="pn-eyebrow" id="pn-greet">Welcome</p>
    <a class="pn-primary" id="pn-primary" href="morning.html">
      <span class="pn-body">
        <span class="pn-when" id="pn-when">On rising</span>
        <span class="pn-title" id="pn-title">Morning Prayers</span>
      </span>
      <span class="pn-go" aria-hidden="true"><svg viewBox="0 0 24 24" width="22" height="22"
        fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
        stroke-linejoin="round"><path d="M5 12h13"/><path d="M12 6l6 6-6 6"/></svg></span>
    </a>
    <nav class="pn-all" aria-label="All daily prayers">
      <a href="morning.html">Morning</a>
      <a href="table.html">Table</a>
      <a href="hours.html">Hours</a>
      <a href="sleep.html">Before Sleep</a>
    </nav>
  </section>

  <section class="this-week" id="this-week" hidden></section>

  <details class="journey">
    <summary class="journey-sum">
      <span class="journey-sum-t">Coming Home to the Ancient Church</span>
      <span class="journey-sum-h">the story behind this book</span>
    </summary>
    <div class="landing-body">
    <p>Many who find their way to the Orthodox Church begin somewhere else — most often in the
       Western Protestant traditions: evangelical, Reformed, Baptist, Methodist, Anglican, or
       non-denominational. The path eastward is rarely a rejection of the love of Christ first
       learned there. It is a search for its <em>fullness</em> — for the Church of the Apostles,
       the worship of the early centuries, and the unbroken life of prayer that has carried the
       faith from the upper room to this very morning.</p>
    <p>For the Protestant inquirer, Orthodoxy can feel at once ancient and entirely new: the
       same Scriptures, the same Lord, yet received within a Church that never set aside the
       sacraments, the Creed of the Councils, the communion of the saints, or the honor due the
       Theotokos, the Mother of God. It is less a set of new ideas than an older way of being
       Christian — liturgical, sacramental, and rooted in the witness of the Fathers, who
       learned the faith from those who walked with Christ.</p>
    <p>This little book gathers the daily prayers of that tradition — for the morning, the
       table, the hours of the day, and the night — alongside resources for exploring the
       faith: the early Church Fathers, the Creeds and the Councils, and the questions that most
       often draw seekers eastward. Whether you are simply curious or already on the road, you
       are welcome here.</p>
    </div>
    <p class="landing-come">&ldquo;Come and see.&rdquo;<span class="landing-ref">John 1:46</span></p>
  </details>

  <nav class="landing-cta" aria-label="Explore">
    <a class="cta cta-ghost" href="resources.html">Explore the faith</a>
  </nav>

  {cross}

  <p class="colophon">These prayers are excerpted from <cite>Orthodox Christian
    Prayers</cite>, edited by Priest John Mikitish &amp; Hieromonk Herman
    (Majkrzak) (South Canaan, Penn.: St. Tikhon&rsquo;s Monastery Press, 2019).
    &copy; 2019 St. Tikhon&rsquo;s Monastery Press. All rights reserved.
    Permission is granted for this document to be made available on
    <a href="https://www.oca.org">www.oca.org</a>, for those who wish to use
    these prayers in their homes.</p>
  {pray_js}
</section>'''

# inline SVG icons (stroke uses currentColor; no emoji). Orthodox-themed,
# hand-drawn — HOME = a domed church, BOOK = the Gospel (cross on the cover),
# COMPASS = an open book/manuscript (Resources).
HOME = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><path d="M12 2v2.4"/><path d="M10.7 3.2h2.6"/>'
        '<path d="M12 4.8c1.4 0 2.3 1.1 2.3 2.4 0 1.5-2.3 3.2-2.3 3.2S9.7 8.7 9.7 7.2C9.7 5.9 10.6 4.8 12 4.8z"/>'
        '<path d="M6 21v-8.6l6-2.4 6 2.4V21"/><path d="M4 21h16"/>'
        '<path d="M10.3 21v-3.1a1.7 1.7 0 0 1 3.4 0V21"/></svg>')
BOOK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><rect x="5" y="3" width="14" height="18" rx="1.6"/>'
        '<path d="M12 7.4v6"/><path d="M9.4 9.6h5.2"/></svg>')
COMPASS = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true"><path d="M12 6.4v13.2"/>'
           '<path d="M12 6.4C9.8 5 6.6 5 4 6v12.6c2.6-1 5.8-1 8 .4"/>'
           '<path d="M12 6.4c2.2-1.4 5.4-1.4 8-.4v12.6c-2.6-1-5.8-1-8 .4"/></svg>')
GEAR = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 '
        '1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 '
        '0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 '
        '0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 '
        '1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 '
        '2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 '
        '0-1.51 1z"/></svg>')
CAMERA = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true">'
          '<path d="M4 8h3l1.4-2h7.2L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/>'
          '<circle cx="12" cy="13" r="3.2"/></svg>')
SUN = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
       'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/><path d="M12 1.5v2M12 20.5v2'
       'M3.9 3.9l1.4 1.4M18.7 18.7l1.4 1.4M1.5 12h2M20.5 12h2M3.9 20.1l1.4-1.4M18.7 5.3l1.4-1.4"/></svg>')
MOON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg>')
CLOSE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
         'aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>')

# ---- decorative artwork: original red line ornaments in the booklet's style ---
# (the source PDF holds only three woodcuts; these hand-drawn SVGs add more art
#  in the same red-ink idiom — the page tints them with the rubric red)
ORTHODOX_CROSS = (
    '<svg viewBox="0 0 120 200" fill="currentColor" aria-hidden="true">'
    '<rect x="54" y="14" width="12" height="172"/>'
    '<rect x="42" y="40" width="36" height="9"/>'
    '<rect x="22" y="80" width="76" height="12"/>'
    '<polygon points="30,150 90,132 90,143 30,161"/></svg>')

ICXC_ROUNDEL = (
    '<svg viewBox="0 0 140 140" aria-hidden="true" style="font-family:inherit">'
    '<circle cx="70" cy="70" r="64" fill="none" stroke="currentColor" stroke-width="4"/>'
    '<rect x="66" y="8" width="8" height="124" fill="currentColor"/>'
    '<rect x="8" y="66" width="124" height="8" fill="currentColor"/>'
    '<g fill="currentColor" font-size="20" text-anchor="middle" font-weight="600">'
    '<text x="37" y="46">IC</text><text x="103" y="46">XC</text>'
    '<text x="37" y="110">NI</text><text x="103" y="110">KA</text></g>'
    '<g stroke="currentColor" stroke-width="2">'
    '<line x1="28" y1="28" x2="46" y2="28"/><line x1="94" y1="28" x2="112" y2="28"/></g></svg>')

THEOTOKOS_MONO = (
    '<svg viewBox="0 0 210 80" aria-hidden="true" style="font-family:inherit">'
    '<g fill="currentColor" font-size="44" text-anchor="middle" font-weight="600">'
    '<text x="50" y="62">ΜΡ</text><text x="160" y="62">ΘΥ</text></g>'
    '<g stroke="currentColor" stroke-width="3">'
    '<line x1="22" y1="18" x2="78" y2="18"/><line x1="132" y1="18" x2="188" y2="18"/></g>'
    '<g fill="currentColor"><rect x="103" y="30" width="4" height="22"/>'
    '<rect x="96" y="37" width="18" height="4"/></g></svg>')

CHI_RHO = (
    '<svg viewBox="0 0 140 170" aria-hidden="true" style="font-family:inherit">'
    '<line x1="70" y1="18" x2="70" y2="155" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>'
    '<path d="M70 22 C100 22 100 70 70 70" fill="none" stroke="currentColor" stroke-width="9"/>'
    '<g stroke="currentColor" stroke-width="9" stroke-linecap="round">'
    '<line x1="44" y1="86" x2="96" y2="150"/><line x1="96" y1="86" x2="44" y2="150"/></g>'
    '<g fill="currentColor" font-size="26" text-anchor="middle">'
    '<text x="24" y="138">Α</text><text x="118" y="138">Ω</text></g></svg>')

RULE = (
    '<svg viewBox="0 0 240 18" aria-hidden="true" preserveAspectRatio="xMidYMid meet">'
    '<g stroke="currentColor" stroke-width="2" fill="currentColor">'
    '<line x1="14" y1="9" x2="100" y2="9"/><line x1="140" y1="9" x2="226" y2="9"/>'
    '<circle cx="14" cy="9" r="3" stroke="none"/><circle cx="226" cy="9" r="3" stroke="none"/>'
    '<circle cx="104" cy="9" r="2" stroke="none"/><circle cx="136" cy="9" r="2" stroke="none"/>'
    '<polygon points="120,1 129,9 120,17 111,9" stroke="none"/></g></svg>')

CAL = (
    '<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="6" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<rect x="16" y="26" width="88" height="80" rx="8"/><path d="M16 47h88"/>'
    '<path d="M40 16v18M80 16v18"/><path d="M58 68h30M34 88h54"/>'
    '<circle cx="40" cy="68" r="4.5" fill="currentColor" stroke="none"/></svg>')

GOSPEL_ORN = (
    '<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="6" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<rect x="26" y="14" width="68" height="92" rx="8"/>'
    '<path d="M60 34v40"/><path d="M44 50h32"/></svg>')

ORN = {
    "cross":   (ORTHODOX_CROSS, "Orthodox cross", "art-cross"),
    "roundel": (ICXC_ROUNDEL, "IC XC NIKA — the Cross of Christ Conquers", "art-roundel"),
    "mono":    (THEOTOKOS_MONO, "Mother of God (ΜΡ ΘΥ)", "art-mono"),
    "chirho":  (CHI_RHO, "Chi-Rho — the monogram of Christ, with Alpha and Omega", "art-chirho"),
    "rule":    (RULE, "Ornamental rule", "art-rule"),
    "cal":     (CAL, "Liturgical calendar", "art-cal"),
    "gospel":  (GOSPEL_ORN, "The Holy Scriptures", "art-gospel"),
}


def art(kind, foot=False):
    svg, label, cls = ORN[kind]
    extra = " art-foot" if foot else ""
    return f'<figure class="art {cls}{extra}" role="img" aria-label="{label}">{svg}</figure>'


# a closing cross to end a page (placed at the foot so it never pushes content down)
CLOSING = art("cross", foot=True)

# the gilt headpiece rule that crowns a section title
RULE_FIG = ('<figure class="art art-rule" role="img" aria-label="Ornamental rule">'
            + RULE + '</figure>')


def _headpiece(html):
    """Insert the gilt rule inside every section divider, just after its title,
    turning a bare title into an illuminated headpiece (cross -> TITLE -> rule)."""
    return re.sub(r'(<section class="divider[^"]*"[^>]*>.*?</h1>)(\s*</section>)',
                  r'\1' + RULE_FIG + r'\2', html, flags=re.S)


# the gilt cross drawn (not a font glyph) that crowns each headpiece
def _drawn_crosses(html):
    return html.replace('<span class="cross">✠</span>',
                        '<span class="cross">' + ORTHODOX_CROSS + '</span>')


# apply the drawn headpiece cross to the prayer-booklet content
content = _drawn_crosses(content)

# bottom tab bar (dedicated mobile nav): Home + Prayers/Resources pop-up
# sub-menus + the slide-up Settings sheet
TABBAR_TMPL = '''<nav class="tabbar" aria-label="Primary">
  <a class="tab{h_act}" href="index.html" aria-label="Home"><span class="tab-i">{HOME}</span><span class="tab-l">Home</span></a>
  <a class="tab{p_act}" href="prayers.html" aria-label="Prayers"><span class="tab-i">{BOOK}</span><span class="tab-l">Prayers</span></a>
  <button class="tab tab-fab" id="cam-btn" type="button" aria-label="Read Greek — take or choose a photo"><span class="tab-i">{CAMERA}</span><span class="tab-l">Greek</span></button>
  <input id="cam-input" type="file" accept="image/*" hidden>
  <a class="tab{r_act}" href="resources.html" aria-label="Resources"><span class="tab-i">{COMPASS}</span><span class="tab-l">Resources</span></a>
  <button class="tab" id="settings-btn" type="button" aria-haspopup="true" aria-expanded="false"
          aria-controls="menu" aria-label="Settings"><span class="tab-i">{GEAR}</span><span class="tab-l">Settings</span></button>
</nav>
<div id="menu-backdrop" class="backdrop"></div>
<div id="menu" class="drawer" role="dialog" aria-modal="true" aria-label="Settings">
  <div class="drawer-head">
    <span class="grab" aria-hidden="true"></span>
    <button class="drawer-close" type="button" aria-label="Close">{CLOSE}</button>
  </div>
  <div class="drawer-heading">Settings</div>
  <div class="menu-row">
    <span class="menu-label">Text size</span>
    <span class="seg" role="group" aria-label="Text size">
      <button id="size-dn" type="button" title="Smaller text" aria-label="Smaller text">A&minus;</button>
      <button id="size-up" type="button" title="Larger text" aria-label="Larger text">A+</button>
    </span>
  </div>
  <div class="menu-row">
    <span class="menu-label">Theme</span>
    <span class="seg" role="group" aria-label="Theme">
      <button id="theme-light" type="button" title="Light" aria-label="Light mode" aria-pressed="false">{SUN}</button>
      <button id="theme-dark" type="button" title="Dark" aria-label="Dark mode" aria-pressed="false">{MOON}</button>
    </span>
  </div>
  <div class="menu-row">
    <span class="menu-label">Background</span>
    <span class="seg" role="group" aria-label="Background temperature">
      <button id="temp-warm" type="button" aria-pressed="true">Warm</button>
      <button id="temp-cool" type="button" aria-pressed="false">Cool</button>
    </span>
  </div>
  <div class="menu-col">
    <span class="menu-label">Primary colour <span class="menu-pick" id="primary-pick">Default</span></span>
    {primary_sw}
  </div>
  <div class="menu-col">
    <span class="menu-label">Secondary colour <span class="menu-pick" id="secondary-pick">Default</span></span>
    {secondary_sw}
    <button class="menu-reset" id="appearance-reset" type="button">Reset to default</button>
  </div>
  <div class="menu-row">
    <span class="menu-label">Dyslexia-friendly</span>
    <button id="dys" class="switch" type="button" role="switch" aria-checked="false"
            aria-label="Dyslexia-friendly text"><span class="knob"></span></button>
  </div>
  <div class="menu-row">
    <span class="menu-label">Available offline</span>
    <button id="offline" class="switch" type="button" role="switch" aria-checked="false"
            aria-label="Available offline"><span class="knob"></span></button>
  </div>
  <p class="menu-note" id="offline-note">Save every page and your settings on this device, so the
     app works with no connection. External links still need internet.</p>
  <div class="drawer-heading">Church calendar</div>
  <div class="menu-row">
    <span class="menu-label">Follow the calendar</span>
    <span class="seg" role="group" aria-label="Follow the Church calendar">
      <button id="cal-off" type="button" aria-pressed="true">Off</button>
      <button id="cal-new" type="button" aria-pressed="false" title="Revised Julian (New)">New</button>
      <button id="cal-old" type="button" aria-pressed="false" title="Julian (Old)">Old</button>
    </span>
  </div>
  <div class="menu-row">
    <span class="menu-label">Fast-day reminders</span>
    <button id="fastnotify" class="switch" type="button" role="switch" aria-checked="false"
            aria-label="Fast-day reminders"><span class="knob"></span></button>
  </div>
  <p class="menu-note">Reminders appear when you open the app. For alerts even when it&rsquo;s
     closed, <a href="calendar.html">subscribe to the calendar</a>.</p>
</div>'''


def tabbar(active="", current=""):
    return TABBAR_TMPL.format(
        h_act=" active" if active == "home" else "",
        p_act=" active" if active == "prayers" else "",
        r_act=" active" if active == "resources" else "",
        HOME=HOME, BOOK=BOOK, CAMERA=CAMERA, COMPASS=COMPASS, GEAR=GEAR, SUN=SUN, MOON=MOON, CLOSE=CLOSE,
        primary_sw=_swatches("primary", BRAND_PRIMARY), secondary_sw=_swatches("secondary", BRAND_SECONDARY))


# ---- Early Church Fathers reading checklist --------------------------------
NA   = "https://www.newadvent.org/fathers/"
CCEL = "https://www.ccel.org/fathers"
ECW  = "https://www.earlychristianwritings.com/"
WSA  = "https://en.wikisource.org/wiki/Ante-Nicene_Fathers"
WSN  = "https://en.wikisource.org/wiki/Nicene_and_Post-Nicene_Fathers"


def lv(term):  # a LibriVox search that always resolves to results
    return "https://librivox.org/search?q=" + quote(term) + "&search_form=advanced"


# each work: (id, title, author/date, read-url-or-None, note)
ERAS = [
 {"name": "The Apostolic Fathers", "dates": "c. AD 70–155",
  "blurb": "The first generation after the Apostles — the earliest evidence of how the Church worshipped, was governed, and confessed its faith.",
  "read": [("New Advent", NA), ("Early Christian Writings", ECW), ("Wikisource (ANF I)", WSA)],
  "audio": lv("apostolic fathers"),
  "works": [
    ("didache", "The Didache", "Anonymous, c. 90", ECW+"didache.html",
     "A church manual — baptism, the Eucharist, fasting, and the “two ways” of life and death."),
    ("1clement", "First Epistle of Clement", "Clement of Rome, c. 96", ECW+"1clement.html",
     "Rome writes to Corinth on order and ministry — an early witness to apostolic succession."),
    ("ignatius", "The Seven Epistles", "Ignatius of Antioch, c. 107", ECW+"ignatius.html",
     "Written on the road to martyrdom: the bishop, the Eucharist, and the unity of the Church."),
    ("polycarp", "Letter to the Philippians", "Polycarp of Smyrna, c. 110", ECW+"polycarp.html",
     "A disciple of the Apostle John exhorts the Church to faith and righteousness."),
    ("mpolycarp", "The Martyrdom of Polycarp", "Church of Smyrna, c. 155", ECW+"martyrdompolycarp.html",
     "The earliest detailed account of a Christian martyrdom outside the New Testament."),
    ("barnabas", "The Epistle of Barnabas", "Anonymous, c. 130", ECW+"barnabas.html",
     "An early reading of the Old Testament as fulfilled in Christ."),
    ("diognetus", "The Epistle to Diognetus", "Mathetes, c. 130", ECW+"diognetus.html",
     "A luminous early apology describing Christians as “the soul of the world.”"),
    ("hermas", "The Shepherd of Hermas", "Hermas, c. 140", ECW+"shepherd.html",
     "Visions and parables on repentance; treasured and widely read in the early Church."),
    ("2clement", "Second Clement", "Anonymous, c. 150", ECW+"2clement.html",
     "The earliest surviving Christian sermon."),
    ("papias", "Fragments", "Papias of Hierapolis, c. 110", ECW+"papias.html",
     "Early traditions about the origins of the Gospels."),
  ]},
 {"name": "The Apologists", "dates": "c. AD 120–200",
  "blurb": "Defenders who explained the faith to emperors and philosophers, articulating doctrine in dialogue with the wider world.",
  "read": [("New Advent", NA), ("Early Christian Writings", ECW), ("Wikisource (ANF)", WSA)],
  "audio": lv("Justin Martyr"),
  "works": [
    ("justin-apol", "First & Second Apology", "Justin Martyr, c. 155", ECW+"justinmartyr.html",
     "A philosopher’s defense — and the earliest description of Sunday worship and the Eucharist."),
    ("justin-trypho", "Dialogue with Trypho", "Justin Martyr, c. 160", ECW+"justinmartyr.html",
     "A sustained discussion of Christ in the Hebrew Scriptures."),
    ("athenagoras", "A Plea for the Christians", "Athenagoras, c. 177", ECW+"athenagoras.html",
     "Answers the slanders against Christians and defends the resurrection."),
    ("theophilus", "To Autolycus", "Theophilus of Antioch, c. 180", ECW+"theophilus.html",
     "The first Christian use of the word “Trinity.”"),
    ("tatian", "Address to the Greeks", "Tatian, c. 170", ECW+"tatian.html",
     "A sharp critique of pagan culture; Tatian later compiled the Diatessaron gospel harmony."),
    ("minucius", "Octavius", "Minucius Felix, c. 200", None,
     "An elegant Latin dialogue defending the faith against its cultured despisers."),
  ]},
 {"name": "The Ante-Nicene Fathers", "dates": "c. AD 180–300",
  "blurb": "As the Church spread, these teachers confronted heresy and laid the groundwork of theology, the canon, and the rule of faith.",
  "read": [("New Advent", NA), ("CCEL (ANF)", CCEL), ("Wikisource (ANF)", WSA)],
  "audio": lv("Tertullian"),
  "works": [
    ("irenaeus-ah", "Against Heresies", "Irenaeus of Lyons, c. 180", ECW+"irenaeus.html",
     "Refutes Gnosticism and defines apostolic succession and the rule of faith — foundational."),
    ("irenaeus-demo", "On the Apostolic Preaching", "Irenaeus of Lyons, c. 190", None,
     "A short, warm catechism of the Christian faith."),
    ("tertullian-apol", "Apology", "Tertullian, c. 197", None,
     "“The blood of the martyrs is the seed of the Church.” The father of Latin theology."),
    ("tertullian-presc", "Prescription Against Heretics", "Tertullian, c. 200", None,
     "Argues that the Scriptures rightly belong to the Church."),
    ("clement-alex", "The Instructor & Stromateis", "Clement of Alexandria, c. 198", None,
     "Faith and learning joined; Christ as the teacher of the whole person."),
    ("hippolytus", "The Apostolic Tradition", "Hippolytus of Rome, c. 215", None,
     "An early church order: ordination, baptism, and the Eucharistic prayer."),
    ("origen-fp", "On First Principles", "Origen, c. 225", None,
     "The first attempt at a systematic theology."),
    ("origen-celsus", "Against Celsus", "Origen, c. 248", None,
     "A major reasoned defense of Christianity against a pagan critic."),
    ("cyprian-unity", "On the Unity of the Church", "Cyprian of Carthage, c. 251", None,
     "On the episcopate and the grave danger of schism."),
    ("gregory-thaum", "Declaration of Faith", "Gregory Thaumaturgus, c. 260", None,
     "An early Trinitarian creed."),
  ]},
 {"name": "The Nicene Age & the Greek Fathers", "dates": "AD 325–451",
  "blurb": "The age of the great councils, when the Trinitarian and Christological debates defined the Creed.",
  "read": [("New Advent", NA), ("CCEL (NPNF)", CCEL), ("Wikisource (NPNF)", WSN)],
  "audio": lv("Athanasius incarnation"),
  "works": [
    ("athanasius-inc", "On the Incarnation", "Athanasius of Alexandria, c. 318", None,
     "Why God became man — a perennial introduction to the faith."),
    ("athanasius-antony", "The Life of Antony", "Athanasius, c. 360", None,
     "The book that spread monasticism across the world."),
    ("cyril-jer", "Catechetical Lectures", "Cyril of Jerusalem, c. 350", None,
     "Instructions to the newly baptized — an early window into liturgy and creed."),
    ("basil-spirit", "On the Holy Spirit", "Basil the Great, c. 375", None,
     "Defends the divinity of the Spirit and the place of tradition in worship."),
    ("basil-hex", "The Hexaemeron", "Basil the Great, c. 370", None,
     "Homilies on the six days of creation."),
    ("naz-orations", "Five Theological Orations", "Gregory of Nazianzus, c. 380", None,
     "The most refined defense of the Trinity — earning him the title “the Theologian.”"),
    ("nyssa-catech", "The Great Catechism", "Gregory of Nyssa, c. 385", None,
     "A systematic exposition of the faith for teachers."),
    ("chrysostom-priest", "On the Priesthood", "John Chrysostom, c. 388", None,
     "On the dignity and the burden of the pastoral office."),
    ("chrysostom-hom", "Homilies on the Gospels", "John Chrysostom, c. 390", None,
     "“Golden-mouthed” preaching on Scripture and the Christian life."),
  ]},
 {"name": "The Latin Fathers", "dates": "AD 340–450",
  "blurb": "The Western fathers who shaped Latin Christianity, the Scriptures, and the doctrine of grace.",
  "read": [("New Advent", NA), ("CCEL (NPNF)", CCEL), ("Project Gutenberg", "https://www.gutenberg.org/")],
  "audio": lv("Augustine Confessions"),
  "works": [
    ("ambrose-myst", "On the Mysteries", "Ambrose of Milan, c. 390", None,
     "On baptism and the Eucharist, by the bishop who baptized Augustine."),
    ("jerome", "On Illustrious Men & Letters", "Jerome, c. 392", None,
     "The translator of the Latin Vulgate and a great scholar of Scripture."),
    ("augustine-conf", "Confessions", "Augustine of Hippo, c. 398",
     "https://www.gutenberg.org/ebooks/3296",
     "The first spiritual autobiography — “our heart is restless until it rests in Thee.”"),
    ("augustine-doc", "On Christian Doctrine", "Augustine, c. 397", None,
     "How to read, interpret, and teach the Scriptures."),
    ("augustine-city", "The City of God", "Augustine, c. 426", None,
     "History and theology written after the fall of Rome."),
    ("augustine-trin", "On the Trinity", "Augustine, c. 417", None,
     "The great Latin synthesis of Trinitarian theology."),
    ("vincent", "The Commonitory", "Vincent of Lérins, c. 434", None,
     "“What has been believed everywhere, always, and by all” — a rule for discerning tradition."),
    ("cassian", "The Conferences", "John Cassian, c. 426", None,
     "Brings the wisdom of the Egyptian desert monks to the West."),
  ]},
 {"name": "The Ecumenical Councils & Creeds", "dates": "AD 325–451",
  "blurb": "Where the Church, gathered as one, confessed the faith in the Creed and the great definitions of the Person of Christ.",
  "read": [("New Advent", NA), ("CCEL (NPNF II)", CCEL), ("Wikisource", WSN)],
  "audio": None,
  "works": [
    ("nicaea", "First Council of Nicaea — the Nicene Creed", "AD 325", None,
     "Christ “of one essence (homoousios) with the Father,” against Arianism."),
    ("const1", "First Council of Constantinople", "AD 381", None,
     "Completes the Creed and affirms the divinity of the Holy Spirit."),
    ("ephesus", "Council of Ephesus", "AD 431", None,
     "Mary as Theotokos and the unity of Christ’s person."),
    ("chalcedon", "Council of Chalcedon — the Definition", "AD 451", None,
     "Christ acknowledged in two natures, “without confusion or division.”"),
  ]},
]


# verified free full-text links per work (New Advent / CCEL, grounded by search)
CF_READ = {
 "didache":"https://www.newadvent.org/fathers/0714.htm",
 "1clement":"https://www.newadvent.org/fathers/1010.htm",
 "ignatius":"https://www.newadvent.org/fathers/0104.htm",
 "polycarp":"https://www.newadvent.org/fathers/0136.htm",
 "mpolycarp":"https://www.newadvent.org/fathers/0102.htm",
 "barnabas":"https://www.newadvent.org/fathers/0124.htm",
 "diognetus":"https://www.newadvent.org/fathers/0101.htm",
 "hermas":"https://www.newadvent.org/fathers/0201.htm",
 "2clement":"https://www.newadvent.org/fathers/1011.htm",
 "papias":"https://www.newadvent.org/fathers/0125.htm",
 "justin-apol":"https://www.newadvent.org/fathers/0126.htm",
 "justin-trypho":"https://www.newadvent.org/fathers/0128.htm",
 "athenagoras":"https://www.newadvent.org/fathers/0205.htm",
 "theophilus":"https://www.newadvent.org/fathers/0204.htm",
 "tatian":"https://www.newadvent.org/fathers/0202.htm",
 "minucius":"https://www.newadvent.org/fathers/0410.htm",
 "irenaeus-ah":"https://www.newadvent.org/fathers/0103.htm",
 "irenaeus-demo":"https://www.ccel.org/ccel/irenaeus/demonstr.html",
 "tertullian-apol":"https://www.newadvent.org/fathers/0301.htm",
 "tertullian-presc":"https://www.newadvent.org/fathers/0311.htm",
 "clement-alex":"https://www.newadvent.org/fathers/0210.htm",
 "hippolytus":"https://www.newadvent.org/fathers/0501.htm",
 "origen-fp":"https://www.newadvent.org/fathers/0412.htm",
 "origen-celsus":"https://www.newadvent.org/fathers/0416.htm",
 "cyprian-unity":"https://www.newadvent.org/fathers/050701.htm",
 "gregory-thaum":"https://www.newadvent.org/fathers/0601.htm",
 "athanasius-inc":"https://www.newadvent.org/fathers/2802.htm",
 "athanasius-antony":"https://www.newadvent.org/fathers/2811.htm",
 "cyril-jer":"https://www.newadvent.org/fathers/3101.htm",
 "basil-spirit":"https://www.newadvent.org/fathers/3203.htm",
 "basil-hex":"https://www.newadvent.org/fathers/3201.htm",
 "naz-orations":"https://www.newadvent.org/fathers/3102.htm",
 "nyssa-catech":"https://www.newadvent.org/fathers/2908.htm",
 "chrysostom-priest":"https://www.newadvent.org/fathers/1922.htm",
 "chrysostom-hom":"https://www.newadvent.org/fathers/2001.htm",
 "ambrose-myst":"https://www.newadvent.org/fathers/3405.htm",
 "jerome":"https://www.newadvent.org/fathers/2708.htm",
 "augustine-conf":"https://www.newadvent.org/fathers/1101.htm",
 "augustine-doc":"https://www.newadvent.org/fathers/1202.htm",
 "augustine-city":"https://www.newadvent.org/fathers/1201.htm",
 "augustine-trin":"https://www.newadvent.org/fathers/1301.htm",
 "vincent":"https://www.newadvent.org/fathers/3506.htm",
 "cassian":"https://www.newadvent.org/fathers/3508.htm",
 "nicaea":"https://www.newadvent.org/fathers/3801.htm",
 "const1":"https://www.newadvent.org/fathers/3808.htm",
 "ephesus":"https://www.newadvent.org/fathers/3810.htm",
 "chalcedon":"https://www.newadvent.org/fathers/3811.htm",
}
# per-work free audio (url, type) — verified; works without one fall back to the
# per-era LibriVox hub link
CF_AUDIO = {
 "justin-apol": ("https://librivox.org/the-first-apology-by-martyr/", "LibriVox"),
 "irenaeus-ah": ("https://librivox.org/against-heresies-by-irenaeus/", "LibriVox"),
 "athanasius-inc": ("https://archive.org/details/on_the_incarnation_2206_librivox", "LibriVox"),
 "athanasius-antony": ("https://librivox.org/the-life-of-anthony-by-athanasius-of-alexandria/", "LibriVox"),
 "cyril-jer": ("https://archive.org/details/CyrilJCatLects01", "LibriVox"),
 "basil-spirit": ("https://librivox.org/the-book-of-saint-basil-on-the-spirit-by-basil-of-caesarea/", "LibriVox"),
 "basil-hex": ("https://librivox.org/the-hexaemeron-by-basil-of-caesarea/", "LibriVox"),
 "naz-orations": ("https://librivox.org/theological-orations-by-gregory-of-nazianzus/", "LibriVox"),
 "nyssa-catech": ("https://librivox.org/on-virginity-by-gregory-of-nyssa/", "LibriVox"),
 "chrysostom-priest": ("https://archive.org/details/on-the-priesthood-chrysostom_202109", "audio"),
 "ambrose-myst": ("https://archive.org/details/on_duties_of_clergy_librivox", "LibriVox"),
 "jerome": ("https://librivox.org/on-illustrious-men-de-viris-illustribus-by-saint-jerome/", "LibriVox"),
 "augustine-conf": ("https://librivox.org/the-confessions-by-saint-augustine-of-hippo/", "LibriVox"),
 "augustine-city": ("https://librivox.org/the-city-of-god-by-st-augustine-of-hippo/", "LibriVox"),
 "augustine-doc": ("https://librivox.org/on-christian-doctrine-by-saint-augustine-of-hippo/", "LibriVox"),
 "augustine-trin": ("https://www.youtube.com/watch?v=N1qKWQw87Es", "YouTube"),
 "vincent": ("https://librivox.org/the-commonitory-of-saint-vincent-lerins-by-vincent-lerins/", "LibriVox"),
 "cassian": ("https://librivox.org/the-conferences-of-john-cassian-part-i-by-john-cassian/", "LibriVox"),
}
AUDIO_HUBS = [
 ("LibriVox", "https://librivox.org/"),
 ("Ancient Faith Radio", "https://www.ancientfaith.com/"),
 ("YouTube", "https://www.youtube.com/results?search_query=church+fathers+audiobook"),
]

# reference sections (free links), shown after the chronological checklist
REF_SECTIONS = [
 {"name": "The Creeds", "blurb": "The Church's confessions of faith, in a few lines.",
  "items": [
    ("The Nicene–Constantinopolitan Creed (381)", "https://www.newadvent.org/cathen/11049a.htm",
     "The Creed of the first two Ecumenical Councils — recited at every Liturgy."),
    ("The Apostles' Creed", "https://www.newadvent.org/cathen/01629a.htm",
     "An ancient baptismal creed of the Western Church."),
    ("The Athanasian Creed (Quicumque Vult)", "https://ccel.org/ccel/schaff/creeds2.iv.i.iv.html",
     "A precise confession of the Trinity and the Incarnation."),
    ("The Chalcedonian Definition (451)", "https://www.newadvent.org/fathers/3811.htm",
     "Christ in two natures, “without confusion or division.”"),
  ]},
 {"name": "Catechisms", "blurb": "Ordered introductions to the whole of the faith.",
  "items": [
    ("The Orthodox Faith — Fr. Thomas Hopko", "https://www.oca.org/orthodoxy/the-orthodox-faith",
     "A free four-volume introduction from the OCA: doctrine, worship, Bible, spirituality.", True),
    ("The Longer Catechism — St. Philaret of Moscow", "https://www.ccel.org/ccel/schaff/creeds2.html",
     "The classic question-and-answer catechism of the Orthodox Church.", True),
    ("An Exact Exposition of the Orthodox Faith — St. John of Damascus",
     "https://www.newadvent.org/fathers/3304.htm",
     "The great early synthesis of patristic theology.", True),
    ("How to Be an Orthodox Christian (podcast)",
     "https://www.ancientfaith.com/podcasts/how-to-be-an-orthodox-christian/",
     "A free catechetical podcast series for inquirers, from Ancient Faith.", True),
  ]},
 {"name": "Recommended Reading", "blurb": "A few books to go deeper — free where the text is public-domain.",
  "items": [
    ("Athanasius — On the Incarnation", "https://www.ccel.org/ccel/athanasius/incarnation.html",
     "The classic short treatise on why God became man.", True),
    ("The Apostolic Fathers (Lightfoot translation)", "https://ccel.org/ccel/lightfoot/fathers.html",
     "Clement, Ignatius, Polycarp, the Didache and more, in one free volume.", True),
    ("Eusebius — Church History", "https://www.newadvent.org/fathers/2501.htm",
     "The first history of the Church, from the Apostles to Constantine.", True),
    ("Alexander Schmemann — For the Life of the World", "https://svspress.com/for-the-life-of-the-world-new-edition/",
     "A modern classic on the sacraments and the world as gift.", False),
    ("Vladimir Lossky — The Mystical Theology of the Eastern Church",
     "https://en.wikipedia.org/wiki/Vladimir_Lossky",
     "The landmark 20th-century synthesis of Orthodox theology.", False),
    ("Kallistos Ware — The Orthodox Way", "https://svspress.com/the-orthodox-way-classics-series-vol-2/",
     "A warm, accessible introduction to the Orthodox vision of God.", False),
    ("Jaroslav Pelikan — The Emergence of the Catholic Tradition (100–600)",
     "https://press.uchicago.edu/ucp/books/book/chicago/C/bo3799466.html",
     "Volume 1 of the great history of the development of doctrine.", False),
    ("Georges Florovsky — The Eastern Fathers of the Fourth Century",
     "http://www.holytrinitymission.org/books/english/fathers_florovsky_1.htm",
     "A free, masterful survey of the Greek Fathers.", True),
  ]},
]


# in-depth topics: an original summary of the Orthodox understanding + curated
# early-Church writings and trusted explanations (free links verified by search)
TOPICS = [
 {"name": "The Theotokos",
  "intro": "Theotokos (“God-bearer”) is the Church’s oldest title for the Virgin Mary, and "
           "first of all a confession about Christ: because the one she bore is truly God made "
           "man, she is rightly called the Mother of God. The Third Ecumenical Council (Ephesus, "
           "431) affirmed this title to guard the unity of Christ’s divine and human natures in "
           "one Person. The Church honors her as Ever-Virgin and as the “new Eve,” whose "
           "obedience undid the disobedience of the first — venerated above all the saints, yet "
           "her glory is always referred to her Son, for God alone is worshipped.",
  "items": [
    ("Council of Ephesus (AD 431)", "https://www.newadvent.org/fathers/3810.htm",
     "Proclaimed Mary as Theotokos, safeguarding the unity of Christ.", True),
    ("Cyril of Alexandria — Third Letter to Nestorius (with the Twelve Anathemas)",
     "https://www.ccel.org/ccel/schaff/npnf214.x.viii.html",
     "The letter that framed the Council’s decision on the Theotokos.", True),
    ("Justin Martyr — Dialogue with Trypho (ch. 100: Mary, the new Eve)",
     "https://www.newadvent.org/fathers/0128.htm", "One of the earliest Eve–Mary parallels.", True),
    ("Irenaeus — Against Heresies (the obedience of the Virgin)",
     "https://www.newadvent.org/fathers/0103.htm", "Develops Mary as the new Eve.", True),
    ("St John of Damascus — An Exact Exposition of the Orthodox Faith",
     "https://www.newadvent.org/fathers/3304.htm",
     "The classic synthesis, including the Ever-Virgin and the Dormition.", True),
    ("“Beneath Thy Protection” (Sub Tuum Praesidium)", "https://en.wikipedia.org/wiki/Sub_tuum_praesidium",
     "The oldest known prayer to the Theotokos — a 3rd-century papyrus already calling her by that name.", True),
    ("The Veneration of the Virgin Mary — Abp Dmitri (Royster)", "https://orthochristian.com/58526.html",
     "An Orthodox explanation of how and why she is honored.", True),
    ("The Ever-Virginity of the Mother of God (GOARCH)",
     "https://www.goarch.org/-/the-ever-virginity-of-the-mother-of-god",
     "On the Church’s teaching of her perpetual virginity.", True),
    ("The Theotokos and the Church (OCA)", "https://www.oca.org/reflections/berzonsky/the-theotokos-and-the-church",
     "A short reflection on her place in the life of the Church.", True),
  ]},
 {"name": "The Priesthood",
  "intro": "From the beginning the Church has been ordered around a threefold ministry — bishop, "
           "presbyter (priest), and deacon — received from the Apostles by the laying on of hands "
           "and handed down in unbroken succession. The bishop is the icon of Christ and the "
           "center of the local Church; the priest shepherds the parish and celebrates the "
           "Mysteries (sacraments); the deacon serves. Ordination is not a career but a calling "
           "and a gift of the Holy Spirit, and the Church has always set high requirements — in "
           "faith, character, and life (cf. 1 Timothy 3; Titus 1) — for those who serve at the "
           "altar. Alongside this ordained priesthood, all the baptized share in the royal "
           "priesthood of Christ.",
  "items": [
    ("St John Chrysostom — On the Priesthood (Six Books)", "https://www.newadvent.org/fathers/1922.htm",
     "The classic treatise on the dignity and burden of the priestly office.", True),
    ("St Gregory the Theologian — Oration 2 (In Defense of His Flight)",
     "https://www.newadvent.org/fathers/310202.htm",
     "The great patristic exposition of the character of the priesthood.", True),
    ("St Ignatius of Antioch — The Seven Epistles", "https://www.newadvent.org/fathers/0104.htm",
     "Earliest witness to the bishop, presbyter, and deacon, and the unity of the Church around the bishop.", True),
    ("St Clement of Rome — First Epistle (order & succession)", "https://www.newadvent.org/fathers/1010.htm",
     "On the apostolic ordering of ministry and succession.", True),
    ("Hippolytus — The Apostolic Tradition (the ordination prayers)",
     "https://www.gutenberg.org/files/61614/61614-h/61614-h.htm",
     "The earliest surviving rite of ordination.", True),
    ("The Orthodox Faith — Holy Orders (OCA)",
     "https://www.oca.org/orthodoxy/the-orthodox-faith/worship/the-sacraments/holy-orders",
     "The Orthodox understanding of ordination and the clergy.", True),
    ("The Orthodox Faith — Priesthood (OCA)",
     "https://www.oca.org/orthodoxy/the-orthodox-faith/doctrine-scripture/salvation-history/priesthood",
     "Christ’s priesthood and the ministry of the Church.", True),
  ]},
]


def _divider(title):
    return (f'<section class="divider"><span class="cross">{ORTHODOX_CROSS}</span><h1>{title}</h1>'
            + RULE_FIG + '</section>')


# small up-right arrow marking an external destination
_EXT = ('<svg class="link-row__ext" viewBox="0 0 24 24" width="16" height="16" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true"><path d="M7 17 17 7"/><path d="M8 7h9v9"/></svg>')

# right-pointing chevron for internal "go to" rows (hub destinations)
_CHEV_R = ('<svg class="row-chev" viewBox="0 0 24 24" width="18" height="18" fill="none" '
           'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
           'aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>')

# lights the office whose time-of-day window contains the current hour (the
# windows wrap past midnight, e.g. Before Sleep 21–04)
NOW_JS = ('<script>(function(){var h=new Date().getHours(),'
          'e=document.querySelectorAll(".office[data-h0]");for(var i=0;i<e.length;i++){'
          'var a=+e[i].getAttribute("data-h0"),b=+e[i].getAttribute("data-h1");'
          'if(a<b?(h>=a&&h<b):(h>=a||h<b))e[i].classList.add("office--now");}})();</script>')

# the home "pray now" hero: pick the office of the moment by local hour
HOME_JS = ('<script>(function(){var h=new Date().getHours();'
           'var s=[[4,11,"morning.html","On rising","Morning Prayers","Good morning"],'
           '[11,17,"hours.html","Through the day","Prayers for the Hours","Good afternoon"],'
           '[17,21,"hours.html","This evening","Prayers for the Hours","Good evening"],'
           '[21,4,"sleep.html","At nightfall","Prayers Before Sleep","A blessed evening"]];'
           'var c=s[0];for(var i=0;i<s.length;i++){var a=s[i][0],b=s[i][1];'
           'if(a<b?(h>=a&&h<b):(h>=a||h<b)){c=s[i];break;}}'
           'function t(id,v){var el=document.getElementById(id);if(el)el.textContent=v;}'
           'var p=document.getElementById("pn-primary");if(p)p.setAttribute("href",c[2]);'
           't("pn-when",c[3]);t("pn-title",c[4]);t("pn-greet",c[5]);})();</script>')


def _office_row(title, href, blurb, emb, when, h0, h1):
    attr = f' data-h0="{h0}" data-h1="{h1}"' if h0 is not None else ''
    return (f'<li class="office"{attr}><a class="office-link" href="{href}">'
            f'<span class="office-node" aria-hidden="true">{ORN[emb][0]}</span>'
            f'<span class="office-body"><span class="office-when">{when}'
            f'<span class="office-now">Now</span></span>'
            f'<span class="office-t">{title}</span>'
            f'<span class="office-d">{blurb}</span></span>{_CHEV_R}</a></li>')


def _cycle(items):
    return '<ol class="cycle">' + "".join(_office_row(*it) for it in items) + '</ol>'


def _browse_row(name, href, blurb, emb):
    return (f'<li><a class="browse-row" href="{href}">'
            f'<span class="browse-emblem" aria-hidden="true">{ORN[emb][0]}</span>'
            f'<span class="browse-body"><span class="browse-t">{name}</span>'
            f'<span class="browse-d">{blurb}</span></span>{_CHEV_R}</a></li>')


def _host(url):
    try:
        h = urlparse(url).netloc.lower()
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""


def _links_ul(items):
    """A crafted list of destination rows (premium replacement for bare link lists)."""
    out = ['<ul class="link-list">']
    for it in items:
        title, url, desc = it[0], it[1], it[2]
        free = len(it) > 3 and it[3]
        badge = ' <span class="badge--free">free</span>' if free else ''
        host = _host(url)
        hostline = f'<span class="link-row__host">{host}</span>' if host else ''
        out.append(
            f'<li><a class="link-row" href="{url}" target="_blank" rel="noopener">'
            f'<span class="link-row__body">'
            f'<span class="link-row__title">{title}{badge}</span>'
            f'<span class="link-row__desc">{desc}</span>{hostline}</span>{_EXT}</a></li>')
    out.append('</ul>')
    return "\n".join(out)


_BACK_ARROW = ('<svg class="res-back__i" viewBox="0 0 24 24" width="16" height="16" fill="none" '
               'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
               'aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>')
BACK = f'<a class="res-back" href="resources.html">{_BACK_ARROW}<span>All resources</span></a>'


def back_link(href, label):
    """A back-to-hub pill, left-aligned at the top of a reading page."""
    return (f'<div class="page-back"><a class="res-back" href="{href}">'
            f'{_BACK_ARROW}<span>{label}</span></a></div>')


def topic_page(topic, ornament=""):
    return "\n".join(['<section class="resources">', BACK, _divider(topic["name"]),
                      f'<p class="topic-intro">{topic["intro"]}</p>',
                      _links_ul(topic["items"]),
                      (art(ornament, foot=True) if ornament else ""), '</section>'])


def ref_page(ref, ornament=""):
    o = ['<section class="resources">', BACK, _divider(ref["name"])]
    if ref.get("blurb"):
        o.append(f'<p class="topic-intro">{ref["blurb"]}</p>')
    o.append(_links_ul(ref["items"]))
    if ornament:
        o.append(art(ornament, foot=True))
    o.append('</section>')
    return "\n".join(o)


# long-form in-depth articles (lead paragraph + sub-sections + sources)
ARTICLES = [
 {"name": "The Ecumenical Councils", "slug": "councils", "ornament": "cross",
  "lead": "An Ecumenical Council is a gathering of the bishops of the whole Church to confess "
          "the one faith and to settle the disputes that threaten her unity. The Orthodox Church "
          "receives <strong>seven</strong> such councils as ecumenical; together they gave us the "
          "Creed and the boundaries within which the Church speaks of the Holy Trinity and of the "
          "Person of Christ. A council&rsquo;s authority rests not in the assembly itself but in "
          "its reception by the whole Body of the Church.",
  "sections": [
    ("First Council of Nicaea — 325",
     ["Summoned by St Constantine against the teaching of Arius, who held the Son to be a creature. "
      "The Council confessed the Son to be <em>of one essence</em> (homoousios) with the Father, gave "
      "the first part of the Creed, set a common reckoning of Pascha, and issued twenty canons."]),
    ("First Council of Constantinople — 381",
     ["Completed the Creed we still recite (the Nicene&ndash;Constantinopolitan Creed) and affirmed the "
      "divinity of the Holy Spirit against those who denied it, condemning also the teaching of "
      "Apollinaris that Christ lacked a human mind."]),
    ("Council of Ephesus — 431",
     ["Affirmed that the Virgin Mary is truly <em>Theotokos</em>, the Mother of God, and that the one "
      "born of her is the one divine Person of the Word made flesh &mdash; against Nestorius, who divided "
      "Christ into two."]),
    ("Council of Chalcedon — 451",
     ["Defined that the one Christ is made known in <em>two natures</em>, divine and human, &ldquo;without "
      "confusion, change, division, or separation,&rdquo; united in one Person &mdash; against Eutyches, "
      "who taught that Christ&rsquo;s humanity was swallowed up in his divinity."]),
    ("Second Council of Constantinople — 553",
     ["Reaffirmed Chalcedon and Cyril of Alexandria, clarifying that there is one Person (hypostasis) of "
      "Christ in two natures, and condemned writings that still leaned toward Nestorianism."]),
    ("Third Council of Constantinople — 680&ndash;681",
     ["Confessed <em>two wills and two energies</em> in Christ, divine and human, his human will freely "
      "obeying the divine &mdash; against Monothelitism, which allowed him only one will."]),
    ("Second Council of Nicaea — 787",
     ["Restored the veneration of the holy icons against Iconoclasm, teaching that the honour given to an "
      "icon passes to the one it depicts, and carefully distinguishing veneration (proskynesis) from the "
      "worship (latreia) due to God alone."]),
    ("Councils after the Seven",
     ["The Church&rsquo;s conciliar life did not end in 787. The Orthodox hold in high regard later "
      "councils such as that of Constantinople in 879&ndash;880 under St Photios, the Hesychast councils "
      "of 1341&ndash;1351 that affirmed St Gregory Palamas&rsquo; distinction between God&rsquo;s "
      "unknowable essence and his uncreated energies, and the Synod of Jerusalem (1672). Some are "
      "regarded by many Orthodox as carrying ecumenical authority."]),
  ],
  "items": [
    ("The Seven Ecumenical Councils — canons &amp; definitions (NPNF II.14)",
     "https://ccel.org/ccel/schaff/npnf214", "Schaff&rsquo;s full canons and dogmatic decrees.", True),
    ("Nicaea I (325)", "https://www.newadvent.org/fathers/3801.htm", "The Creed and twenty canons.", True),
    ("Constantinople I (381)", "https://www.newadvent.org/fathers/3808.htm", "Completes the Creed.", True),
    ("Ephesus (431)", "https://www.newadvent.org/fathers/3810.htm", "Mary as Theotokos.", True),
    ("Chalcedon (451)", "https://www.newadvent.org/fathers/3811.htm", "The Definition of the two natures.", True),
    ("The first seven councils — overview", "https://en.wikipedia.org/wiki/First_seven_ecumenical_councils",
     "A concise survey with dates, places and decisions.", True),
  ]},
 {"name": "The Bible &amp; Its Canon", "slug": "bible", "ornament": "gospel",
  "lead": "The Orthodox Church did not so much <em>choose</em> the books of the Bible as <em>recognize</em> "
          "the books she had always read and prayed. Scripture is the Church&rsquo;s own book, received "
          "and interpreted within Holy Tradition; the canon &mdash; the list of books &mdash; took settled "
          "shape gradually, confirmed by the Fathers and the councils as the Church discerned which "
          "writings the Holy Spirit had given her.",
  "sections": [
    ("The Old Testament — the Septuagint",
     ["The Orthodox read the Greek <em>Septuagint</em> (LXX), the translation used by the Apostles and "
      "quoted throughout the New Testament. Its Old Testament is broader than the later Hebrew (and "
      "Protestant) canon, and it is the text from which the Church&rsquo;s services are drawn."]),
    ("The Anagignoskomena — &ldquo;the books that are read&rdquo;",
     ["Beyond the books shared with the Hebrew canon, the Church receives a number of others read in "
      "worship: Tobit, Judith, the Wisdom of Solomon, the Wisdom of Sirach, Baruch and the Letter of "
      "Jeremiah, 1&ndash;3 Maccabees, 1 Esdras, additions to Daniel and Esther, Psalm 151 and the Prayer "
      "of Manasseh. Orthodox tradition calls these the <em>anagignoskomena</em> &mdash; profitable and "
      "Scripture, though some Fathers rank them a step below the rest."]),
    ("The New Testament",
     ["The twenty-seven books of the New Testament are the same as those held across the Christian world. "
      "They were not imposed from above but proved themselves through use &mdash; read in the Liturgy, "
      "received from the Apostles, and recognized in the same faith everywhere."]),
    ("How the canon was received",
     ["The list was confirmed over time rather than at a single moment. St Athanasius&rsquo; 39th Festal "
      "Letter (367) gives the earliest list of the twenty-seven New Testament books; regional councils at "
      "Laodicea (c. 363) and Carthage (397) set out the canon; the Council in Trullo (692) ratified these "
      "earlier canons for the whole Church; and the Synod of Jerusalem (1672) reaffirmed the Orthodox "
      "Scriptures against later Western disputes. Throughout, the canon is read <em>within</em> the "
      "Church, not apart from her."]),
  ],
  "items": [
    ("St Athanasius — Letters (incl. the 39th Festal Letter, 367)", "https://ccel.org/ccel/schaff/npnf204",
     "The earliest list of the twenty-seven New Testament books.", True),
    ("The Synod of Jerusalem (1672) &amp; the Confession of Dositheus", "https://ccel.org/ccel/schaff/creeds2",
     "The Orthodox reaffirmation of the Scriptures and the faith.", True),
    ("The Septuagint (LXX)", "https://en.wikipedia.org/wiki/Septuagint",
     "The Greek Old Testament of the early Church.", True),
    ("The Anagignoskomena / deuterocanon", "https://en.wikipedia.org/wiki/Deuterocanonical_books",
     "The books read in the Church beyond the Hebrew canon.", True),
    ("How the biblical canon developed", "https://en.wikipedia.org/wiki/Development_of_the_Christian_biblical_canon",
     "A historical overview of the canon&rsquo;s formation.", True),
    ("The Orthodox Faith — Scripture &amp; Tradition (OCA)", "https://www.oca.org/orthodoxy/the-orthodox-faith",
     "Fr Thomas Hopko&rsquo;s free introduction, including the Bible.", True),
  ]},
]
ARTICLE_BY_SLUG = {a["slug"]: a for a in ARTICLES}


def article_page(a):
    o = ['<section class="resources">', BACK, _divider(a["name"])]
    if a.get("lead"):
        o.append(f'<p class="article-lead">{a["lead"]}</p>')
    for sub, paras in a["sections"]:
        o.append(f'<h2 class="subhead">{sub}</h2>')
        for p in paras:
            o.append(f'<p class="topic-intro">{p}</p>')
    o.append(_links_ul(a["items"]))
    if a.get("ornament"):
        o.append(art(a["ornament"], foot=True))
    o.append('</section>')
    return "\n".join(o)


def fathers_page(ornament=""):
    o = ['<section class="resources" id="papers">', BACK, _divider("The Early Church Fathers")]
    o.append('<p class="res-intro">A reading path through the first centuries of the Church — '
             'tick each work as you read or listen; your progress is saved on this device.</p>')
    hubs = " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in AUDIO_HUBS)
    o.append(f'<p class="cf-audiohubs">Listen free: {hubs}</p>')
    o.append('<div class="cf-progress-wrap"><div class="cf-progress-row">'
             '<span id="cf-progress">0 read</span></div>'
             '<span class="cf-track"><span id="cf-bar" class="cf-fill"></span></span></div>')
    # small read/listen glyphs for the action chips
    _CF_READ_I = ('<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" '
                  'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                  '<path d="M2 5h8a3 3 0 0 1 3 3v11a2.5 2.5 0 0 0-2.5-2.5H2z"/>'
                  '<path d="M22 5h-8a3 3 0 0 0-3 3v11a2.5 2.5 0 0 1 2.5-2.5H22z"/></svg>')
    _CF_LISTEN_I = ('<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" '
                    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                    '<path d="M11 5 6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/></svg>')
    for era in ERAS:
        o.append('<section class="cf-era">')
        o.append(f'<h3 class="cf-era-h">{era["name"]} <span class="cf-dates">{era["dates"]}</span></h3>')
        o.append(f'<p class="cf-blurb">{era["blurb"]}</p>')
        src = " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in era["read"])
        if era.get("audio"):
            src += f' &nbsp;·&nbsp; Audio: <a href="{era["audio"]}" target="_blank" rel="noopener">LibriVox</a>'
        o.append(f'<p class="cf-sources">Read free: {src}</p>')
        o.append('<ul class="cf-list">')
        for wid, title, by, read, note in era["works"]:
            url = CF_READ.get(wid) or read
            rl = (f'<a class="cf-chip" href="{url}" target="_blank" rel="noopener">'
                  f'{_CF_READ_I}<span>Read</span></a>' if url else '')
            au = CF_AUDIO.get(wid)
            al = (f'<a class="cf-chip" href="{au[0]}" target="_blank" rel="noopener">'
                  f'{_CF_LISTEN_I}<span>Listen</span></a>' if au else '')
            chips = (f'<div class="cf-chips">{rl}{al}</div>' if (rl or al) else '')
            o.append(f'<li class="cf-item"><label class="cf-check">'
                     f'<input type="checkbox" data-cf="{wid}">'
                     f'<span class="cf-title">{title}</span></label>'
                     f'<div class="cf-meta"><span class="cf-by">{by}</span></div>'
                     f'<div class="cf-note">{note}</div>{chips}</li>')
        o.append('</ul></section>')
    o.append('<p class="res-foot">The Fathers and Councils gathered here belong to the '
             '<em>undivided</em> early Church — the common inheritance of the Orthodox and the '
             'wider Christian world, not the property of any one later tradition. The texts are '
             'linked from free public-domain libraries (including the Catholic-run New Advent and '
             'the ecumenical CCEL, Wikisource and Early Christian Writings), which simply host the '
             'standard public-domain translations; the <em>Orthodox</em> reading of them is drawn '
             'from the Orthodox sources (OCA, GOARCH, OrthoChristian, Ancient Faith) linked in the '
             'Topics. Audio is from LibriVox and other free sources; a few modern books link to the '
             'publisher.</p>')
    if ornament:
        o.append(art(ornament, foot=True))
    o.append('</section>')
    return "\n".join(o)


# Resources hub: topics grouped into sections and shown as a hairline-divided
# browse list (deliberately unlike the Prayers cycle — browsing, not praying)
RES_GROUPS = [
    ("The Faith", [
        ("The Theotokos", "theotokos.html", "Who the Church confesses Mary to be — and why.", "mono"),
        ("The Priesthood", "priesthood.html", "The threefold ministry, and what the Church asks of a priest.", "cross"),
        ("The Creeds", "creeds.html", "The Church's confessions of faith, in a few lines.", "roundel"),
    ]),
    ("History &amp; Scripture", [
        ("The Ecumenical Councils", "councils.html", "The seven councils that shaped the faith, and those after.", "cross"),
        ("The Bible &amp; Its Canon", "bible.html", "How the Church received the Scriptures — canon, Septuagint, the books.", "gospel"),
        ("The Early Church Fathers", "fathers.html", "A reading checklist by era, with text and audio.", "chirho"),
    ]),
    ("Going Deeper", [
        ("Catechisms", "catechisms.html", "Ordered introductions to the whole faith.", "chirho"),
        ("Recommended Reading", "reading.html", "A few books to go deeper.", "rule"),
    ]),
    ("For Your Phone", [
        ("The Church Calendar", "calendar.html", "Feast days for your phone — old- and new-calendar downloads.", "cal"),
    ]),
]


def _emblem(kind):
    return f'<span class="res-card-emblem" aria-hidden="true">{ORN[kind][0]}</span>'


# the red woodcut icons recoloured to follow the chosen primary colour: the ink
# becomes a CSS mask filled with --rubric, so it tracks the theme (the hatching
# is preserved as the mask's alpha). Mounted on a paper plate like a panel icon.
ICON_MASKS = [
    ("assets/img/icon_p1.png", "assets/img/icon_p1-mask.png", 760, 806),
    ("assets/img/icon_p15.png", "assets/img/icon_p15-mask.png", 820, 981),
]


def reicon(mask, w, h, alt):
    return (f'<span class="reframe"><span class="reicon" role="img" aria-label="{alt}" '
            f'style="--m:url({mask}); aspect-ratio:{w}/{h}"></span></span>')


def gen_icon_masks():
    """Turn the opaque red-on-white woodcuts into alpha masks (ink → alpha) so
    CSS can fill them with the live accent colour. Needs Pillow at build time;
    if absent, the committed masks are reused."""
    try:
        from PIL import Image, ImageChops, ImageOps
    except ImportError:
        print("Pillow not available — keeping existing icon masks"); return
    for src, dst, _w, _h in ICON_MASKS:
        if not os.path.exists(src):
            continue
        im = Image.open(src).convert("RGB")
        r, g, b = im.split()
        mn = ImageChops.darker(ImageChops.darker(r, g), b)   # per-pixel min channel
        alpha = ImageOps.autocontrast(ImageChops.invert(mn))  # 255-min, stretched
        out = Image.new("RGBA", im.size, (0, 0, 0, 0)); out.putalpha(alpha)
        out.save(dst)
    print("wrote icon masks", len(ICON_MASKS))


def hub_page():
    o = ['<section class="resources resources-hub" id="top">', _divider("Resources"),
         '<p class="res-intro">Explore the faith — by topic.</p>']
    for gname, cards in RES_GROUPS:
        o.append(f'<h2 class="browse-group">{gname}</h2>')
        o.append('<ul class="browse-list">')
        for c in cards:
            o.append(_browse_row(*c))
        o.append('</ul>')
    o.append(art("roundel", foot=True))
    o.append('</section>')
    return "\n".join(o)


# Prayers index — the hours of the day as a connected cycle (the current office
# is lit by time of day). title, href, blurb, emblem, time-label, hour-window
PRAYER_CYCLE = [
    ("Morning Prayers", "morning.html", "On rising — the morning rule.", "cross", "On rising", 4, 11),
    ("Prayers at Table", "table.html", "Blessings before and after meals.", "gospel", "At meals", None, None),
    ("Hours of the Day &amp; Night", "hours.html", "Through the hours of the day.", "chirho", "Through the day", 11, 21),
    ("Before Sleep", "sleep.html", "At the close of the day.", "roundel", "At nightfall", 21, 4),
]


def prayers_hub():
    o = ['<section class="resources prayers-hub" id="top">', _divider("Prayers"),
         '<p class="res-intro">The hours of the day — pray as each calls.</p>',
         _cycle(PRAYER_CYCLE)]
    if ANCIENT:
        o.append('<a class="hub-feature" href="ancient.html">'
                 f'{_emblem("roundel")}'
                 '<span class="hub-feature-body">'
                 '<span class="hub-feature-t">The Ancient Faith Prayer Book '
                 '<span class="pill pill-ancient pill-sm">Ancient</span></span>'
                 '<span class="hub-feature-d">A fuller cycle of daily offices — with prayers for '
                 'Communion, confession, the departed and many occasions.</span></span>'
                 f'{_CHEV_R}</a>')
    o.append(art("cross", foot=True))
    o.append(NOW_JS)
    o.append('</section>')
    return "\n".join(o)


# ---- The Ancient Faith Prayer Book (converted from the EPUB; opt-in) --------
# slug, page/menu title, short blurb for the hub cards
AFPB = [
    ("af-morning",      "Morning Prayers",                "On rising — the morning rule."),
    ("af-midday",       "Midday Prayers",                 "For the middle of the day."),
    ("af-meals",        "Prayers at Meals",               "Blessings before and after eating."),
    ("af-evening",      "Evening Prayers",                "The evening rule."),
    ("af-night",        "Prayers at the Close of Day",    "At the very end of the day."),
    ("af-precommunion", "Preparation for Holy Communion", "Prayers before receiving the Mysteries."),
    ("af-communion",    "Holy Communion",                 "At the reception of Communion."),
    ("af-thanksgiving", "Thanksgiving After Communion",   "Prayers of thanksgiving."),
    ("af-confession",   "Before Confession",              "In preparation for confession."),
    ("af-departed",     "Prayers for the Departed",       "For those who have fallen asleep."),
    ("af-occasions",    "Prayers for Various Occasions",  "For many needs and times of life."),
    ("af-saints",       "Prayers to the Saints",          "Troparia and prayers to the saints."),
]
AFPB_TITLES = {slug: title for slug, title, _ in AFPB}

PILL = '<span class="pill pill-ancient">Ancient Faith Prayer Book</span>'

# the Christ-the-Teacher icon, moved here from the foot of Morning Prayers
CHRIST_FIG = ('<figure class="icon">'
              + reicon("assets/img/icon_p15-mask.png", 820, 981, "Icon of Christ the Teacher")
              + '<figcaption>Christ the Teacher</figcaption></figure>')

_ancient_src = open("ancient.content.html").read() if os.path.exists("ancient.content.html") else ""
_ancient_src = _drawn_crosses(_ancient_src)
_amarks = list(re.finditer(r'<section class="divider afpb" id="(af-[a-z]+)">', _ancient_src))
ANCIENT = {}
for _ai, _am in enumerate(_amarks):
    _aend = _amarks[_ai + 1].start() if _ai + 1 < len(_amarks) else len(_ancient_src)
    ANCIENT[_am.group(1)] = _ancient_src[_am.start():_aend]


# the five offices of the AFPB daily cycle, with time-of-day windows; emblem
AFPB_CYCLE = {
    "af-morning": ("On rising", 4, 11, "cross"),
    "af-midday":  ("Midday", 11, 16, "chirho"),
    "af-meals":   ("At meals", None, None, "gospel"),
    "af-evening": ("Evening", 16, 21, "cross"),
    "af-night":   ("At nightfall", 21, 4, "roundel"),
}
# emblems for the remaining (sacraments & occasions) browse rows
AFPB_REST_EMB = {
    "af-precommunion": "chirho", "af-communion": "gospel", "af-thanksgiving": "chirho",
    "af-confession": "cross", "af-departed": "roundel", "af-occasions": "rule", "af-saints": "mono",
}


def afpb_hub():
    o = ['<section class="resources afpb-hub prayers-hub" id="top">',
         _divider("The Ancient Faith Prayer Book"),
         CHRIST_FIG,
         '<p class="res-intro">Prayers from <em>The Ancient Faith Prayer Book</em> '
         '(Ancient Faith Publishing). ' + PILL + '</p>']
    # the daily cycle (those offices that map to a time of day)
    cyc = []
    for slug, title, blurb in AFPB:
        if slug in AFPB_CYCLE and slug in ANCIENT:
            when, h0, h1, emb = AFPB_CYCLE[slug]
            cyc.append((title, f"{slug}.html", blurb, emb, when, h0, h1))
    if cyc:
        o.append('<h2 class="browse-group">The daily cycle</h2>')
        o.append(_cycle(cyc))
    # everything else — sacraments & occasions — as a browse list
    rest = [(t, f"{s}.html", b, AFPB_REST_EMB.get(s, "rule"))
            for s, t, b in AFPB if s not in AFPB_CYCLE and s in ANCIENT]
    if rest:
        o.append('<h2 class="browse-group">Sacraments &amp; occasions</h2>')
        o.append('<ul class="browse-list">')
        for row in rest:
            o.append(_browse_row(*row))
        o.append('</ul>')
    o.append(NOW_JS)
    o.append('</section>')
    return "\n".join(o)


# downloadable / subscribable liturgical calendars (generated by generate_calendars.py)
CAL_FILES = [
    ("New (Revised Julian) calendar", "orthodox-new-calendar.ics",
     "Used by most Orthodox churches (Greek, Antiochian, the OCA, Romanian, Bulgarian…). "
     "Fixed feasts fall on their familiar dates — Nativity on December 25, Theophany on January 6."),
    ("Old (Julian) calendar", "orthodox-old-calendar.ics",
     "Used by the Russian, Serbian, Georgian, Jerusalem and Athonite churches. Fixed feasts fall "
     "thirteen days later — Nativity on January 7, Theophany on January 19."),
]


def calendar_page():
    o = ['<section class="resources" id="top">', BACK, _divider("The Church Calendar")]
    o.append('<p class="topic-intro">Add the Orthodox feasts and fasts to your phone or computer. '
             'Both calendars keep the <em>same</em> Pascha and moveable cycle — Orthodox Pascha is '
             'reckoned the same way by all — and differ only in the fixed feasts: the Old (Julian) '
             'calendar observes them thirteen days after the New (Revised Julian) calendar. Choose '
             'the one your parish follows.</p>')
    o.append('<p class="topic-intro">Each fasting day is labelled with the <em>kind</em> of fast — '
             'strict, wine &amp; oil, fish, or fast-free — so you can see at a glance what is kept. '
             'These are the customary guidelines; the exact discipline varies by jurisdiction, so '
             'follow your parish and your spiritual father.</p>')
    o.append('<div class="cal-set">')
    for title, fn, blurb in CAL_FILES:
        o.append('<div class="cal-card">'
                 f'<h3>{title}</h3><p>{blurb}</p>'
                 '<div class="cal-actions">'
                 f'<a class="cal-btn sub" data-sub="{fn}" href="calendars/{fn}">Subscribe (auto-updating)</a>'
                 f'<a class="cal-btn dl" href="calendars/{fn}" download>Download .ics</a>'
                 '</div></div>')
    o.append('</div>')
    o.append('<div class="cal-how"><h3 class="subhead">How to add it</h3><ul>'
             '<li><strong>iPhone / iPad:</strong> tap <em>Subscribe</em> and confirm — it stays '
             'up to date automatically. (Or Settings → Calendar → Accounts → Add Subscribed '
             'Calendar, and paste the link.)</li>'
             '<li><strong>Google Calendar:</strong> on a computer, “Other calendars” → <em>From '
             'URL</em>, and paste the Subscribe link (copy it from the button).</li>'
             '<li><strong>Outlook:</strong> Add calendar → <em>Subscribe from web</em>, and paste '
             'the link.</li>'
             '<li><strong>One-time import (no updates):</strong> use <em>Download .ics</em> and '
             'open the file in your calendar app.</li></ul></div>')
    o.append('<p class="res-foot">Includes the Twelve Great Feasts and Pascha; the pre-Lenten, '
             'Lenten and Paschal Sundays; the four fasting seasons (Great Lent, Apostles’, '
             'Dormition and Nativity), the year-round Wednesday &amp; Friday fast, and the '
             'fast-free weeks; and many feasts of the saints (moveable dates computed for '
             '2025–2045). Dates are generated from public liturgical reckoning — for the daily '
             'saints and the precise fasting rule, always defer to your own parish calendar.</p>')
    o.append(art("cal", foot=True))
    o.append('</section>')
    return "\n".join(o)


# sets each "Subscribe" button to a webcal:// link for this host (auto-detected)
CAL_JS = '''<script>
(function(){var h=location.host;Array.prototype.forEach.call(
document.querySelectorAll('a.cal-btn.sub'),function(a){
a.href="webcal://"+h+"/calendars/"+a.getAttribute("data-sub");});})();
</script>'''

GREEK_JS = '<script src="greek-tool.js?v=7" defer></script>'


def greek_page():
    return "\n".join([
        '<section class="resources" id="top">', BACK, _divider("Greek Photo Translator"),
        '<p class="topic-intro">Take or choose a photo of Greek text and this will read it and '
        'translate it. It <strong>needs an internet connection</strong>, and works best on '
        '<strong>clear, straight-on, well-lit printed Greek</strong>. Stylised icon lettering, '
        'calligraphy and heavy accents are often misread — when that happens, correct the text in '
        'the box and translate again, or open it in Google Translate for the best result.</p>',
        '<div class="gk">',
        # capture zone — doubles as the empty state
        f'<label class="gk-drop" for="gk-file"><span class="gk-drop-i" aria-hidden="true">{CAMERA}</span>'
        '<span class="gk-drop-t">Take or choose a photo</span>'
        '<span class="gk-drop-d">Clear, straight-on, well-lit printed Greek works best</span></label>',
        '<input id="gk-file" type="file" accept="image/*" hidden>',
        '<img id="gk-img" class="gk-img" alt="Your photo" hidden>',
        '<div class="gk-status-row"><span id="gk-spin" class="gk-spin" aria-hidden="true" hidden></span>'
        '<p id="gk-status" class="gk-status" aria-live="polite"></p></div>',
        # result cards
        '<div class="gk-card gk-card-greek">'
        '<div class="gk-card-h">Greek <span class="gk-hint">(correct it if the reading is off)</span></div>'
        '<textarea id="gk-greek" class="gk-greek" rows="3" dir="auto" '
        'placeholder="Greek text appears here — or type it in"></textarea>'
        '<button id="gk-go" class="gk-mini" type="button">Translate again</button></div>',
        '<div class="gk-card gk-card-translit">'
        '<div class="gk-card-h">Transliteration</div>'
        '<p id="gk-translit" class="gk-translit"></p></div>',
        '<div class="gk-card gk-card-en">'
        '<div class="gk-card-h">English <span class="gk-hint">(rough)</span></div>'
        '<p id="gk-en" class="gk-en"></p>'
        '<a id="gk-gt" class="gk-cta" target="_blank" rel="noopener" hidden>Open in Google Translate</a></div>',
        '</div>',
        '<p class="res-foot">Text recognition runs in your browser (open-source); the rough '
        'translation uses a free public service, and the button above hands the text to Google '
        'Translate for a much better rendering. None is perfect — for careful study, compare with a '
        'printed translation. This is the one part of the app that reaches the internet.</p>',
        art("gospel", foot=True),
        '</section>'])


# ---- scripts ---------------------------------------------------------------
EARLY_JS = '''<script>
(function(){var r=document.documentElement,L=localStorage,t=L.getItem("theme"),s=L.getItem("size"),f=L.getItem("font");
if(t==="dark"||t==="light")r.dataset.theme=t;else if(window.matchMedia&&matchMedia("(prefers-color-scheme:dark)").matches)r.dataset.theme="dark";
if(s)r.dataset.size=s;if(f==="dyslexic")r.dataset.font="dyslexic";
var cool=L.getItem("temp")==="cool";if(cool)r.dataset.temp="cool";
var pc=L.getItem("primary");if(pc)r.dataset.primary=pc;
var sc=L.getItem("secondary");if(sc)r.dataset.secondary=sc;
var dk=r.dataset.theme==="dark";
var tc=document.getElementById("tc");if(tc)tc.setAttribute("content",dk?(cool?"#121317":"#161518"):(cool?"#f4f5f7":"#faf6ee"));})();
</script>'''

CONTROL_JS = '''<script>
(function(){
  var r=document.documentElement, d=document, L=localStorage;
  var backdrop=d.getElementById("menu-backdrop");
  // each pop-up sheet, paired with the tab button that opens it
  var sheets=[["settings-btn","menu"]]
    .map(function(p){ return {btn:d.getElementById(p[0]), el:d.getElementById(p[1])}; })
    .filter(function(s){ return s.btn && s.el; });
  function setOpen(s,o){ s.el.classList.toggle("open",o); s.btn.setAttribute("aria-expanded", o?"true":"false"); }
  function hideAll(){ sheets.forEach(function(s){ setOpen(s,false); });
    backdrop.classList.remove("open"); r.classList.remove("menu-open"); }
  function show(s){ sheets.forEach(function(x){ if(x!==s) setOpen(x,false); });
    setOpen(s,true); backdrop.classList.add("open"); r.classList.add("menu-open"); }
  sheets.forEach(function(s){
    s.btn.addEventListener("click", function(e){ e.stopPropagation();
      if(s.el.classList.contains("open")) hideAll(); else show(s); });
    var cb=s.el.querySelector(".drawer-close");
    if(cb) cb.addEventListener("click", hideAll);
    Array.prototype.forEach.call(s.el.querySelectorAll(".drawer-link"), function(a){
      a.addEventListener("click", hideAll); });
    var sy=null, dy=0;
    var atTop=true;
    s.el.addEventListener("touchstart", function(e){ sy=e.touches[0].clientY; dy=0; atTop=s.el.scrollTop<=0; s.el.style.transition="none"; }, {passive:true});
    // only drag-to-dismiss when the sheet is scrolled to the top, so swiping
    // down to scroll the content doesn't drag the whole sheet
    s.el.addEventListener("touchmove", function(e){ if(sy===null) return; dy=e.touches[0].clientY-sy; if(atTop && dy>0) s.el.style.transform="translateY("+dy+"px)"; }, {passive:true});
    s.el.addEventListener("touchend", function(){ s.el.style.transition=""; s.el.style.transform=""; if(atTop && dy>70) hideAll(); sy=null; });
  });
  backdrop.addEventListener("click", hideAll);
  d.addEventListener("keydown", function(e){ if(e.key==="Escape") hideAll(); });

  var sizes=["","l","xl"];
  function cur(){ return Math.max(0, sizes.indexOf(r.dataset.size||"")); }
  function setSize(i){ i=Math.max(0,Math.min(sizes.length-1,i)); var v=sizes[i];
    if(v){ r.dataset.size=v; L.setItem("size",v); } else { delete r.dataset.size; L.removeItem("size"); } }
  d.getElementById("size-up").onclick=function(){ setSize(cur()+1); };
  d.getElementById("size-dn").onclick=function(){ setSize(cur()-1); };

  var tl=d.getElementById("theme-light"), td=d.getElementById("theme-dark"), tc=d.getElementById("tc");
  function paintTC(){ if(!tc) return; var dark=r.dataset.theme==="dark", cool=r.dataset.temp==="cool";
    tc.setAttribute("content", dark?(cool?"#121317":"#161518"):(cool?"#f4f5f7":"#faf6ee")); }
  function paintTheme(){ var dark=r.dataset.theme==="dark";
    td.setAttribute("aria-pressed", dark?"true":"false");
    tl.setAttribute("aria-pressed", dark?"false":"true"); paintTC(); }
  tl.onclick=function(){ r.dataset.theme="light"; L.setItem("theme","light"); paintTheme(); };
  td.onclick=function(){ r.dataset.theme="dark";  L.setItem("theme","dark");  paintTheme(); };

  // background temperature (warm is the default; cool tints the page cooler)
  var twb=d.getElementById("temp-warm"), tcb=d.getElementById("temp-cool");
  function paintTemp(){ var cool=r.dataset.temp==="cool";
    if(tcb) tcb.setAttribute("aria-pressed", cool?"true":"false");
    if(twb) twb.setAttribute("aria-pressed", cool?"false":"true"); paintTC(); }
  function setTemp(v){ if(v==="cool"){ r.dataset.temp="cool"; L.setItem("temp","cool"); }
    else { delete r.dataset.temp; L.setItem("temp","warm"); } paintTemp(); }
  if(twb) twb.onclick=function(){ setTemp("warm"); };
  if(tcb) tcb.onclick=function(){ setTemp("cool"); };

  // primary / secondary colour swatches (Tailwind families; "" = brand default)
  var swatches=d.querySelectorAll(".swatch");
  function pickName(k){ var c=L.getItem(k)||""; return c?c.charAt(0).toUpperCase()+c.slice(1):"Default"; }
  function paintSwatches(){
    Array.prototype.forEach.call(swatches,function(b){
      var k=b.getAttribute("data-k"), c=b.getAttribute("data-c")||""; var cur=L.getItem(k)||"";
      b.setAttribute("aria-pressed", c===cur?"true":"false"); });
    var pp=d.getElementById("primary-pick"), sp=d.getElementById("secondary-pick");
    if(pp) pp.textContent=pickName("primary"); if(sp) sp.textContent=pickName("secondary"); }
  Array.prototype.forEach.call(swatches,function(b){ b.onclick=function(){
    var k=b.getAttribute("data-k"), c=b.getAttribute("data-c")||"";
    if(c){ r.dataset[k]=c; L.setItem(k,c); } else { delete r.dataset[k]; L.removeItem(k); }
    paintSwatches(); }; });
  // reset all appearance choices back to the brand default
  var rst=d.getElementById("appearance-reset");
  if(rst) rst.onclick=function(){
    delete r.dataset.primary; L.removeItem("primary");
    delete r.dataset.secondary; L.removeItem("secondary");
    delete r.dataset.temp; L.setItem("temp","warm");
    paintSwatches(); paintTemp(); };

  var dys=d.getElementById("dys");
  function paintDys(){ dys.setAttribute("aria-checked", r.dataset.font==="dyslexic"?"true":"false"); }
  dys.onclick=function(){ if(r.dataset.font==="dyslexic"){ delete r.dataset.font; L.setItem("font","serif"); }
    else { r.dataset.font="dyslexic"; L.setItem("font","dyslexic"); } paintDys(); };

  // reading-checklist progress (saved per device)
  var boxes=d.querySelectorAll('input[type=checkbox][data-cf]');
  function progress(){ if(!boxes.length) return; var done=0;
    Array.prototype.forEach.call(boxes,function(c){ if(c.checked) done++; });
    var p=d.getElementById("cf-progress"); if(p) p.textContent=done+" of "+boxes.length+" read";
    var b=d.getElementById("cf-bar"); if(b) b.style.width=(100*done/boxes.length)+"%"; }
  Array.prototype.forEach.call(boxes,function(cb){
    var k="cf:"+cb.getAttribute("data-cf");
    if(L.getItem(k)==="1") cb.checked=true;
    cb.addEventListener("change",function(){ if(cb.checked) L.setItem(k,"1"); else L.removeItem(k); progress(); }); });
  progress();

  // follow the Church calendar (off / new / old)
  var calMap=[["off","cal-off"],["new","cal-new"],["old","cal-old"]];
  function paintCal(){ var v=L.getItem("cal")||"off";
    calMap.forEach(function(p){ var b=d.getElementById(p[1]); if(b) b.setAttribute("aria-pressed", p[0]===v?"true":"false"); }); }
  function setCal(v){ if(v==="off") L.removeItem("cal"); else L.setItem("cal",v); paintCal(); if(window.OCsync) window.OCsync(); }
  calMap.forEach(function(p){ var b=d.getElementById(p[1]); if(b) b.onclick=function(){ setCal(p[0]); }; });

  // fast-day reminders (in-app; fires when the app is opened on a fast day)
  var fn=d.getElementById("fastnotify");
  function paintFn(){ if(fn) fn.setAttribute("aria-checked", L.getItem("fastnotify")==="1"?"true":"false"); }
  if(fn) fn.onclick=function(){
    if(L.getItem("fastnotify")==="1"){ L.setItem("fastnotify","0"); paintFn(); return; }
    if(window.Notification && Notification.requestPermission){
      Notification.requestPermission().then(function(perm){
        L.setItem("fastnotify", perm==="granted"?"1":"0"); paintFn(); if(window.OCsync) window.OCsync(); });
    } else { L.setItem("fastnotify","0"); paintFn(); }
  };

  // available offline (registers a service worker that caches the whole app)
  var swOk=("serviceWorker" in navigator);
  var offBtn=d.getElementById("offline"), offNote=d.getElementById("offline-note");
  function paintOff(){ if(offBtn) offBtn.setAttribute("aria-checked", L.getItem("offline")==="1"?"true":"false"); }
  function clearCaches(){ if(window.caches) caches.keys().then(function(ks){
    ks.forEach(function(k){ if(k.indexOf("ortho-")===0) caches.delete(k); }); }); }
  if(offBtn){
    if(!swOk){ offBtn.setAttribute("disabled","true"); if(offNote) offNote.textContent="Offline use isn’t supported by this browser."; }
    offBtn.onclick=function(){
      if(!swOk) return;
      if(L.getItem("offline")==="1"){
        L.setItem("offline","0"); paintOff();
        navigator.serviceWorker.getRegistrations().then(function(rs){ rs.forEach(function(r){ r.unregister(); }); });
        clearCaches();
      } else {
        L.setItem("offline","1"); paintOff();
        navigator.serviceWorker.register("sw.js");
      }
    };
  }
  if(swOk && L.getItem("offline")==="1") navigator.serviceWorker.register("sw.js");

  // centre camera button: open the camera, downscale the photo, then hand it
  // to the Greek translator page (auto-processed there)
  var camBtn=d.getElementById("cam-btn"), cam=d.getElementById("cam-input");
  if(camBtn && cam){
    camBtn.onclick=function(){ cam.value=""; cam.click(); };
    cam.addEventListener("change", function(){
      var f=cam.files && cam.files[0]; if(!f) return;
      var im=new Image(), u=URL.createObjectURL(f);
      im.onload=function(){
        var mx=1600, s=Math.min(1, mx/Math.max(im.width, im.height));
        var c=d.createElement("canvas"); c.width=Math.round(im.width*s); c.height=Math.round(im.height*s);
        c.getContext("2d").drawImage(im,0,0,c.width,c.height); URL.revokeObjectURL(u);
        try{ sessionStorage.setItem("gk-photo", c.toDataURL("image/jpeg",0.8)); }catch(e){}
        location.href="greek.html";
      };
      im.onerror=function(){ URL.revokeObjectURL(u); location.href="greek.html"; };
      im.src=u;
    });
  }

  paintTheme(); paintTemp(); paintSwatches(); paintDys(); paintCal(); paintFn(); paintOff();
})();
</script>'''

# service worker: precache the whole app for offline use (opt-in via Settings).
# __VERSION__ / __ASSETS__ are filled at build time. Cross-origin (external
# links) are left to the network; same-origin is cache-first.
SW_TMPL = '''const CACHE="ortho-__VERSION__";
const ASSETS=__ASSETS__;
self.addEventListener("install", function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(ASSETS); })
    .then(function(){ return self.skipWaiting(); }));
});
self.addEventListener("activate", function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.map(function(k){ if(k!==CACHE && k.indexOf("ortho-")===0) return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});
self.addEventListener("fetch", function(e){
  var req=e.request;
  if(req.method!=="GET") return;
  if(new URL(req.url).origin!==location.origin) return;   // external links use the network
  e.respondWith(caches.match(req, {ignoreSearch:true}).then(function(hit){
    if(hit) return hit;
    return fetch(req).then(function(res){
      if(res && res.status===200 && res.type==="basic"){
        var copy=res.clone(); caches.open(CACHE).then(function(c){ c.put(req, copy); });
      }
      return res;
    }).catch(function(){
      if(req.mode==="navigate") return caches.match("index.html");
      return Response.error();
    });
  }));
});
'''

# ---- user theming: Tailwind palette for primary/secondary colour pickers ----
# shades used: 400/500 (dark accents + swatch dots), 600 (secondary light),
# 700/800 (primary light + deep). Values are Tailwind v3.
TW = {
 "red":     {"400": "#f87171", "500": "#ef4444", "600": "#dc2626", "700": "#b91c1c", "800": "#991b1b"},
 "orange":  {"400": "#fb923c", "500": "#f97316", "600": "#ea580c", "700": "#c2410c", "800": "#9a3412"},
 "amber":   {"400": "#fbbf24", "500": "#f59e0b", "600": "#d97706", "700": "#b45309", "800": "#92400e"},
 "yellow":  {"400": "#facc15", "500": "#eab308", "600": "#ca8a04", "700": "#a16207", "800": "#854d0e"},
 "lime":    {"400": "#a3e635", "500": "#84cc16", "600": "#65a30d", "700": "#4d7c0f", "800": "#3f6212"},
 "green":   {"400": "#4ade80", "500": "#22c55e", "600": "#16a34a", "700": "#15803d", "800": "#166534"},
 "emerald": {"400": "#34d399", "500": "#10b981", "600": "#059669", "700": "#047857", "800": "#065f46"},
 "teal":    {"400": "#2dd4bf", "500": "#14b8a6", "600": "#0d9488", "700": "#0f766e", "800": "#115e59"},
 "cyan":    {"400": "#22d3ee", "500": "#06b6d4", "600": "#0891b2", "700": "#0e7490", "800": "#155e75"},
 "sky":     {"400": "#38bdf8", "500": "#0ea5e9", "600": "#0284c7", "700": "#0369a1", "800": "#075985"},
 "blue":    {"400": "#60a5fa", "500": "#3b82f6", "600": "#2563eb", "700": "#1d4ed8", "800": "#1e40af"},
 "indigo":  {"400": "#818cf8", "500": "#6366f1", "600": "#4f46e5", "700": "#4338ca", "800": "#3730a3"},
 "violet":  {"400": "#a78bfa", "500": "#8b5cf6", "600": "#7c3aed", "700": "#6d28d9", "800": "#5b21b6"},
 "purple":  {"400": "#c084fc", "500": "#a855f7", "600": "#9333ea", "700": "#7e22ce", "800": "#6b21a8"},
 "fuchsia": {"400": "#e879f9", "500": "#d946ef", "600": "#c026d3", "700": "#a21caf", "800": "#86198f"},
 "pink":    {"400": "#f472b6", "500": "#ec4899", "600": "#db2777", "700": "#be185d", "800": "#9d174d"},
 "rose":    {"400": "#fb7185", "500": "#f43f5e", "600": "#e11d48", "700": "#be123c", "800": "#9f1239"},
 "slate":   {"400": "#94a3b8", "500": "#64748b", "600": "#475569", "700": "#334155", "800": "#1e293b"},
}
TW_ORDER = ["red", "orange", "amber", "yellow", "lime", "green", "emerald", "teal", "cyan",
            "sky", "blue", "indigo", "violet", "purple", "fuchsia", "pink", "rose", "slate"]
# the app's own identity, shown as the "Default" swatch (data-c="")
BRAND_PRIMARY = "#b3322a"   # cinnabar
BRAND_SECONDARY = "#9a7b1e" # gold


def _lum(hx):
    """WCAG relative luminance of a #rrggbb colour (0–1)."""
    h = hx.lstrip("#"); ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4) for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def _on(hx):
    """Readable text colour to place on a fill of hx (the contrast guard)."""
    return "#1b1b1b" if _lum(hx) > 0.45 else "#ffffff"


def themes_css():
    """Generated stylesheet: background temperature + Tailwind primary/secondary."""
    o = ["/* generated by build.py — user theming (do not edit by hand) */",
         "/* background temperature: warm is the styles.css default; cool tints cooler */",
         ('html[data-temp="cool"]{ --paper:#f4f5f7; --surface:#ffffff; --surface-sunk:#e9ecf1;'
          ' --desk:#dfe3ea; --hairline:#dde1e8; --hairline-strong:#c7cdd8; }'),
         ('html[data-theme="dark"][data-temp="cool"]{ --paper:#121317; --surface:#1b1d22;'
          ' --surface-sunk:#0e0f12; --desk:#0a0b0d; --hairline:#2c2f37; --hairline-strong:#3c404a; }'),
         "/* primary colour (accent: titles, active state, buttons, FAB) */"]
    for fam in TW_ORDER:
        c = TW[fam]
        # --on-rubric: text colour for fills of --rubric (contrast guard — light
        # hues like yellow/lime need dark text instead of white)
        o.append(f'html[data-primary="{fam}"]{{ --rubric:{c["700"]}; --rubric-deep:{c["800"]}; --on-rubric:{_on(c["700"])}; }}')
        o.append(f'html[data-theme="dark"][data-primary="{fam}"]{{ --rubric:{c["400"]}; --rubric-deep:{c["500"]}; --on-rubric:{_on(c["400"])}; }}')
    o.append("/* secondary colour (gilding accent) */")
    for fam in TW_ORDER:
        c = TW[fam]
        # --on-gold: readable text/mark colour on a --gold fill (the Ancient pill,
        # the lit office node) — dark secondaries need light text and vice-versa
        o.append(f'html[data-secondary="{fam}"]{{ --gold:{c["600"]}; --on-gold:{_on(c["600"])}; }}')
        o.append(f'html[data-theme="dark"][data-secondary="{fam}"]{{ --gold:{c["400"]}; --on-gold:{_on(c["400"])}; }}')
    return "\n".join(o) + "\n"


def _swatches(kind, default_hex):
    """A horizontally-scrolling row of colour dots for the settings sheet."""
    o = [f'<div class="swatches" role="group" aria-label="{kind} colour">',
         (f'<button class="swatch swatch-default" type="button" data-k="{kind}" data-c="" '
          f'style="--sw:{default_hex}" title="Default" aria-label="Default" aria-pressed="true"></button>')]
    for fam in TW_ORDER:
        o.append(f'<button class="swatch" type="button" data-k="{kind}" data-c="{fam}" '
                 f'style="--sw:{TW[fam]["500"]}" title="{fam.capitalize()}" '
                 f'aria-label="{fam}" aria-pressed="false"></button>')
    o.append('</div>')
    return "\n".join(o)


HEAD_TMPL = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="favicon.ico?v=7" sizes="32x32">
<link rel="icon" type="image/png" sizes="32x32" href="assets/icons/favicon-32.png?v=7">
<link rel="icon" type="image/png" sizes="16x16" href="assets/icons/favicon-16.png?v=7">
<link rel="apple-touch-icon" href="assets/icons/apple-touch-icon.png?v=7">
<link rel="manifest" href="site.webmanifest?v=7">
<meta name="apple-mobile-web-app-title" content="Prayers">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" id="tc" content="#faf6ee">
<link rel="stylesheet" href="styles.css">
<link rel="stylesheet" href="themes.css?v=1">
{early}
</head>
<body>
<div class="scroll">
<main class="book">
{body}
</main>
</div>
{topnav}
{control}
<script src="calendar-data.js?v=1" defer></script>
<script src="calendar.js?v=3" defer></script>
{scripts}
</body>
</html>
'''


def page(path, title, desc, body, active="", scripts=""):
    # gild the single page-opening drop-cap (the grandest initial)
    body = body.replace('<span class="dropcap">', '<span class="dropcap gilt">', 1)
    html = HEAD_TMPL.format(title=title, desc=desc, body=body, topnav=tabbar(active, path),
                            control=CONTROL_JS, early=EARLY_JS, scripts=scripts)
    open(path, "w").write(html)
    print("wrote", path, len(html), "bytes")


# split the prayer content into one page per prayer time, at the section dividers
_marks = list(re.finditer(r'<section class="divider[^"]*" id="(morning|table|hours|sleep)">', content))
PRAYERS = {}
for _i, _m in enumerate(_marks):
    _end = _marks[_i + 1].start() if _i + 1 < len(_marks) else len(content)
    PRAYERS[_m.group(1)] = content[_m.start():_end]

# --- per-page "jump to" nav: chips that link to the sections within a prayer page ---
_TITLE_RE = re.compile(
    r'^(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\s+prayer'
    r'|^(a|two)\s+(prayer|prayers|song|songs)\b'
    r'|^morning prayer\b'
    r'|^prayers?\s+(of|at|for|before|throughout)\b'
    r'|^the symbol of faith\b|^psalm\b', re.I)


def _label(inner):
    # join the title lines, but stop at an attribution ("by …") or parenthetical
    out = []
    for ln in re.split(r'<br\s*/?>', inner):
        t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', ln)).strip()
        if not t:
            continue
        if out and re.match(r'^(by\b|\()', t, re.I):
            break
        out.append(t)
    lab = " ".join(out)
    lab = re.sub(r'\s*:?\s*by the same\b.*$', '', lab, flags=re.I).strip().rstrip(':').strip()
    return lab


def with_jump_nav(seg):
    targets = []
    cnt = [0]

    def nid():
        cnt[0] += 1
        return f'j{cnt[0]}'

    def on_h2(m):
        inner = m.group(1)
        lab = re.sub(r'^(at the |at |after the |after )', '', _label(inner), flags=re.I).strip() or _label(inner)
        sid = nid(); targets.append((sid, lab))
        return f'<h2 class="subhead" id="{sid}">{inner}</h2>'

    seg = re.sub(r'<h2 class="subhead">(.*?)</h2>', on_h2, seg, flags=re.S)

    def on_rub(m):
        inner = m.group(1)
        lab = _label(inner)
        if not _TITLE_RE.search(lab):
            return m.group(0)
        sid = nid(); targets.append((sid, lab))
        return f'<p class="rubric" id="{sid}">{inner}</p>'

    seg = re.sub(r'<p class="rubric">(.*?)</p>', on_rub, seg, flags=re.S)
    if len(targets) < 2:
        return seg
    chips = "".join(f'<a href="#{sid}">{lab}</a>' for sid, lab in targets)
    nav = f'<nav class="page-toc" aria-label="On this page">{chips}</nav>'
    parts = seg.split('</section>', 1)               # place after the section title
    return (parts[0] + '</section>\n' + nav + parts[1]) if len(parts) == 2 else nav + seg


PLAYER = '<script src="player.js?v=5" defer></script>'

# home / landing page
page("index.html", "Prayers for Morning, Day &amp; Night",
     "An Orthodox prayer book and companion for the journey — daily prayers for morning, the "
     "table, the hours of the day and night, and before sleep, with resources for inquirers "
     "coming from Western Protestant Christianity to Orthodoxy.",
     LANDING.format(cross=CLOSING, rule=RULE_FIG, pray_js=HOME_JS), active="home")

# Prayers index (card hub; replaces the old slide-up Prayers menu)
page("prayers.html", "Prayers — Daily Prayers",
     "The daily Orthodox prayers — morning, at the table, the hours of the day and night, before "
     "sleep, and the Ancient Faith Prayer Book.",
     prayers_hub(), active="prayers")

# one page per prayer time (read-aloud player on each)
PRAYER_PAGES = [("morning", "Morning Prayers"), ("table", "Prayers at Table"),
                ("hours", "Prayers for the Hours of the Day & Night"), ("sleep", "Prayers Before Sleep")]
for slug, title in PRAYER_PAGES:
    page(f"{slug}.html", f"{title} — Daily Prayers",
         f"{title}: a web edition of the St. Tikhon's Monastery Press / OCA daily-prayers booklet.",
         back_link("prayers.html", "All prayers") + with_jump_nav(_headpiece(PRAYERS[slug])) + CLOSING,
         active="prayers", scripts=PLAYER)

# The Ancient Faith Prayer Book: a hub + one page per office (read-aloud on each)
if ANCIENT:
    page("ancient.html", "The Ancient Faith Prayer Book — Daily Prayers",
         "Prayers from The Ancient Faith Prayer Book (Ancient Faith Publishing): "
         "morning, midday, evening and night prayers, Holy Communion, confession and more.",
         afpb_hub(), active="prayers")
    _credit = f'<p class="afpb-credit">{PILL}</p>'
    for slug, title, blurb in AFPB:
        if slug not in ANCIENT:
            continue
        body = with_jump_nav(_headpiece(ANCIENT[slug])).replace('</section>\n', '</section>\n' + _credit, 1)
        page(f"{slug}.html", f"{title} — The Ancient Faith Prayer Book",
             f"{title}, from The Ancient Faith Prayer Book (Ancient Faith Publishing).",
             back_link("ancient.html", "Prayer Book") + body + CLOSING, active="prayers", scripts=PLAYER)

# resources hub + a page per topic/section
page("resources.html", "Resources — Daily Prayers",
     "Topics, early-Church writings, creeds, councils, catechisms and recommended reading.",
     hub_page(), active="resources")

TOPIC_SLUGS = {"The Theotokos": "theotokos", "The Priesthood": "priesthood"}
TOPIC_ORN = {"The Theotokos": "mono", "The Priesthood": "cross"}
for t in TOPICS:
    page(f'{TOPIC_SLUGS[t["name"]]}.html', f'{t["name"]} — Daily Prayers',
         f'{t["name"]} in the Orthodox Church, with early-Church writings and trusted explanations.',
         topic_page(t, TOPIC_ORN[t["name"]]), active="resources")

page("fathers.html", "The Early Church Fathers — Daily Prayers",
     "A reading checklist of the early Church Fathers, with free text and audio links.",
     fathers_page("chirho"), active="resources")

page("calendar.html", "The Church Calendar — Daily Prayers",
     "Downloadable Orthodox calendars (Old/Julian and New/Revised Julian) for Google "
     "Calendar, Outlook and Apple Calendar — feasts, fasts and the Paschal cycle.",
     calendar_page(), active="resources", scripts=CAL_JS)

page("greek.html", "Greek Photo Translator — Daily Prayers",
     "Photograph Greek text and read it in English — on-device recognition with transliteration "
     "and translation. Online tool; results are approximate.",
     greek_page(), active="resources", scripts=GREEK_JS)

# in-depth articles (Councils, the Bible & its canon)
for _a in ARTICLES:
    page(f'{_a["slug"]}.html', f'{_a["name"]} — Daily Prayers',
         re.sub(r"<[^>]+>", "", _a["lead"])[:155], article_page(_a), active="resources")

REF_SLUGS = {"The Creeds": "creeds",
             "Catechisms": "catechisms", "Recommended Reading": "reading"}
REF_ORN = {"The Creeds": "chirho",
           "Catechisms": "roundel", "Recommended Reading": "rule"}
for ref in REF_SECTIONS:
    page(f'{REF_SLUGS[ref["name"]]}.html', f'{ref["name"]} — Daily Prayers',
         ref.get("blurb", "") or ref["name"], ref_page(ref, REF_ORN[ref["name"]]), active="resources")

# feast data for the client-side "This Week" panel + fast reminder (single source
# of truth: the lists in generate_calendars.py)
_caldata = {
    "fixed": [[m, dd, name, great] for (m, dd, name, great) in gc.FIXED],
    "moveable": [[off, name, great] for (off, name, great) in gc.MOVEABLE],
    "offset": gc.JULIAN_OFFSET,
}
open("calendar-data.js", "w").write("window.OC=" + json.dumps(_caldata, ensure_ascii=False) + ";\n")
print("wrote calendar-data.js", len(gc.FIXED), "fixed +", len(gc.MOVEABLE), "moveable")

# generated theming stylesheet (background temperature + Tailwind primary/secondary)
open("themes.css", "w").write(themes_css())
print("wrote themes.css", len(TW_ORDER), "colour families")

# recolourable masks for the red woodcut icons (so they follow the primary colour)
gen_icon_masks()

# ---- service worker: precache the whole app for offline use ----------------
# build inputs that are NOT deployed (see .vercelignore) — must never be listed,
# or cache.addAll() would 404 and the whole offline install would fail
_NODEPLOY = {"prayers.content.html", "ancient.content.html", "assets/icons/app-icon.png"}
_assets = {"./"}
_assets.update(glob.glob("*.html"))
for _p in ["styles.css", "themes.css", "player.js", "calendar.js", "calendar-data.js", "greek-tool.js",
           "site.webmanifest", "favicon.ico"]:
    if os.path.exists(_p):
        _assets.add(_p)
for _pat in ["fonts/*.woff2", "assets/img/*", "assets/icons/*", "calendars/*.ics"]:
    _assets.update(glob.glob(_pat))
_assets = sorted(a for a in _assets if a not in _NODEPLOY)
# cache version = hash of the cached files' contents, so a new deploy busts it
_h = hashlib.sha1()
for _p in _assets:
    if _p == "./":
        continue
    try:
        _h.update(open(_p, "rb").read())
    except OSError:
        pass
_sw = SW_TMPL.replace("__VERSION__", _h.hexdigest()[:10]) \
             .replace("__ASSETS__", json.dumps(_assets))
open("sw.js", "w").write(_sw)
print("wrote sw.js", len(_assets), "assets, cache", _h.hexdigest()[:10])
