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

  function renderWeek(cal) {
    var box = document.getElementById("this-week");
    if (!box) return;
    if (!cal) { box.hidden = true; box.innerHTML = ""; return; }
    var today = todayUTC();
    var h = '<h2 class="tw-h">This Week</h2>'
          + '<div class="tw-sub">' + (cal === "old" ? "Old (Julian)" : "New (Revised Julian)") + ' calendar</div>'
          + '<ul class="tw-list">';
    for (var i = 0; i < 7; i++) {
      var dt = addDays(today, i), inf = dayInfo(dt, cal);
      var feast = inf.feasts.map(function (f) { return (f.great ? "✦ " : "") + f.name; }).join(" · ");
      var fast = inf.fast.kind !== "none"
        ? '<span class="tw-fast tw-' + inf.fast.kind + '">' + inf.fast.label + '</span>' : "";
      h += '<li class="tw-day' + (i === 0 ? " tw-today" : "") + '">'
        + '<span class="tw-date">' + WD[dt.getUTCDay()] + " " + MO[dt.getUTCMonth()] + " " + dt.getUTCDate() + '</span>'
        + '<span class="tw-body">' + (feast ? '<span class="tw-feast">' + feast + '</span>' : "") + fast + '</span>'
        + '</li>';
    }
    h += '</ul><a class="tw-more" href="calendar.html">Add to your phone &rsaquo;</a>';
    box.innerHTML = h;
    box.hidden = false;
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
