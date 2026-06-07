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

# inline SVG icons (stroke uses currentColor; no emoji)
BURGER = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
          'stroke-linecap="round" aria-hidden="true"><line x1="3" y1="6" x2="21" y2="6"/>'
          '<line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>')
SUN = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
       'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/><path d="M12 1.5v2M12 20.5v2'
       'M3.9 3.9l1.4 1.4M18.7 18.7l1.4 1.4M1.5 12h2M20.5 12h2M3.9 20.1l1.4-1.4M18.7 5.3l1.4-1.4"/></svg>')
MOON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg>')

TOPNAV = '''<nav class="topnav" aria-label="Header">
  <a class="brand" href="#top"><span class="cross">&#10016;</span> Daily Prayers</a>
  <button id="burger" class="iconbtn" type="button" aria-haspopup="true" aria-expanded="false"
          aria-controls="menu" title="Menu" aria-label="Open menu">{BURGER}</button>
  <div id="menu-backdrop" class="backdrop"></div>
  <div id="menu" class="drawer" role="menu">
    <a class="drawer-link" href="#morning">Morning Prayers</a>
    <a class="drawer-link" href="#table">Prayers at Table</a>
    <a class="drawer-link" href="#hours">Prayers for the Hours</a>
    <a class="drawer-link" href="#sleep">Prayers Before Sleep</a>
    <div class="drawer-settings">
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
    </div>
  </div>
</nav>'''.format(BURGER=BURGER, SUN=SUN, MOON=MOON)

# applied in <head> before paint to avoid a flash of the wrong theme/size/font
EARLY_JS = '''<script>
(function(){var r=document.documentElement,L=localStorage,t=L.getItem("theme"),s=L.getItem("size"),f=L.getItem("font");
if(t==="dark"||t==="light")r.dataset.theme=t;else if(window.matchMedia&&matchMedia("(prefers-color-scheme:dark)").matches)r.dataset.theme="dark";
if(s)r.dataset.size=s;if(f==="dyslexic")r.dataset.font="dyslexic";})();
</script>'''

CONTROL_JS = '''<script>
(function(){
  var r=document.documentElement, d=document, L=localStorage;
  var menu=d.getElementById("menu"), burger=d.getElementById("burger"),
      backdrop=d.getElementById("menu-backdrop");
  function open(o){ menu.classList.toggle("open",o); backdrop.classList.toggle("open",o);
    burger.setAttribute("aria-expanded", o?"true":"false"); }
  burger.addEventListener("click", function(e){ e.stopPropagation(); open(!menu.classList.contains("open")); });
  backdrop.addEventListener("click", function(){ open(false); });
  d.addEventListener("keydown", function(e){ if(e.key==="Escape") open(false); });
  Array.prototype.forEach.call(menu.querySelectorAll(".drawer-link"), function(a){
    a.addEventListener("click", function(){ open(false); }); });

  var sizes=["","l","xl"];
  function cur(){ return Math.max(0, sizes.indexOf(r.dataset.size||"")); }
  function setSize(i){ i=Math.max(0,Math.min(sizes.length-1,i)); var v=sizes[i];
    if(v){ r.dataset.size=v; L.setItem("size",v); } else { delete r.dataset.size; L.removeItem("size"); } }
  d.getElementById("size-up").onclick=function(){ setSize(cur()+1); };
  d.getElementById("size-dn").onclick=function(){ setSize(cur()-1); };

  var tl=d.getElementById("theme-light"), td=d.getElementById("theme-dark");
  function paintTheme(){ var dark=r.dataset.theme==="dark";
    td.setAttribute("aria-pressed", dark?"true":"false");
    tl.setAttribute("aria-pressed", dark?"false":"true"); }
  tl.onclick=function(){ r.dataset.theme="light"; L.setItem("theme","light"); paintTheme(); };
  td.onclick=function(){ r.dataset.theme="dark";  L.setItem("theme","dark");  paintTheme(); };

  var dys=d.getElementById("dys");
  function paintDys(){ dys.setAttribute("aria-checked", r.dataset.font==="dyslexic"?"true":"false"); }
  dys.onclick=function(){ if(r.dataset.font==="dyslexic"){ delete r.dataset.font; L.setItem("font","serif"); }
    else { r.dataset.font="dyslexic"; L.setItem("font","dyslexic"); } paintDys(); };

  paintTheme(); paintDys();
})();
</script>'''

HTML = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prayers for Morning, Day &amp; Night</title>
<meta name="description" content="Orthodox prayers for morning, the table, the
  hours of the day and night, and before sleep — a web edition of the booklet
  published by St. Tikhon's Monastery Press / OCA.">
<link rel="icon" href="favicon.ico" sizes="32x32">
<link rel="icon" type="image/png" sizes="32x32" href="assets/icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="assets/icons/favicon-16.png">
<link rel="apple-touch-icon" href="assets/icons/apple-touch-icon.png">
<link rel="manifest" href="site.webmanifest">
<meta name="apple-mobile-web-app-title" content="Prayers">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#fffdf8">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#1d1d20">
<link rel="stylesheet" href="styles.css">
{EARLY_JS}
</head>
<body>
<main class="book">
{COVER}
{content}
</main>
{TOPNAV}
{CONTROL_JS}
</body>
</html>
'''

open("index.html", "w").write(HTML)
print("wrote index.html", len(HTML), "bytes")
