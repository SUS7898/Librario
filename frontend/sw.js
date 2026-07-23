/* Librario 서비스워커
   - 앱 셸(app.js/css/html)은 network-first: 배포하면 새로고침 없이 최신 반영.
   - 대용량 리더 라이브러리(vendor)·아이콘은 cache-first: 불변이라 캐시가 이득(오프라인 가능).
   - API/미디어(책 파일)는 캐시하지 않음(인증/최신성/대용량).
*/
const CACHE = 'librario-shell-v8';
const SHELL = [
  '/', '/index.html',
  '/assets/app.css', '/assets/app.js',
  '/assets/icon-192.png', '/assets/icon-512.png',
  '/manifest.webmanifest',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('message', e => {
  if (e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function isShell(p){
  return p === '/' || p === '/index.html' || p === '/manifest.webmanifest'
      || p === '/assets/app.js' || p === '/assets/app.css';
}
function isImmutable(p){
  return p.startsWith('/assets/vendor/') || (p.startsWith('/assets/') && p.endsWith('.png'));
}

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (url.pathname.startsWith('/api/')) return;   // API/미디어는 항상 네트워크

  // 불변 자원(vendor 라이브러리, 아이콘): 캐시 우선
  if (isImmutable(url.pathname)) {
    e.respondWith(
      caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {});
        return res;
      }))
    );
    return;
  }

  // 앱 셸: 네트워크 우선(최신 코드), 실패 시 캐시로 폴백 → 배포 즉시 반영 + 오프라인 동작
  if (isShell(url.pathname)) {
    e.respondWith(
      fetch(e.request).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match(e.request).then(hit => hit || caches.match('/index.html')))
    );
    return;
  }

  // 그 외(SPA 라우트): 네트워크, 실패 시 index.html
  e.respondWith(fetch(e.request).catch(() => caches.match('/index.html')));
});
