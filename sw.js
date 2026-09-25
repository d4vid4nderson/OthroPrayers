const CACHE="ortho-6c47a79e24";
const ASSETS=["./", "assets/icons/apple-touch-icon.png", "assets/icons/favicon-16-dark.png", "assets/icons/favicon-16.png", "assets/icons/favicon-32-dark.png", "assets/icons/favicon-32.png", "assets/icons/icon-192-maskable.png", "assets/icons/icon-192.png", "assets/icons/icon-512-maskable.png", "assets/icons/icon-512.png", "assets/img/icon_p1-mask.png", "assets/img/icon_p1.png", "assets/img/icon_p15-mask.png", "assets/img/icon_p15.png", "assets/img/icon_p21.png", "assets/img/spm-cross-mask.png", "assets/img/spm-cross.jpg", "calendar-data.js", "calendar.js", "favicon.ico", "fonts/cormorant.woff2", "fonts/ebgaramond-italic.woff2", "fonts/ebgaramond.woff2", "fonts/imfell-sc.woff2", "fonts/inter.woff2", "fonts/opendyslexic-400-italic.woff2", "fonts/opendyslexic-400-normal.woff2", "fonts/opendyslexic-700-normal.woff2", "fonts/uncial-antiqua.woff2", "index.html", "pb-duties.html", "pb-evening.html", "pb-general.html", "pb-morning.html", "pb-noon.html", "prayerbook.html", "sanctuary.css", "site.webmanifest", "spm-angelus.html", "spm-asperges.html", "spm-before-mass.html", "spm-mass-essay.html", "spm-regina-caeli.html", "spm-vidi-aquam.html", "spm-welcome.html", "st-peter-missal.html", "styles.css", "themes.css", "western-compline.html", "western-fasting.html"];
self.addEventListener("install", function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(ASSETS); })
    .then(function(){ return self.skipWaiting(); }));
});
self.addEventListener("activate", function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.map(function(k){ if(k!==CACHE && k.indexOf("ortho-")===0) return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});
self.addEventListener("fetch", function(e){
  var req=e.request;
  if(req.method!=="GET") return;
  if(new URL(req.url).origin!==location.origin) return;   // external links use the network
  e.respondWith(caches.match(req, {ignoreSearch:true}).then(function(hit){
    if(hit) return hit;
    return fetch(req).then(function(res){
      if(res && res.status===200 && res.type==="basic"){
        var copy=res.clone(); caches.open(CACHE).then(function(c){ c.put(req, copy); });
      }
      return res;
    }).catch(function(){
      if(req.mode==="navigate") return caches.match("index.html");
      return Response.error();
    });
  }));
});
