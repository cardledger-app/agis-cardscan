/* AgiS カードスキャン — オフライン用 Service Worker
   方針: network-first（オンラインなら常に最新、圏外ならキャッシュ）。
   店頭で電波が弱くても開ける／更新してもキャッシュに閉じ込められない、の両立。 */
var CACHE = 'agis-cardscan-v3';
var SHELL = [
  './index.html',
  './prices.json',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(SHELL); })
      .then(function () { return self.skipWaiting(); })
      .catch(function () { /* 1つでも落ちたら諦める（インストール自体は通す） */ })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        return k === CACHE ? null : caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  if (new URL(req.url).origin !== self.location.origin) return;

  e.respondWith(
    fetch(req).then(function (res) {
      if (res && res.ok) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req.url.split('?')[0], copy); });
      }
      return res;
    }).catch(function () {
      /* prices.json?<時刻> のようなクエリ付きでもキャッシュに当てる */
      return caches.match(req, { ignoreSearch: true }).then(function (hit) {
        return hit || caches.match('./index.html');
      });
    })
  );
});
