/* Client-side Orthodox calendar engine for the home "This Week" panel and the
 * in-app fast-day reminder. Feast data comes from calendar-data.js (window.OC,
 * generated from generate_calendars.py); the fasting rules below mirror it.
 * All date maths is done in UTC to avoid timezone drift. */
(function () {
  var OC = window.OC;
  if (!OC) return;
  var OFF = OC.offset || 13;
  var WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  var MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function mkUTC(y, m, d) { return new Date(Date.UTC(y, m - 1, d)); }
  function addDays(dt, n) { var x = new Date(dt.getTime()); x.setUTCDate(x.getUTCDate() + n); return x; }
  function diffDays(a, b) { return Math.round((a - b) / 86400000); }

  // Orthodox Pascha (Meeus Julian computus) as a Gregorian UTC date
  function pascha(y) {
    var a = y % 4, b = y % 7, c = y % 19, d = (19 * c + 15) % 30, e = (2 * a + 4 * b - d + 34) % 7;
    var m = Math.floor((d + e + 114) / 31), day = ((d + e + 114) % 31) + 1;
    return addDays(mkUTC(y, m, day), 13);   // Julian -> Gregorian (1900-2099)
  }

  function feastsFor(dt, off) {
    var out = [];
    var base = addDays(dt, -off);            // un-shift to the Julian fixed date
    OC.fixed.forEach(function (f) {
      if (base.getUTCMonth() + 1 === f[0] && base.getUTCDate() === f[1]) out.push({ name: f[2], great: f[3] });
    });
    var p = pascha(dt.getUTCFullYear()), k = diffDays(dt, p);   // moveable: same for both calendars
    OC.moveable.forEach(function (mv) { if (mv[0] === k) out.push({ name: mv[1], great: mv[2] }); });
    return out;
  }

  function F(l, k) { return { label: l, kind: k }; }

  // The fasting discipline for a day (a customary guide; varies by jurisdiction)
  function fastFor(dt, off) {
    var y = dt.getUTCFullYear(), p = pascha(y), k = diffDays(dt, p), dow = dt.getUTCDay();
    var base = addDays(dt, -off), bm = base.getUTCMonth() + 1, bd = base.getUTCDate();
    // fast-free weeks
    if (k >= 0 && k <= 6) return F("Fast-free — all foods", "free");
    if (k >= 49 && k <= 55) return F("Fast-free — all foods", "free");
    if (k >= -70 && k <= -64) return F("Fast-free — all foods", "free");
    if ((bm === 12 && bd >= 25) || (bm === 1 && bd <= 4)) return F("Fast-free — all foods", "free");
    // special fixed days
    if (bm === 3 && bd === 25) return F("Fish, wine & oil", "fish");   // Annunciation
    if (bm === 8 && bd === 6) return F("Fish, wine & oil", "fish");    // Transfiguration
    if (bm === 9 && bd === 14) return F("Strict fast", "strict");      // Exaltation
    if (bm === 8 && bd === 29) return F("Strict fast", "strict");      // Beheading
    if (bm === 1 && bd === 5) return F("Strict fast", "strict");       // Eve of Theophany
    if (k === -7) return F("Fish, wine & oil", "fish");                // Palm Sunday
    // Cheesefare week
    if (k >= -55 && k <= -49) return F("No meat; dairy, eggs & fish", "dairy");
    // the four fasting seasons
    if (k >= -48 && k <= -1) return (dow === 0 || dow === 6) ? F("Wine & oil", "oil") : F("Strict fast", "strict");
    if (k >= 57 && dt <= addDays(mkUTC(y, 6, 28), off)) return F("Fish, wine & oil", "fish");  // Apostles'
    if (dt >= addDays(mkUTC(y, 8, 1), off) && dt <= addDays(mkUTC(y, 8, 14), off))
      return (dow === 0 || dow === 6) ? F("Wine & oil", "oil") : F("Strict fast", "strict");   // Dormition
    if (dt >= addDays(mkUTC(y, 11, 15), off) && dt <= addDays(mkUTC(y, 12, 24), off))
      return F("Fish, wine & oil", "fish");                                                    // Nativity
    // weekly Wednesday & Friday fast
    if (dow === 3 || dow === 5) return F("Fast — no meat, fish or dairy", "fast");
    return F("", "none");
  }

  function dayInfo(dt, calKey) {
    var off = calKey === "old" ? OFF : 0;
    return { feasts: feastsFor(dt, off), fast: fastFor(dt, off) };
  }

  function todayUTC() {
    var n = new Date();
    return mkUTC(n.getFullYear(), n.getMonth() + 1, n.getDate());
  }

  // short pill label per fast kind (the full guidance lives in the detail)
  var SHORT = { strict: "Strict", oil: "Wine & oil", fish: "Fish", dairy: "Dairy day",
                fast: "Fast day", free: "Fast-free", none: "" };
  // how to keep each kind of day (a customary guide; my own wording)
  var FAST_INFO = {
    strict: { title: "Strict fast", how: "No meat, fish, dairy, eggs, wine or oil; shellfish is usually allowed. This is the strictest level (xerophagy)." },
    oil:    { title: "Wine & oil", how: "Wine and oil are allowed today — but still no meat, fish, dairy or eggs." },
    fish:   { title: "Fish, wine & oil", how: "Fish, wine and oil are allowed today; no meat, dairy or eggs." },
    dairy:  { title: "Dairy permitted", how: "No meat, but dairy, eggs and fish are allowed all week — even on Wednesday and Friday." },
    fast:   { title: "Fast day", how: "A weekly fast day. Abstain from meat, fish, dairy and eggs; wine and oil are often kept too. Shellfish is usually allowed." },
    free:   { title: "Fast-free", how: "No fasting today — all foods are allowed, even on Wednesday and Friday." },
    none:   { title: "Not a fast day", how: "No fast is appointed for today." }
  };
  var NOTE = "Fasting goes hand in hand with prayer and almsgiving — it is not a diet. " +
             "Children, the sick, expectant mothers and travellers are given leniency; keep the " +
             "fast as your parish priest or spiritual father advises.";

  function renderWeek(cal) {
    var box = document.getElementById("this-week");
    if (!box) return;
    if (!cal) {
      // empty state that teaches: invite the reader to follow the calendar,
      // unless they've dismissed the prompt
      if (localStorage.getItem("tw-hide-prompt") === "1") { box.hidden = true; box.innerHTML = ""; return; }
      box.classList.add("tw-prompt-mode");
      box.innerHTML =
        '<span class="tw-prompt-emblem" aria-hidden="true">&#10022;</span>'
        + '<h2 class="tw-h">Follow the Church Calendar</h2>'
        + '<p class="tw-prompt-d">See this week&rsquo;s feasts and fasts here on the home page, '
        + 'with guidance on how to keep each day. Choose the Old (Julian) or New calendar in Settings.</p>'
        + '<div class="tw-prompt-actions">'
        + '<button class="tw-prompt-btn" id="tw-open-settings" type="button">Open Settings</button>'
        + '<button class="tw-prompt-skip" id="tw-skip" type="button">Not now</button>'
        + '</div>';
      box.hidden = false;
      var os = document.getElementById("tw-open-settings");
      if (os) os.addEventListener("click", function () {
        var sb = document.getElementById("settings-btn"); if (sb) sb.click();
      });
      var sk = document.getElementById("tw-skip");
      if (sk) sk.addEventListener("click", function () {
        localStorage.setItem("tw-hide-prompt", "1"); box.hidden = true; box.innerHTML = "";
      });
      return;
    }
    box.classList.remove("tw-prompt-mode");
    var today = todayUTC();
    var h = '<h2 class="tw-h">This Week</h2>'
          + '<div class="tw-sub">' + (cal === "old" ? "Old (Julian)" : "New (Revised Julian)") + ' calendar</div>'
          + '<div class="tw-list">';
    for (var i = 0; i < 7; i++) {
      var dt = addDays(today, i), inf = dayInfo(dt, cal), k = inf.fast.kind, isToday = i === 0;
      var feast = inf.feasts.map(function (f) { return (f.great ? "✦ " : "") + f.name; }).join(" · ");
      var fi = FAST_INFO[k] || FAST_INFO.none;
      var pill = k !== "none" ? '<span class="tw-fast tw-' + k + '">' + SHORT[k] + '</span>' : "";
      h += '<div class="tw-row">'
        + '<button class="tw-day' + (isToday ? " tw-today" : "") + '" type="button" aria-expanded="' + (isToday ? "true" : "false") + '">'
        + '<span class="tw-date">' + WD[dt.getUTCDay()] + " &middot; " + MO[dt.getUTCMonth()] + " " + dt.getUTCDate() + '</span>'
        + (feast ? '<span class="tw-feast">' + feast + '</span>' : "")
        + pill + '<span class="tw-chev" aria-hidden="true"></span>'
        + '</button>'
        + '<div class="tw-detail"' + (isToday ? "" : " hidden") + '>'
        + (feast ? '<p class="tw-d-feast">' + feast + '</p>' : "")
        + '<p class="tw-d-fast"><strong>' + fi.title + '.</strong> ' + fi.how + '</p>'
        + '<p class="tw-d-note">' + NOTE + '</p>'
        + '</div></div>';
    }
    h += '</div><a class="tw-more" href="calendar.html">Add to your phone &rsaquo;</a>';
    box.innerHTML = h;
    box.hidden = false;
    Array.prototype.forEach.call(box.querySelectorAll(".tw-day"), function (btn) {
      btn.addEventListener("click", function () {
        var open = btn.getAttribute("aria-expanded") === "true";
        btn.setAttribute("aria-expanded", open ? "false" : "true");
        var det = btn.nextElementSibling;
        if (det) det.hidden = open;
      });
    });
  }

  function maybeNotify(cal) {
    if (!cal) return;
    if (localStorage.getItem("fastnotify") !== "1") return;
    if (!window.Notification || Notification.permission !== "granted") return;
    var n = new Date(), key = n.getFullYear() + "-" + (n.getMonth() + 1) + "-" + n.getDate();
    if (localStorage.getItem("fastnotify-last") === key) return;   // at most once per day
    localStorage.setItem("fastnotify-last", key);
    var f = fastFor(todayUTC(), cal === "old" ? OFF : 0);
    if (f.kind !== "none" && f.kind !== "free") {
      try { new Notification("Orthodox fast today", { body: f.label, tag: "ortho-fast" }); } catch (e) {}
    }
  }

  window.OCsync = function () {
    var cal = localStorage.getItem("cal");   // "new" | "old" | null
    renderWeek(cal);
    maybeNotify(cal);
  };

  if (document.readyState !== "loading") window.OCsync();
  else document.addEventListener("DOMContentLoaded", window.OCsync);
})();
