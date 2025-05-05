const CACHE_NAME = 'byteme-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/static/index.html',
  '/static/sw.js',
  '/static/manifest.json',
  '/static/favicon.png',
  'https://cdn.tailwindcss.com',
  'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs/loader.min.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for offline operations
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-code-execution') {
        event.waitUntil(
            // Handle background sync
            // This would be implemented based on your specific needs
            Promise.resolve()
        );
    }
});

// Push notification handling
self.addEventListener('push', (event) => {
    const options = {
        body: event.data.text(),
        icon: '/favicon.png',
        badge: '/favicon.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        }
    };

    event.waitUntil(
        self.registration.showNotification('ByteMe', options)
    );
}); 