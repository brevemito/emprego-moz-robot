/* =========================================================================
   Brevemito Vagas — service worker
   - Guarda a "casca" do site (HTML, CSS, JS, ícones) para abrir depressa.
   - Vagas e bolsas (jobs.json, bolsas.json): tenta sempre a rede primeiro
     e, sem internet, mostra a última lista guardada.
   Para forçar todos os telemóveis a buscar ficheiros novos, aumente VERSION.
   ========================================================================= */

const VERSION = "bm-v2";
const SHELL = [
  "./",
  "index.html",
  "styles.css",
  "bolsas.css",
  "design.css",
  "novidades.css",
  "app.js",
  "extras.js",
  "bolsas.js",
  "manifest.webmanifest",
  "icon-192.png",
  "icon-512.png",
  "apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function isData(url) {
  return url.hostname === "raw.githubusercontent.com" && url.pathname.endsWith(".json");
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Dados: rede primeiro; sem rede, a última cópia (ignora o ?t=...).
  if (isData(url)) {
    const key = url.origin + url.pathname;
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(VERSION).then((c) => c.put(key, copy));
          }
          return res;
        })
        .catch(() => caches.match(key))
    );
    return;
  }

  // Ficheiros do próprio site: mostra o guardado e actualiza em segundo plano.
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(req, { ignoreSearch: true }).then((cached) => {
        const network = fetch(req)
          .then((res) => {
            if (res.ok && res.type === "basic") {
              const copy = res.clone();
              caches.open(VERSION).then((c) => c.put(req, copy));
            }
            return res;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
  }
});
