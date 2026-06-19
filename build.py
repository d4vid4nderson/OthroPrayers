#!/usr/bin/env python3
"""Assemble index.html (the prayer booklet) and resources.html (the Resources
area, incl. the Early Church Fathers reading checklist) from a shared shell.
Run `python3 generate.py` first to (re)produce prayers.content.html."""

import os
import re
from urllib.parse import quote

content = open("prayers.content.html").read()
# one black, letter-spaced title the generator can't auto-clean (CSS spaces it)
content = re.sub(r"for\s+a\s+n\s+y\s+m\s+e\s+a\s+l", "for any meal", content)
# the Crucifixion banner is no longer displayed in the booklet pages
content = re.sub(r'<figure class="banner">.*?</figure>\s*', "", content, flags=re.S)
# mount the woodcut icon as a framed plate with a small-caps caption (from its alt)
content = re.sub(
    r'(<figure class="icon"><img[^>]*alt="(?:Icon of )?([^"]*)"[^>]*>)(\s*</figure>)',
    r'\1<figcaption>\2</figcaption>\3', content)

LANDING = '''<section class="cover landing" id="top">
  <figure class="coverimg">
    <img src="assets/img/icon_p1.png" width="742" height="787"
         alt="Icon of the Mother of God “of the Sign” (Znamenie)">
  </figure>
  <h1>PRAYERS <span class="i">for</span> MORNING,<br>DAY &amp; NIGHT</h1>
  <p class="landing-sub">An Orthodox prayer book &amp; companion for the journey</p>
  {rule}

  <div class="landing-body">
    <h2 class="landing-h">Coming Home to the Ancient Church</h2>
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

  <nav class="landing-cta" aria-label="Begin">
    <a class="cta" href="morning.html">Begin with Morning Prayers</a>
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
</section>'''

# inline SVG icons (stroke uses currentColor; no emoji)
HOME = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><path d="M3 11.5 12 4l9 7.5"/>'
        '<path d="M5 10v9a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-9"/><path d="M9.5 20v-5h5v5"/></svg>')
BOOK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><path d="M2 4h6a3 3 0 0 1 3 3v13a2.5 2.5 0 0 0-2.5-2.5H2z"/>'
        '<path d="M22 4h-6a3 3 0 0 0-3 3v13a2.5 2.5 0 0 1 2.5-2.5H22z"/></svg>')
COMPASS = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
           '<polygon points="16.2 7.8 13.4 13.4 7.8 16.2 10.6 10.6"/></svg>')
GEAR = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 '
        '1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 '
        '0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 '
        '0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 '
        '1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 '
        '2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 '
        '0-1.51 1z"/></svg>')
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

