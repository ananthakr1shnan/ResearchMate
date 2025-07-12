// ResearchMate Service Worker
// Simple service worker to prevent 404 errors

self.addEventListener('install', function(event) {
    console.log('Service Worker installed');
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    console.log('Service Worker activated');
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function(event) {
    // For now, just let all requests pass through
    // Future: Add caching strategy here
    return;
});
