const CACHE_NAME = "smart-restaurant-v3";
const ASSETS = [
  "/app/",
  "/app/index.html",
  "/app/styles.css",
  "/app/shared/shared.jsx",
  "/app/views/customer.jsx",
  "/app/views/admin.jsx",
  "/app/views/kitchen.jsx",
  "/app/views/landing.jsx",
  "/app/app.jsx",
  "/app/vendor/react.production.min.js",
  "/app/vendor/react-dom.production.min.js",
  "/app/vendor/babel.min.js",
  "/app/manifest.json",
  "/app/icon.svg"
];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request))
  );
});
