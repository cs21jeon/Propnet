// Proptalk PWA Service Worker
const CACHE_NAME = 'proptalk-web-v1';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
    // Network-first strategy for API calls, cache-first for static assets
    if (event.request.url.includes('/api/') || event.request.url.includes('/socket.io/')) {
        return; // Let network handle API and WebSocket
    }
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});
