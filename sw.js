const CACHE="ortho-c91364e52c";
const ASSETS=["./", "af-communion.html", "af-confession.html", "af-departed.html", "af-evening.html", "af-meals.html", "af-midday.html", "af-morning.html", "af-night.html", "af-occasions.html", "af-precommunion.html", "af-saints.html", "af-thanksgiving.html", "ancient.html", "assets/icons/apple-touch-icon.png", "assets/icons/favicon-16.png", "assets/icons/favicon-32.png", "assets/icons/icon-192-maskable.png", "assets/icons/icon-192.png", "assets/icons/icon-512-maskable.png", "assets/icons/icon-512.png", "assets/img/icon_p1.png", "assets/img/icon_p15.png", "assets/img/icon_p21.png", "bible.html", "calendar-data.js", "calendar.html", "calendar.js", "calendars/orthodox-new-calendar.ics", "calendars/orthodox-old-calendar.ics", "catechisms.html", "councils.html", "creeds.html", "fathers.html", "favicon.ico", "fonts/cormorant.woff2", "fonts/ebgaramond-italic.woff2", "fonts/ebgaramond.woff2", "fonts/opendyslexic-400-italic.woff2", "fonts/opendyslexic-400-normal.woff2", "fonts/opendyslexic-700-normal.woff2", "greek-tool.js", "greek.html", "hours.html", "index.html", "morning.html", "player.js", "prayers.html", "priesthood.html", "reading.html", "resources.html", "site.webmanifest", "sleep.html", "styles.css", "table.html", "theotokos.html"];
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
