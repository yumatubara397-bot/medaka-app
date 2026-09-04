/**
 * メダカ在庫撮影アシスタント - Service Worker
 * v6: 出品タブ(Phase 3) / 履歴タブ(Phase 4) 実装。
 *     オークタウンCSV(Shift_JIS) + 画像ZIP をブラウザ内で生成、出品履歴を IndexedDB に保存
 * v5: 編集タブ(Phase 2) 実装。AI加工 + ライトボックス + IndexedDB キャッシュ
 */

const CACHE_VERSION = 'medaka-cache-v69';  // バージョン更新で古いキャッシュ自動削除
const APP_SHELL = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Noto+Sans+JP:wght@400;500;700;900&display=swap'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => {
      return Promise.all(
        APP_SHELL.map((url) =>
          cache.add(url).catch((e) => console.warn('SW skip cache:', url, e))
        )
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  if (req.method !== 'GET') return;
  if (url.hostname.includes('script.google.com')) return;
  if (url.hostname.includes('googleapis.com')) return;

  // HTML はブラウザのHTTPキャッシュを通さず、必ず取り直す。
  // これをしないと、公開し直しても古い画面が出続ける。
  const isDoc = req.mode === 'navigate'
    || (req.destination === 'document')
    || url.pathname.endsWith('/')
    || url.pathname.endsWith('.html');

  event.respondWith(
    fetch(isDoc ? new Request(req, { cache: 'reload' }) : req)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE_VERSION).then((cache) => cache.put(req, copy));
        return res;
      })
      .catch(() => caches.match(req).then((c) => c || caches.match('./index.html')))
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});