ORN = {
    "cross":   (ORTHODOX_CROSS, "Orthodox cross", "art-cross"),
    "roundel": (ICXC_ROUNDEL, "IC XC NIKA — the Cross of Christ Conquers", "art-roundel"),
    "mono":    (THEOTOKOS_MONO, "Mother of God (ΜΡ ΘΥ)", "art-mono"),
    "chirho":  (CHI_RHO, "Chi-Rho — the monogram of Christ, with Alpha and Omega", "art-chirho"),
    "rule":    (RULE, "Ornamental rule", "art-rule"),
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

# bottom tab bar (dedicated mobile nav): Home + Prayers/Resources pop-up
# sub-menus + the slide-up Settings sheet
TABBAR_TMPL = '''<nav class="tabbar" aria-label="Primary">
  <a class="tab{h_act}" href="index.html" aria-label="Home"><span class="tab-i">{HOME}</span><span class="tab-l">Home</span></a>
  <button class="tab{p_act}" id="prayers-btn" type="button" aria-haspopup="true" aria-expanded="false"
          aria-controls="prayers-menu" aria-label="Prayers"><span class="tab-i">{BOOK}</span><span class="tab-l">Prayers</span></button>
  <button class="tab{r_act}" id="resources-btn" type="button" aria-haspopup="true" aria-expanded="false"
          aria-controls="resources-menu" aria-label="Resources"><span class="tab-i">{COMPASS}</span><span class="tab-l">Resources</span></button>
  <button class="tab" id="settings-btn" type="button" aria-haspopup="true" aria-expanded="false"
          aria-controls="menu" aria-label="Settings"><span class="tab-i">{GEAR}</span><span class="tab-l">Settings</span></button>
</nav>
<div id="menu-backdrop" class="backdrop"></div>
<div id="prayers-menu" class="drawer" role="dialog" aria-modal="true" aria-label="Prayers">
  <div class="drawer-head">
    <span class="grab" aria-hidden="true"></span>
    <button class="drawer-close" type="button" aria-label="Close">{CLOSE}</button>
  </div>
  <div class="drawer-heading">Prayers</div>
  <nav class="drawer-nav" aria-label="Prayers">{prayer_links}</nav>
</div>
<div id="resources-menu" class="drawer" role="dialog" aria-modal="true" aria-label="Resources">
  <div class="drawer-head">
    <span class="grab" aria-hidden="true"></span>
    <button class="drawer-close" type="button" aria-label="Close">{CLOSE}</button>
  </div>
  <div class="drawer-heading">Resources</div>
  <nav class="drawer-nav" aria-label="Resources">{res_links}</nav>
</div>
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
    <span class="menu-label">Dyslexia-friendly</span>
    <button id="dys" class="switch" type="button" role="switch" aria-checked="false"
            aria-label="Dyslexia-friendly text"><span class="knob"></span></button>
  </div>
</div>'''


def _drawer_links(pairs, current):
    out = []
    for p in pairs:
        href, label = p[0], p[1]
        pill = p[2] if len(p) > 2 else ""
        here = href == current or (pill == "ancient" and current.startswith("af-"))
        cls = " active" if here else ""
        cur = ' aria-current="page"' if here else ""
        tag = ' <span class="pill pill-ancient pill-sm">Ancient</span>' if pill == "ancient" else ""
        out.append(f'<a class="drawer-link{cls}"{cur} href="{href}">{label}{tag}</a>')
    return "\n".join(out)


def tabbar(active="", current=""):
    prayer_pairs = [("morning.html", "Morning Prayers"), ("table.html", "Prayers at Table"),
                    ("hours.html", "Prayers for the Hours of the Day &amp; Night"),
                    ("sleep.html", "Prayers Before Sleep"),
                    ("ancient.html", "The Ancient Faith Prayer Book", "ancient")]
    res_pairs = [(href, name) for name, href, _ in RES_CARDS]
    return TABBAR_TMPL.format(
        h_act=" active" if active == "home" else "",
        p_act=" active" if active == "prayers" else "",
        r_act=" active" if active == "resources" else "",
        prayer_links=_drawer_links(prayer_pairs, current),
        res_links=_drawer_links(res_pairs, current),
        HOME=HOME, BOOK=BOOK, COMPASS=COMPASS, GEAR=GEAR, SUN=SUN, MOON=MOON, CLOSE=CLOSE)


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
 {"name": "The Ecumenical Councils", "blurb": "The canons and definitions of the Church gathered as one.",
  "items": [
    ("The Seven Ecumenical Councils (canons & decrees)", "https://ccel.org/ccel/schaff/npnf214.html",
     "Schaff's NPNF Vol. 14 — full canons and dogmatic decrees, with commentary."),
    ("Nicaea I (325)", "https://www.newadvent.org/fathers/3801.htm",
     "Against Arianism; the original Nicene Creed and twenty canons."),
    ("Constantinople I (381)", "https://www.newadvent.org/fathers/3808.htm",
     "Completes the Creed; the divinity of the Holy Spirit."),
    ("Ephesus (431)", "https://www.newadvent.org/fathers/3810.htm",
     "Mary as Theotokos; the unity of Christ."),
    ("Chalcedon (451)", "https://www.newadvent.org/fathers/3811.htm",
     "The Definition of the two natures of Christ, and thirty canons."),
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
    return (f'<section class="divider"><span class="cross">✠</span><h1>{title}</h1>'
            + RULE_FIG + '</section>')


def _links_ul(items):
    out = ['<ul class="ref-list">']
    for it in items:
        title, url, desc = it[0], it[1], it[2]
        free = len(it) > 3 and it[3]
        badge = ' <span class="ref-free">free</span>' if free else ''
        out.append(f'<li class="ref-item"><a class="ref-title" href="{url}" target="_blank" '
                   f'rel="noopener">{title}</a>{badge}<div class="cf-note">{desc}</div></li>')
    out.append('</ul>')
    return "\n".join(out)


BACK = '<a class="res-back" href="resources.html">&larr; All resources</a>'


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


def fathers_page(ornament=""):
    o = ['<section class="resources" id="papers">', BACK, _divider("The Early Church Fathers")]
    o.append('<p class="res-intro">A reading path through the first centuries of the Church — '
             'tick each work as you read or listen; your progress is saved on this device.</p>')
    hubs = " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in AUDIO_HUBS)
    o.append(f'<p class="cf-audiohubs">Listen free: {hubs}</p>')
    o.append('<p class="cf-progress-wrap"><span id="cf-progress">0 read</span>'
             '<span class="cf-track"><span id="cf-bar" class="cf-fill"></span></span></p>')
    for era in ERAS:
        o.append('<div class="cf-era">')
        o.append(f'<h3>{era["name"]} <span class="cf-dates">{era["dates"]}</span></h3>')
        o.append(f'<p class="cf-blurb">{era["blurb"]}</p>')
        src = " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in era["read"])
        if era.get("audio"):
            src += f' &nbsp;·&nbsp; Audio: <a href="{era["audio"]}" target="_blank" rel="noopener">LibriVox</a>'
        o.append(f'<p class="cf-sources">Read free: {src}</p>')
        o.append('<ul class="cf-list">')
        for wid, title, by, read, note in era["works"]:
            url = CF_READ.get(wid) or read
            rl = (f'<a class="cf-read" href="{url}" target="_blank" rel="noopener">read &rsaquo;</a>'
                  if url else '')
            au = CF_AUDIO.get(wid)
            al = (f'<a class="cf-listen" href="{au[0]}" target="_blank" rel="noopener">listen &rsaquo;</a>'
                  if au else '')
            links = "".join(f'<span class="cf-sep">·</span>{x}' for x in (rl, al) if x)
            o.append(f'<li class="cf-item"><label><input type="checkbox" data-cf="{wid}">'
                     f'<span class="cf-title">{title}</span></label>'
                     f'<div class="cf-meta"><span class="cf-by">{by}</span>{links}</div>'
                     f'<div class="cf-note">{note}</div></li>')
        o.append('</ul></div>')
    o.append('<p class="res-foot">Text links point to free public-domain libraries — New Advent, '
             'CCEL, Wikisource and Early Christian Writings — and audio to LibriVox and other free '
             'sources. A few modern books link to the publisher.</p>')
    if ornament:
        o.append(art(ornament, foot=True))
    o.append('</section>')
    return "\n".join(o)


# Resources hub: a card per topic/section (links to its own page)
RES_CARDS = [
    ("The Theotokos", "theotokos.html", "Who the Church confesses Mary to be — and why."),
    ("The Priesthood", "priesthood.html", "The threefold ministry, and what the Church asks of a priest."),
    ("The Early Church Fathers", "fathers.html", "A reading checklist by era, with text and audio."),
    ("The Creeds", "creeds.html", "The Church's confessions of faith, in a few lines."),
    ("The Ecumenical Councils", "councils.html", "The canons and definitions of the councils."),
    ("Catechisms", "catechisms.html", "Ordered introductions to the whole faith."),
    ("Recommended Reading", "reading.html", "A few books to go deeper."),
]


def hub_page():
    o = ['<section class="resources" id="top">', _divider("Resources"),
         '<p class="res-intro">Explore the faith — choose a topic.</p>', '<div class="res-hub">']
    for name, href, blurb in RES_CARDS:
        o.append(f'<a class="res-card" href="{href}"><span class="res-card-t">{name}</span>'
                 f'<span class="res-card-d">{blurb}</span></a>')
    o.append('</div>')
    o.append(art("roundel", foot=True))
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

_ancient_src = open("ancient.content.html").read() if os.path.exists("ancient.content.html") else ""
_amarks = list(re.finditer(r'<section class="divider afpb" id="(af-[a-z]+)">', _ancient_src))
ANCIENT = {}
for _ai, _am in enumerate(_amarks):
    _aend = _amarks[_ai + 1].start() if _ai + 1 < len(_amarks) else len(_ancient_src)
    ANCIENT[_am.group(1)] = _ancient_src[_am.start():_aend]


def afpb_hub():
    o = ['<section class="resources afpb-hub" id="top">',
         _divider("The Ancient Faith Prayer Book"),
         '<p class="res-intro">Prayers from <em>The Ancient Faith Prayer Book</em> '
         '(Ancient Faith Publishing). ' + PILL + '</p>',
         '<div class="res-hub">']
    for slug, title, blurb in AFPB:
        if slug not in ANCIENT:
            continue
        o.append(f'<a class="res-card afpb-card" href="{slug}.html">'
                 f'<span class="res-card-t">{title}</span>'
                 f'<span class="res-card-d">{blurb}</span></a>')
    o.append('</div></section>')
    return "\n".join(o)


# ---- scripts ---------------------------------------------------------------
EARLY_JS = '''<script>
(function(){var r=document.documentElement,L=localStorage,t=L.getItem("theme"),s=L.getItem("size"),f=L.getItem("font");
if(t==="dark"||t==="light")r.dataset.theme=t;else if(window.matchMedia&&matchMedia("(prefers-color-scheme:dark)").matches)r.dataset.theme="dark";
if(s)r.dataset.size=s;if(f==="dyslexic")r.dataset.font="dyslexic";
var tc=document.getElementById("tc");if(tc)tc.setAttribute("content",r.dataset.theme==="dark"?"#2b2722":"#faf6ee");})();
</script>'''

CONTROL_JS = '''<script>
(function(){
  var r=document.documentElement, d=document, L=localStorage;
  var backdrop=d.getElementById("menu-backdrop");
  // each pop-up sheet, paired with the tab button that opens it
  var sheets=[["prayers-btn","prayers-menu"],["resources-btn","resources-menu"],["settings-btn","menu"]]
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
    s.el.addEventListener("touchstart", function(e){ sy=e.touches[0].clientY; dy=0; s.el.style.transition="none"; }, {passive:true});
    s.el.addEventListener("touchmove", function(e){ if(sy===null) return; dy=e.touches[0].clientY-sy; if(dy>0) s.el.style.transform="translateY("+dy+"px)"; }, {passive:true});
    s.el.addEventListener("touchend", function(){ s.el.style.transition=""; s.el.style.transform=""; if(dy>70) hideAll(); sy=null; });
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
  function paintTheme(){ var dark=r.dataset.theme==="dark";
    td.setAttribute("aria-pressed", dark?"true":"false");
    tl.setAttribute("aria-pressed", dark?"false":"true");
    if(tc) tc.setAttribute("content", dark?"#2b2722":"#faf6ee"); }
  tl.onclick=function(){ r.dataset.theme="light"; L.setItem("theme","light"); paintTheme(); };
  td.onclick=function(){ r.dataset.theme="dark";  L.setItem("theme","dark");  paintTheme(); };

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

  paintTheme(); paintDys();
})();
</script>'''

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
     LANDING.format(cross=CLOSING, rule=RULE_FIG), active="home")

# one page per prayer time (read-aloud player on each)
PRAYER_PAGES = [("morning", "Morning Prayers"), ("table", "Prayers at Table"),
                ("hours", "Prayers for the Hours of the Day & Night"), ("sleep", "Prayers Before Sleep")]
for slug, title in PRAYER_PAGES:
    page(f"{slug}.html", f"{title} — Daily Prayers",
         f"{title}: a web edition of the St. Tikhon's Monastery Press / OCA daily-prayers booklet.",
         with_jump_nav(_headpiece(PRAYERS[slug])) + CLOSING, active="prayers", scripts=PLAYER)

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
             body + CLOSING, active="prayers", scripts=PLAYER)

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

REF_SLUGS = {"The Creeds": "creeds", "The Ecumenical Councils": "councils",
             "Catechisms": "catechisms", "Recommended Reading": "reading"}
REF_ORN = {"The Creeds": "chirho", "The Ecumenical Councils": "cross",
           "Catechisms": "roundel", "Recommended Reading": "rule"}
for ref in REF_SECTIONS:
    page(f'{REF_SLUGS[ref["name"]]}.html', f'{ref["name"]} — Daily Prayers',
         ref.get("blurb", "") or ref["name"], ref_page(ref, REF_ORN[ref["name"]]), active="resources")
