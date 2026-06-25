#!/usr/bin/env python3
"""Generate downloadable Orthodox liturgical calendars (.ics) — New (Revised
Julian) and Old (Julian) — that load into Google Calendar, Outlook, and Apple
Calendar, and can be subscribed to on mobile.

All dates are computed from public, factual liturgical data:
 - Orthodox Pascha via the Meeus Julian computus (then +13 days -> Gregorian).
 - The moveable cycle is offset from Pascha (identical in both calendars).
 - Fixed feasts are observed on their familiar date in the New calendar, and
   +13 days later (the Gregorian equivalent of the Julian date) in the Old.

Run:  python3 generate_calendars.py   ->  writes calendars/*.ics
"""

from datetime import date, timedelta

YEARS = range(2025, 2046)        # moveable events are emitted per-year over this span
JULIAN_OFFSET = 13               # Julian -> Gregorian, valid 1900-2099
DTSTAMP = "20240101T000000Z"     # fixed, for reproducible builds
DOMAIN = "othroprayers"          # used only to mint stable UIDs


def orthodox_pascha(year):
    """Gregorian date of Orthodox Pascha (Meeus Julian algorithm + 13 days)."""
    a, b, c = year % 4, year % 7, year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month = (d + e + 114) // 31
    day = ((d + e + 114) % 31) + 1
    return date(year, month, day) + timedelta(days=JULIAN_OFFSET)


# ---- the Twelve Great Feasts (fixed) + Pascha + major commemorations --------
# (month, day, name, is_great) — the New-calendar Gregorian date; Old = +13
FIXED = [
    (9,  1,  "Church New Year (Indiction)",                       False),
    (9,  8,  "Nativity of the Most Holy Theotokos",               True),
    (9,  14, "Exaltation of the Holy Cross",                      True),
    (10, 1,  "Protection of the Most Holy Theotokos",             False),
    (11, 8,  "Synaxis of the Archangel Michael & All Angels",     False),
    (11, 21, "Entry of the Theotokos into the Temple",            True),
    (12, 6,  "St Nicholas the Wonderworker",                      False),
    (12, 25, "The Nativity of Christ",                            True),
    (1,  1,  "Circumcision of Christ & St Basil the Great",       False),
    (1,  6,  "The Holy Theophany of Christ",                      True),
    (1,  30, "Synaxis of the Three Holy Hierarchs",               False),
    (2,  2,  "The Meeting of the Lord in the Temple",             True),
    (3,  25, "The Annunciation of the Theotokos",                 True),
    (4,  23, "St George the Great Martyr",                        False),
    (5,  21, "Ss Constantine & Helen, Equal-to-the-Apostles",     False),
    (6,  24, "Nativity of St John the Forerunner",                False),
    (6,  29, "The Holy Apostles Peter & Paul",                    False),
    (7,  20, "The Holy Prophet Elijah",                           False),
    (8,  6,  "The Transfiguration of Christ",                     True),
    (8,  15, "The Dormition of the Most Holy Theotokos",          True),
    (8,  29, "The Beheading of St John the Forerunner",           False),
    (9,  26, "Repose of St John the Theologian",                  False),
    (10, 18, "St Luke the Apostle & Evangelist",                  False),
    (10, 26, "St Demetrios the Myrrh-streamer",                   False),
    (11, 1,  "Ss Cosmas & Damian, the Unmercenaries",             False),
    (11, 13, "St John Chrysostom",                                False),
    (11, 16, "St Matthew the Apostle & Evangelist",               False),
    (11, 30, "St Andrew the First-Called Apostle",                False),
    (12, 4,  "St Barbara the Great Martyr",                       False),
    (12, 9,  "Conception of the Theotokos by Righteous Anna",     False),
    (12, 12, "St Spyridon the Wonderworker",                      False),
    (12, 27, "St Stephen the Protomartyr & Archdeacon",           False),
    (1,  7,  "Synaxis of St John the Forerunner",                 False),
    (1,  17, "St Anthony the Great",                              False),
    (1,  25, "St Gregory the Theologian",                         False),
    (3,  9,  "The Holy Forty Martyrs of Sebaste",                 False),
    (4,  25, "St Mark the Apostle & Evangelist",                  False),
    (5,  8,  "St John the Theologian",                            False),
    (7,  17, "St Marina the Great Martyr",                        False),
    (7,  25, "The Dormition of Righteous Anna",                   False),
]

# fixed fast markers (observed start dates) — New-calendar dates; Old = +13
FIXED_FASTS = [
    (1,  5,  "Eve of Theophany — strict fast"),
]

# fixed days within a fast whose discipline is relaxed (fish) or made strict
FAST_DAY_FIXED = [
    (3,  25, "Annunciation — fish, wine & oil permitted"),
    (8,  6,  "Transfiguration — fish, wine & oil permitted"),
    (9,  14, "Exaltation of the Cross — strict fast"),
    (8,  29, "Beheading of St John — strict fast"),
]

