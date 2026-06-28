/* Greek photo translator (Resources tool). Photo -> light image clean-up ->
 * on-device OCR (Tesseract.js, modern Greek) -> transliteration + a rough
 * inline translation, with a one-tap hand-off to Google Translate (much better
 * quality). Online-only and approximate; best on clear, printed Greek. */
(function () {
  var fileIn, img, status, spin, gEl, tEl, enEl, gt, go;
  function $(id) { return document.getElementById(id); }

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

  // busy = show the spinner (a working state); omitted/false hides it
  function setStatus(t, busy) {
    if (status) status.textContent = t || "";
    if (spin) spin.hidden = !busy;
  }

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

  // grayscale + contrast + sensible scale — OCR is far better on a clean,
  // high-contrast image at a workable size
  function prep(src) {
    return new Promise(function (res) {
      var im = new Image();
      im.onload = function () {
        var w = im.width, h = im.height, mx = 1800, mn = 1100, s = 1;
        if (Math.max(w, h) > mx) s = mx / Math.max(w, h);
        else if (Math.max(w, h) < mn) s = mn / Math.max(w, h);
        var c = document.createElement("canvas");
        c.width = Math.round(w * s); c.height = Math.round(h * s);
        var x = c.getContext("2d");
        x.drawImage(im, 0, 0, c.width, c.height);
        try {
          var d = x.getImageData(0, 0, c.width, c.height), a = d.data, i, g;
          for (i = 0; i < a.length; i += 4) {
            g = 0.299 * a[i] + 0.587 * a[i + 1] + 0.114 * a[i + 2];
            g = (g - 128) * 1.6 + 128;            // boost contrast
            g = g < 0 ? 0 : g > 255 ? 255 : g;
            a[i] = a[i + 1] = a[i + 2] = g;
          }
          x.putImageData(d, 0, 0);
        } catch (e) { /* tainted canvas etc. — fall back to the raw draw */ }
        res(c);
      };
      im.onerror = function () { res(null); };
      im.src = (typeof src === "string") ? src : URL.createObjectURL(src);
    });
  }

  function googleUrl(text) {
    return "https://translate.google.com/?sl=el&tl=en&op=translate&text=" + encodeURIComponent(text.replace(/\s+/g, " ").trim());
  }

  // high-accuracy path: send the photo to the server (Google Vision + Translate);
  // returns {greek, english} or null if the backend isn't configured / fails
  function tryBackend(dataURL) {
    return fetch("api/greek", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataURL })
    }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { return (j && typeof j.greek === "string") ? j : null; })
      .catch(function () { return null; });
  }

  function process(src) {
    gEl.value = ""; tEl.textContent = ""; enEl.textContent = ""; gt.hidden = true;
    setStatus("Reading the Greek…", true);
    prep(src).then(function (canvas) {
      var durl = canvas ? canvas.toDataURL("image/jpeg", 0.85) : null;
      return (durl ? tryBackend(durl) : Promise.resolve(null)).then(function (best) {
        if (best && best.greek) {                 // server read it
          gEl.value = best.greek; tEl.textContent = translit(best.greek);
          enEl.textContent = best.english || "";
          gt.href = googleUrl(best.greek); gt.hidden = false;
          setStatus("");
          return;
        }
        return ocrFallback(canvas || src);         // on-device reader
      });
    }).catch(function () { setStatus("Couldn’t read the image. Check your connection."); });
  }

  function ocrFallback(imgSrc) {
    setStatus("Reading the Greek…", true);
    return loadTesseract().then(function () {
      return Tesseract.recognize(imgSrc, "ell", {
        logger: function (m) {
          if (m.status === "recognizing text") setStatus("Reading the Greek… " + Math.round(m.progress * 100) + "%", true);
        }
      });
    }).then(function (r) {
      var text = ((r && r.data && r.data.text) || "").replace(/[ \t]+\n/g, "\n").trim();
      if (!text) { setStatus("No Greek text found — try a clearer, straight-on, well-lit photo."); return; }
      gEl.value = text; tEl.textContent = translit(text);
      translate(text);
    }).catch(function () {
      setStatus("Couldn’t read the image. This tool needs an internet connection.");
    });
  }

  function translate(text) {
    // keep line breaks (collapse only runs of spaces/tabs) so lists/verses stay
    // legible line-by-line instead of one justified blob
    var clean = text.replace(/[ \t]+/g, " ").replace(/[ \t]*\n[ \t]*/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
    gt.href = "https://translate.google.com/?sl=el&tl=en&op=translate&text=" + encodeURIComponent(clean);
    gt.hidden = false;
    setStatus("Translating…", true);
    fetch("https://api.mymemory.translated.net/get?langpair=el|en&q=" + encodeURIComponent(clean.slice(0, 480)))
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var en = j && j.responseData && j.responseData.translatedText;
        var bad = !en || (j.responseStatus && j.responseStatus !== 200) ||
                  /MYMEMORY WARNING|INVALID|PLEASE SELECT|^[\s?]*$/i.test(en);
        enEl.textContent = bad
          ? "A reliable translation isn’t available here — tap “Open in Google Translate” below for a much better result."
          : en + (clean.length > 480 ? " …" : "");
        setStatus("");
      })
      .catch(function () {
        enEl.textContent = "";
        setStatus("Couldn’t translate here — open in Google Translate, or check your connection.");
      });
  }

  function ready() {
    fileIn = $("gk-file"); img = $("gk-img"); status = $("gk-status"); spin = $("gk-spin");
    gEl = $("gk-greek"); tEl = $("gk-translit"); enEl = $("gk-en");
    gt = $("gk-gt"); go = $("gk-go");
    if (!fileIn) return;
    fileIn.addEventListener("change", onFile);
    if (go) go.onclick = function () { var t = gEl.value.trim(); if (t) translate(t); };
    var handed = sessionStorage.getItem("gk-photo");
    if (handed) {
      sessionStorage.removeItem("gk-photo");
      img.src = handed; img.hidden = false;
      process(handed);
    }
  }

  function onFile() {
    var f = fileIn.files && fileIn.files[0];
    if (!f) return;
    img.src = URL.createObjectURL(f); img.hidden = false;
    process(f);
  }

  if (document.readyState !== "loading") ready();
  else document.addEventListener("DOMContentLoaded", ready);
})();
