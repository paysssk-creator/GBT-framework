// service-worker.js — GBT 3D PWA 离线缓存
const CACHE = 'gbt3d-v16';
const ASSETS = [
  '/', '/index.html', '/showcase.html',
  '/gbt-3d.js', '/V5-3D-AI-PROTOCOL.md',
  '/manifest.json',
  'https://unpkg.com/three@0.160.0/build/three.min.js'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(res => {
      if (res.ok && e.request.url.endsWith('.glb')) {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
      }
      return res;
    }))
  );
});
