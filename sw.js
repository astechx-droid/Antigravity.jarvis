/* Minimal service worker for Android home-screen install */
const CACHE = 'jarvis-v1';
const ASSETS = ['/', '/index.html', '/style.css', '/script.js', '/jarvis-bg.js', '/manifest.json'];

self.addEventListener('install', (e) => {
    e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).catch(() => {}));
});

self.addEventListener('fetch', (e) => {
    if (e.request.method !== 'GET') return;
    e.respondWith(
        caches.match(e.request).then((r) => r || fetch(e.request).catch(() => caches.match('/index.html')))
    );
});
