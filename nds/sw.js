// 인터넷이 없어도 열리게 하는 캐시.
// - 이 폴더 파일: 인터넷이 있으면 새 파일 먼저(3초 안), 없으면 저장본.
// - 에뮬레이터(cdn.emulatorjs.org/버전/): 버전 고정이라 한 번 받으면 저장본 사용.
// - 롬(media.githubusercontent.com)은 여기서 다루지 않음 → 페이지가 IndexedDB 에 따로 보관.
// index.html 을 고친 뒤에는 VERSION 을 바꿔야 옛 캐시가 지워집니다.
const VERSION = 'nds-2026-10-19a';
const CDN = 'https://cdn.emulatorjs.org/4.2.3/';
const FILES = ['./', './index.html', './manifest.json', './icon-180.png', './icon-192.png', './icon-512.png', './ko-KO.json'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(FILES)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION && k !== 'nds-cdn').map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function fromNetwork(req, ms) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('timeout')), ms);
    fetch(req).then((res) => { clearTimeout(t); resolve(res); }, (err) => { clearTimeout(t); reject(err); });
  });
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = req.url;

  if (url.startsWith(CDN)) {
    e.respondWith(
      caches.open('nds-cdn').then((c) => c.match(req).then((hit) => hit || fetch(req).then((res) => {
        if (res.ok) c.put(req, res.clone());
        return res;
      })))
    );
    return;
  }

  if (new URL(url).origin !== self.location.origin) return;
  e.respondWith(
    fromNetwork(req, 3000)
      .then((res) => {
        if (res.ok) { const copy = res.clone(); caches.open(VERSION).then((c) => c.put(req, copy)); }
        return res;
      })
      .catch(() => caches.match(req, { ignoreSearch: true })
        .then((hit) => hit || (req.mode === 'navigate' ? caches.match('./index.html') : Response.error())))
  );
});
