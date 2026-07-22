/* Librario 서비스워커
   - 앱 셸(정적 자원)만 캐시. API/이미지/책 파일은 절대 캐시하지 않음(권한/대용량 문제).
*/
const CACHE = 'librario-shell-v2';
const SHELL = [
  '/', '/index.html',
  '/assets/app.css', '/assets/app.js',
  '/assets/icon-192.png', '/assets/icon-512.png',
  '/manifest.webmanifest',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // API 와 미디어는 항상 네트워크 (인증/최신성/대용량)
  if (url.pathname.startsWith('/api/')) return;
  if (e.request.method !== 'GET') return;

  // 정적 자원: 캐시 우선, 없으면 네트워크 후 캐시
  if (url.pathname.startsWith('/assets/') || url.pathname === '/' ||
      url.pathname === '/index.html' || url.pathname === '/manifest.webmanifest') {
    e.respondWith(
      caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match('/index.html')))
    );
    return;
  }
  // 그 외(SPA 라우트): index.html 폴백
  e.respondWith(fetch(e.request).catch(() => caches.match('/index.html')));
});
