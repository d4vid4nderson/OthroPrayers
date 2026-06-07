#!/usr/bin/env python3
"""Assemble index.html from the cover template + generated prayer content.
Run `python3 generate.py` first to (re)produce prayers.content.html."""

import re
content = open("prayers.content.html").read()
# one black, letter-spaced title the generator can't auto-clean (CSS spaces it)
content = re.sub(r"for\s+a\s+n\s+y\s+m\s+e\s+a\s+l", "for any meal", content)

COVER = '''<section class="cover" id="top">
  <figure class="coverimg">
    <img src="assets/img/icon_p1.png" width="742" height="787"
         alt="Icon of the Mother of God “of the Sign” (Znamenie)">
  </figure>
  <h1>PRAYERS <span class="i">for</span> MORNING,<br>DAY &amp; NIGHT</h1>
  <nav aria-label="Contents">
    <a href="#morning">Morning Prayers</a>
    <a href="#table">Prayers at Table</a>
    <a href="#hours">Prayers for the Hours of the Day and Night</a>
    <a href="#sleep">Prayers Before Sleep</a>
  </nav>
  <p class="colophon">These prayers are excerpted from <cite>Orthodox Christian
    Prayers</cite>, edited by Priest John Mikitish &amp; Hieromonk Herman
    (Majkrzak) (South Canaan, Penn.: St. Tikhon&rsquo;s Monastery Press, 2019).
    &copy; 2019 St. Tikhon&rsquo;s Monastery Press. All rights reserved.
    Permission is granted for this document to be made available on
    <a href="https://www.oca.org">www.oca.org</a>, for those who wish to use
    these prayers in their homes.</p>
</section>'''

TOPNAV = '''<nav class="topnav" aria-label="Sections">
  <a class="home" href="#top">&#10016;</a>
  <a href="#morning">Morning</a>
  <a href="#table">Table</a>
  <a href="#hours">Hours</a>
  <a href="#sleep">Before Sleep</a>
</nav>'''

HTML = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prayers for Morning, Day &amp; Night</title>
<meta name="description" content="Orthodox prayers for morning, the table, the
  hours of the day and night, and before sleep — a web edition of the booklet
  published by St. Tikhon's Monastery Press / OCA.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="styles.css">
</head>
<body>
{TOPNAV}
<main class="book">
{COVER}
{content}
</main>
<a class="totop" href="#top" aria-label="Back to top">&#8593;</a>
</body>
</html>
'''

open("index.html", "w").write(HTML)
print("wrote index.html", len(HTML), "bytes")
