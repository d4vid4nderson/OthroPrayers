// Serverless OCR + translation for the Greek photo tool (Vercel Function).
// Uses Google Cloud Vision (DOCUMENT_TEXT_DETECTION) + Cloud Translation v2.
//
// SETUP (one time):
//   1. Create a Google Cloud project; enable the "Cloud Vision API" and the
//      "Cloud Translation API".
//   2. Create an API key (APIs & Services -> Credentials). Under "API
//      restrictions", restrict it to just those two APIs.
//   3. In Vercel -> Project -> Settings -> Environment Variables, add
//      GOOGLE_API_KEY = <the key>, then redeploy.
//
// Free tiers (per month): Vision ~1,000 images, Translation ~500k characters;
// modest cost beyond that. The key stays server-side and is never sent to the
// browser. Until it is set, this returns 503 and the client falls back to the
// on-device reader.
module.exports = async (req, res) => {
  const key = process.env.GOOGLE_API_KEY;
  // health check: visit /api/greek to confirm the function is deployed and
  // whether the key is wired. Visit /api/greek?test=1 to actually exercise the
  // Cloud Translation API and see whether it (not just Vision) works — the key
  // itself is never returned.
  if (req.method === "GET") {
    if (key && /[?&]test=1\b/.test(req.url || "")) {
      try {
        const tr = await fetch("https://translation.googleapis.com/language/translate/v2?key=" + key, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ q: "καλημέρα", source: "el", target: "en", format: "text" })
        });
        const tj = await tr.json();
        const t0 = tj && tj.data && tj.data.translations && tj.data.translations[0];
        res.status(200).json({
          ok: true, configured: true, translateStatus: tr.status,
          translateOk: !!(t0 && t0.translatedText),
          sample: (t0 && t0.translatedText) || null,
          error: (tj && tj.error && tj.error.message) || null
        });
      } catch (e) { res.status(200).json({ ok: true, configured: true, translateOk: false, error: String(e) }); }
      return;
    }
    res.status(200).json({ ok: true, configured: !!key }); return;
  }
  if (req.method !== "POST") { res.status(405).json({ error: "POST only" }); return; }
  if (!key) { res.status(503).json({ error: "not_configured" }); return; }
  try {
    let body = req.body;
    if (typeof body === "string") { try { body = JSON.parse(body); } catch (e) { body = {}; } }
    let content = (body && body.image) || "";
    content = String(content).replace(/^data:[^,]+,/, "");   // strip data-URL prefix
    if (!content) { res.status(400).json({ error: "no_image" }); return; }

    const vis = await fetch("https://vision.googleapis.com/v1/images:annotate?key=" + key, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        requests: [{
          image: { content },
          features: [{ type: "DOCUMENT_TEXT_DETECTION" }],
          imageContext: { languageHints: ["el", "grc"] }
        }]
      })
    });
    const vj = await vis.json();
    const r0 = vj && vj.responses && vj.responses[0];
    const greek = ((r0 && r0.fullTextAnnotation && r0.fullTextAnnotation.text) || "").trim();
    if (!greek) { res.status(200).json({ greek: "", english: "" }); return; }

    let english = "", tnote = null;
    const tr = await fetch("https://translation.googleapis.com/language/translate/v2?key=" + key, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q: greek, source: "el", target: "en", format: "text" })
    });
    const tj = await tr.json();
    const t0 = tj && tj.data && tj.data.translations && tj.data.translations[0];
    if (t0 && t0.translatedText) english = t0.translatedText;
    // when translation fails (e.g. the Cloud Translation API isn't enabled, or
    // the key is restricted to Vision only), pass the reason back for debugging
    else tnote = (tj && tj.error && tj.error.message) || ("translate http " + tr.status);

    res.status(200).json({ greek, english, tnote });
  } catch (e) {
    res.status(500).json({ error: "failed" });
  }
};
