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
  // health check: visit /api/greek in a browser to confirm the function is
  // deployed and whether the key is wired (the key itself is never returned)
  if (req.method === "GET") { res.status(200).json({ ok: true, configured: !!key }); return; }
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

    let english = "";
    const tr = await fetch("https://translation.googleapis.com/language/translate/v2?key=" + key, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q: greek, source: "el", target: "en", format: "text" })
    });
    const tj = await tr.json();
    const t0 = tj && tj.data && tj.data.translations && tj.data.translations[0];
    if (t0 && t0.translatedText) english = t0.translatedText;

    res.status(200).json({ greek, english });
  } catch (e) {
    res.status(500).json({ error: "failed" });
  }
};
