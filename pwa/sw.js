/* Steady Voice service worker.
 *
 * The app is a handful of static files and no API, so the caching strategy is
 * the simplest one that is actually correct: precache everything on install,
 * then serve from cache first and fall back to the network.
 *
 * Cache-first matters here. This app is used in the car, at the dinner table
 * and in a school corridor — it must not blank out because the phone dropped
 * to one bar.
 *
 * GENERATED FILE — edit sw.template.js, not sw.js. build.py stamps the cache
 * name with a hash of the built app, so a redeploy always invalidates the old
 * cache. Bumping it by hand is the step everyone forgets, and forgetting it
 * means the phone happily serves last month's app forever.
 */
const CACHE = "steady-voice-d3962e7221d9";

const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon-192.png",
  "./icon-512.png",
  "./icon-512-maskable.png",
  "./apple-touch-icon.png"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE)
      // addAll is atomic: one bad URL fails the whole install, which is what we
      // want — a half-cached app that breaks offline is worse than no SW.
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;

  // Google Fonts are a progressive enhancement — the app declares real
  // fallback stacks, so never let a font request block or fail a page load.
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(req).then(hit => {
      if (hit) return hit;
      return fetch(req)
        .then(res => {
          // Cache same-origin successes so a first visit to any path warms up.
          if (res && res.ok && res.type === "basic") {
            const copy = res.clone();
            caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
          }
          return res;
        })
        // Offline and not cached: a navigation still gets the app shell,
        // so the child never sees a browser error page.
        .catch(() => req.mode === "navigate"
          ? caches.match("./index.html")
          : Response.error());
    })
  );
});
