const CACHE_NAME = 'hufspace-cache-v2';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/HUFSFont.ttf',
  '/static/Symbol.png',
  '/static/HUFS.png',
  '/static/manifest-v2.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