# ---- the moveable cycle (offset in days from Pascha Sunday) -----------------
# (offset, name, is_great)
MOVEABLE = [
    (-70, "Sunday of the Publican & Pharisee (Triodion begins)", False),
    (-63, "Sunday of the Prodigal Son",                          False),
    (-57, "Saturday of Souls (Meatfare)",                        False),
    (-56, "Sunday of the Last Judgement (Meatfare)",             False),
    (-49, "Forgiveness Sunday (Cheesefare)",                     False),
    (-48, "Great Lent begins (Clean Monday)",                    False),
    (-42, "Sunday of Orthodoxy",                                 False),
    (-35, "St Gregory Palamas (2nd Sunday of Lent)",             False),
    (-28, "Veneration of the Cross (3rd Sunday of Lent)",        False),
    (-21, "St John Climacus (4th Sunday of Lent)",               False),
    (-14, "St Mary of Egypt (5th Sunday of Lent)",               False),
    (-8,  "Lazarus Saturday",                                    False),
    (-7,  "Entry of the Lord into Jerusalem (Palm Sunday)",      True),
    (-6,  "Holy Monday",                                         False),
    (-3,  "Holy Thursday",                                       False),
    (-2,  "Holy & Great Friday",                                 False),
    (-1,  "Holy & Great Saturday",                               False),
    (0,   "GREAT & HOLY PASCHA — The Resurrection of Christ",    True),
    (+7,  "Thomas Sunday (Antipascha)",                          False),
    (+9,  "Radonitsa (commemoration of the departed)",          False),
    (+14, "Sunday of the Myrrh-bearing Women",                   False),
    (+39, "The Ascension of the Lord",                           True),
    (+49, "Pentecost — the Holy Trinity",                        True),
    (+50, "Monday of the Holy Spirit",                           False),
    (+56, "All Saints",                                          False),
]


def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")


def fold(line):
    out, line = [], line
    while len(line.encode("utf-8")) > 74:
        # find a cut at <=74 bytes
        cut = 74
        while len(line[:cut].encode("utf-8")) > 74:
            cut -= 1
        out.append(line[:cut])
        line = " " + line[cut:]
    out.append(line)
    return "\r\n".join(out)


def vevent(uid, d, summary, great, rrule=None):
    lines = ["BEGIN:VEVENT",
             f"UID:{uid}@{DOMAIN}",
             f"DTSTAMP:{DTSTAMP}",
             f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
             f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}"]
    if rrule:
        lines.append(rrule)
    lines.append(fold("SUMMARY:" + ("✞ " if great else "") + esc(summary)))
    lines.append("CATEGORIES:" + ("Great Feast" if great else "Feast"))
    lines.append("TRANSP:TRANSPARENT")
    lines.append("END:VEVENT")
    return "\r\n".join(lines)


def slug(name):
    s = "".join(ch.lower() if ch.isalnum() else "-" for ch in name)
    return "-".join(p for p in s.split("-") if p)[:48]


def vspan(uid, d1, d2_excl, summary, desc=None, cat="Fast"):
    """A multi-day all-day event over [d1, d2_excl)."""
    lines = ["BEGIN:VEVENT", f"UID:{uid}@{DOMAIN}", f"DTSTAMP:{DTSTAMP}",
             f"DTSTART;VALUE=DATE:{d1:%Y%m%d}", f"DTEND;VALUE=DATE:{d2_excl:%Y%m%d}",
             fold("SUMMARY:" + esc(summary))]
    if desc:
        lines.append(fold("DESCRIPTION:" + esc(desc)))
    lines += ["CATEGORIES:" + cat, "TRANSP:TRANSPARENT", "END:VEVENT"]
    return "\r\n".join(lines)


def vweekly(uid, anchor, byday, summary, desc):
    """A weekly-recurring all-day event on the given weekday."""
    return "\r\n".join([
        "BEGIN:VEVENT", f"UID:{uid}@{DOMAIN}", f"DTSTAMP:{DTSTAMP}",
        f"DTSTART;VALUE=DATE:{anchor:%Y%m%d}",
        f"DTEND;VALUE=DATE:{anchor + timedelta(days=1):%Y%m%d}",
        f"RRULE:FREQ=WEEKLY;BYDAY={byday}",
        fold("SUMMARY:" + esc(summary)), fold("DESCRIPTION:" + esc(desc)),
        "CATEGORIES:Fast", "TRANSP:TRANSPARENT", "END:VEVENT"])


