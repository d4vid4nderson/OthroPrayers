/* In-app Bible reader. Reads the canon index from window.BIBLE (bible-index.js)
 * and lazy-loads each book from bible/<id>.json on demand. Two views: a grouped
 * library, and a chapter reader with prev/next + a chapter picker. The last
 * position is remembered, and #book or #book/chapter deep-links work. The
 * service worker caches each book as it is read, so visited text is available
 * offline. */
(function () {
  var DATA = window.BIBLE;
  var root = document.getElementById("bible");
  if (!DATA || !root) return;

  var byId = {};
  DATA.books.forEach(function (b) { byId[b.id] = b; });
  var cache = {};                       // id -> book json (in memory for the session)
  var LAST = "bible-last";
  var currentKey = null;                // what view is shown, to avoid re-render loops

  function esc(s) { return (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

  // --- library (grouped book list) -----------------------------------------
  function renderLibrary() {
    currentKey = "";
    if (location.hash) location.hash = "";
    var last = localStorage.getItem(LAST);
    var h = "";
    if (last && byId[last.split("/")[0]]) {
      var lb = byId[last.split("/")[0]], lc = last.split("/")[1] || 1;
      h += '<button class="bib-continue" data-go="' + last + '">'
         + '<span class="bib-continue-l">Continue reading</span>'
         + '<span class="bib-continue-b">' + esc(lb.n) + " " + lc + "</span></button>";
    }
    DATA.groups.forEach(function (g) {
      var books = DATA.books.filter(function (b) { return b.g === g.id; });
      if (!books.length) return;
      h += '<h2 class="bib-group">' + esc(g.n) + "</h2><div class=\"bib-books\">";
      books.forEach(function (b) {
        h += '<button class="bib-book' + (b.dc ? " bib-dc" : "") + '" data-go="' + b.id + '">'
           + esc(b.n) + "</button>";
      });
      h += "</div>";
    });
    root.innerHTML = h;
    var scroller = document.querySelector(".scroll");
    if (scroller) scroller.scrollTop = 0;
  }

  // --- a chapter -----------------------------------------------------------
  function show(id, chap) {
    var b = byId[id];
    if (!b) { renderLibrary(); return; }
    chap = Math.max(1, Math.min(b.ch, parseInt(chap, 10) || 1));
    root.innerHTML = '<p class="bible-loading">Opening ' + esc(b.n) + "&hellip;</p>";
    loadBook(id).then(function (book) {
      render(b, book, chap);
    }).catch(function () {
      root.innerHTML = '<p class="bible-loading">Couldn’t open ' + esc(b.n)
        + '. Check your connection and try again.</p>';
    });
  }

  function loadBook(id) {
    if (cache[id]) return Promise.resolve(cache[id]);
    return fetch("bible/" + id + ".json").then(function (r) {
      if (!r.ok) throw new Error("http " + r.status);
      return r.json();
    }).then(function (j) { cache[id] = j; return j; });
  }

  function chapterPicker(b, chap) {
    var o = '<select class="bib-chap-sel" aria-label="Chapter">';
    for (var i = 1; i <= b.ch; i++) o += '<option value="' + i + '"' + (i === chap ? " selected" : "") + ">" + i + "</option>";
    return o + "</select>";
  }

  var CHEV_L = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>';
  var CHEV_R = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>';
  var BOOKS_I = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h7v15H4z"/><path d="M13 5h7v15h-7z"/></svg>';

  function render(b, book, chap) {
    location.hash = b.id + (chap > 1 ? "/" + chap : "");
    currentKey = b.id + "/" + chap;
    localStorage.setItem(LAST, b.id + "/" + chap);
    var verses = book.c[chap - 1] || [];
    var h = '<div class="bib-bar">'
      + '<button class="bib-lib" data-lib="1" aria-label="All books">' + BOOKS_I + "<span>Books</span></button>"
      + '<span class="bib-title">' + esc(b.n) + " " + chapterPicker(b, chap) + "</span>"
      + "</div>";
    h += '<div class="bib-verses">';
    verses.forEach(function (vt) {
      h += '<p class="bib-v"><span class="bib-n">' + vt[0] + "</span>" + esc(vt[1]) + "</p>";
    });
    h += "</div>";
    // prev / next chapter (spilling across book boundaries handled by the picker)
    h += '<div class="bib-chapnav">';
    h += chap > 1
      ? '<button class="bib-pn" data-go="' + b.id + "/" + (chap - 1) + '">' + CHEV_L + " Chapter " + (chap - 1) + "</button>"
      : "<span></span>";
    h += chap < b.ch
      ? '<button class="bib-pn" data-go="' + b.id + "/" + (chap + 1) + '">Chapter ' + (chap + 1) + " " + CHEV_R + "</button>"
      : "<span></span>";
    h += "</div>";
    root.innerHTML = h;
    var scroller = document.querySelector(".scroll");
    if (scroller) scroller.scrollTop = 0;
    var sel = root.querySelector(".bib-chap-sel");
    if (sel) sel.addEventListener("change", function () { show(b.id, sel.value); });
  }

  // --- routing -------------------------------------------------------------
  function keyFor(hash) {
    hash = (hash || "").replace(/^#/, "");
    if (!hash) return "";
    var p = hash.split("/");
    return byId[p[0]] ? p[0] + "/" + (parseInt(p[1], 10) || 1) : "";
  }
  function route() {
    var hash = (location.hash || "").replace(/^#/, "");
    if (!hash) {
      var last = localStorage.getItem(LAST);
      if (last) { var p = last.split("/"); show(p[0], p[1] || 1); return; }
      renderLibrary(); return;
    }
    var q = hash.split("/");
    if (byId[q[0]]) show(q[0], q[1] || 1); else renderLibrary();
  }
  // honour back/forward and deep links, but not our own hash writes
  window.addEventListener("hashchange", function () {
    if (keyFor(location.hash) !== currentKey) route();
  });

  root.addEventListener("click", function (e) {
    var lib = e.target.closest("[data-lib]");
    if (lib) { renderLibrary(); return; }
    var go = e.target.closest("[data-go]");
    if (go) { var v = go.getAttribute("data-go").split("/"); show(v[0], v[1] || 1); }
  });

  route();
})();
