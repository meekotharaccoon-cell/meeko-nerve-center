// SolarPunk Mycelium — Service Worker
// Enables: offline access, background sync, push notifications

const CACHE_NAME = 'mycelium-v1';
const OFFLINE_URLS = [
  '/meeko-nerve-center/app.html',
  '/meeko-nerve-center/manifest.json',
  'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;700&family=Fraunces:ital,wght@0,300;0,600;1,300&display=swap',
];

// Install: cache essential files
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(OFFLINE_URLS).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

// Activate: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch: network first, cache fallback
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

// Push notifications
self.addEventListener('push', event => {
  const data = event.data?.json() || {};
  event.waitUntil(
    self.registration.showNotification(
      data.title || 'SolarPunk Mycelium',
      {
        body: data.body || 'System update',
        icon: '/meeko-nerve-center/manifest.json',
        badge: '/meeko-nerve-center/manifest.json',
        data: { url: data.url || '/meeko-nerve-center/app.html' },
        actions: [
          { action: 'open', title: 'Open' },
          { action: 'dismiss', title: 'Dismiss' }
        ]
      }
    )
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action !== 'dismiss') {
    const url = event.notification.data?.url || '/meeko-nerve-center/app.html';
    event.waitUntil(clients.openWindow(url));
  }
});
