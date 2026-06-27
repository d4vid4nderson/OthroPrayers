/* Greek photo translator (Resources tool). Photo -> on-device OCR (Tesseract.js,
 * loaded from CDN on first use) -> transliteration + English (free MyMemory API).
 * Online-only and approximate; isolated to this page. No backend or keys. */
(function () {
  var fileIn, img, status, gEl, tEl, enEl, gt, go;
  function $(id) { return document.getElementById(id); }

  // strip Greek diacritics, then map letters to Latin
  var MAP = { "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i",
    "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o",
    "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y", "φ": "f", "χ": "ch",
    "ψ": "ps", "ω": "o" };
  function translit(s) {
    s = s.normalize("NFD").replace(/[̀-ͯ͂-ͅ]/g, "");
    return s.split("").map(function (ch) {
      var low = ch.toLowerCase(), t = MAP[low];
      if (t === undefined) return ch;
      return ch === low ? t : t.charAt(0).toUpperCase() + t.slice(1);
    }).join("");
  }

  function setStatus(t) { if (status) status.textContent = t || ""; }

  function loadTesseract() {
    return new Promise(function (res, rej) {
      if (window.Tesseract) return res();
      var s = document.createElement("script");
      s.src = "https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js";
      s.onload = function () { res(); };
      s.onerror = function () { rej(new Error("load")); };
      document.head.appendChild(s);
    });
  }

  function onFile() {
    var f = fileIn.files && fileIn.files[0];
    if (!f) return;
    img.src = URL.createObjectURL(f); img.hidden = false;
    gEl.value = ""; tEl.textContent = ""; enEl.textContent = ""; gt.hidden = true;
    setStatus("Loading the reader…");
    loadTesseract().then(function () {
      setStatus("Reading the Greek…");
      return Tesseract.recognize(f, "ell+grc", {
        logger: function (m) {
          if (m.status === "recognizing text") setStatus("Reading the Greek… " + Math.round(m.progress * 100) + "%");
        }
      });
    }).then(function (r) {
      var text = ((r && r.data && r.data.text) || "").trim();
      if (!text) { setStatus("No Greek text found — try a clearer, closer photo."); return; }
      gEl.value = text; tEl.textContent = translit(text);
      translate(text);
    }).catch(function () {
      setStatus("Couldn’t read the image. This tool needs an internet connection.");
    });
  }

  function translate(text) {
    var clean = text.replace(/\s+/g, " ").trim();
    gt.href = "https://translate.google.com/?sl=el&tl=en&op=translate&text=" + encodeURIComponent(clean);
    gt.hidden = false;
    setStatus("Translating…");
    fetch("https://api.mymemory.translated.net/get?langpair=el|en&q=" + encodeURIComponent(clean.slice(0, 480)))
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var en = j && j.responseData && j.responseData.translatedText;
        enEl.textContent = en || "(no translation)";
        setStatus(clean.length > 480 ? "Translated the first part — open in Google Translate for the rest." : "");
      })
      .catch(function () {
        setStatus("Translation needs internet — you can still copy the Greek, or open Google Translate.");
      });
  }

  function ready() {
    fileIn = $("gk-file"); img = $("gk-img"); status = $("gk-status");
    gEl = $("gk-greek"); tEl = $("gk-translit"); enEl = $("gk-en");
    gt = $("gk-gt"); go = $("gk-go");
    if (!fileIn) return;
    fileIn.addEventListener("change", onFile);
    if (go) go.onclick = function () { var t = gEl.value.trim(); if (t) translate(t); };
  }

  if (document.readyState !== "loading") ready();
  else document.addEventListener("DOMContentLoaded", ready);
})();