def build(old):
    off = timedelta(days=JULIAN_OFFSET) if old else timedelta(0)
    label = "Old (Julian)" if old else "New (Revised Julian)"
    head = [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//OthroPrayers//Orthodox Calendar//EN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        fold(f"X-WR-CALNAME:Orthodox Calendar — {label}"),
        "X-WR-TIMEZONE:UTC",
        fold("X-WR-CALDESC:Orthodox Christian feasts, fasts and the Paschal "
             f"cycle ({label} calendar). Generated from public liturgical data."),
        "REFRESH-INTERVAL;VALUE=DURATION:P30D",
        "X-PUBLISHED-TTL:P30D",
    ]
    body = []
    # fixed feasts — one yearly-recurring event each
    for m, dd, name, great in FIXED:
        d = date(2025, m, dd) + off
        body.append(vevent(f"fixed-{slug(name)}", d, name, great,
                            rrule="RRULE:FREQ=YEARLY"))
    for m, dd, name in FIXED_FASTS:
        d = date(2025, m, dd) + off
        body.append(vevent(f"fast-{slug(name)}", d, name, False,
                            rrule="RRULE:FREQ=YEARLY"))
    # the year-round Wednesday & Friday fast (one weekly-recurring event each),
    # with the kind of fast shown in the title
    wf_note = ("The customary weekly fast: abstain from meat, fish, dairy and eggs; wine and oil "
               "are often permitted. Suspended during the fast-free weeks marked on the calendar.")
    body.append(vweekly("fast-wed", date(2025, 1, 1), "WE",
                        "Wednesday Fast — no meat, fish, dairy or eggs", wf_note))
    body.append(vweekly("fast-fri", date(2025, 1, 3), "FR",
                        "Friday Fast — no meat, fish, dairy or eggs", wf_note))
    # fixed days whose fasting is relaxed or made strict (shown as their own marker)
    for m, dd, summary in FAST_DAY_FIXED:
        body.append(vevent(f"fastday-{slug(summary)}", date(2025, m, dd) + off, summary, False,
                            rrule="RRULE:FREQ=YEARLY"))
    # moveable cycle + the four fasting seasons + fast-free weeks (per year)
    for y in YEARS:
        pascha = orthodox_pascha(y)
        for offset, name, great in MOVEABLE:
            d = pascha + timedelta(days=offset)
            body.append(vevent(f"mov-{slug(name)}-{y}", d, name, great))
        # Cheesefare week: no meat, but dairy/eggs/fish permitted all week
        body.append(vspan(f"cheesefare-{y}", pascha + timedelta(-55), pascha + timedelta(-48),
                          "Cheesefare Week — no meat; dairy, eggs & fish permitted",
                          "The last week before Great Lent: meat is set aside, but dairy, eggs and "
                          "fish are eaten all week, including Wednesday and Friday."))
        # the four fasting seasons — the kind of fast is named in the title
        body.append(vspan(f"fast-lent-{y}", pascha + timedelta(-48), pascha,
                          "Great Lent & Holy Week — strict fast",
                          "Strict fast on weekdays (no meat, fish, dairy, eggs, wine or oil). Wine "
                          "& oil on Saturdays and Sundays; fish on the Annunciation and Palm Sunday."))
        ap, pp = pascha + timedelta(57), date(y, 6, 29) + off
        if ap < pp:
            body.append(vspan(f"fast-apostles-{y}", ap, pp,
                              "Apostles' Fast — fish, wine & oil on most days",
                              "No meat, dairy or eggs. Fish, wine and oil are permitted on most "
                              "days (commonly not on Wednesdays and Fridays)."))
        body.append(vspan(f"fast-dormition-{y}", date(y, 8, 1) + off, date(y, 8, 15) + off,
                          "Dormition Fast — strict",
                          "Strict fast; wine & oil on Saturdays and Sundays; fish on the "
                          "Transfiguration (Aug 6 / 19)."))
        body.append(vspan(f"fast-nativity-{y}", date(y, 11, 15) + off, date(y, 12, 25) + off,
                          "Nativity Fast — fish, wine & oil on many days",
                          "No meat, dairy or eggs. Fish, wine and oil are permitted on many days; "
                          "the final days before the Nativity are kept more strictly."))
        # the moveable relaxation: fish on Palm Sunday
        body.append(vevent(f"fastday-palm-fish-{y}", pascha + timedelta(-7),
                          "Palm Sunday — fish, wine & oil permitted", False))
        # fast-free weeks — all foods
        body.append(vspan(f"ff-bright-{y}", pascha, pascha + timedelta(7),
                          "Fast-free (Bright Week) — all foods permitted", cat="Fast-free"))
        body.append(vspan(f"ff-trinity-{y}", pascha + timedelta(49), pascha + timedelta(56),
                          "Fast-free (week after Pentecost) — all foods permitted", cat="Fast-free"))
        body.append(vspan(f"ff-publican-{y}", pascha + timedelta(-70), pascha + timedelta(-63),
                          "Fast-free (after the Publican & Pharisee) — all foods", cat="Fast-free"))
        body.append(vspan(f"ff-svyatki-{y}", date(y, 12, 25) + off, date(y + 1, 1, 5) + off,
                          "Fast-free (Nativity to Theophany) — all foods", cat="Fast-free"))
    ics = "\r\n".join(head + body + ["END:VCALENDAR"]) + "\r\n"
    return ics


def main():
    import os
    os.makedirs("calendars", exist_ok=True)
    for old, fn in [(False, "orthodox-new-calendar.ics"),
                    (True, "orthodox-old-calendar.ics")]:
        open(f"calendars/{fn}", "w", newline="").write(build(old))
        print("wrote calendars/" + fn)
    # sanity: print a few Pascha dates
    print("Orthodox Pascha:", {y: f"{orthodox_pascha(y):%b %d}" for y in range(2024, 2031)})


if __name__ == "__main__":
    main()
