// Service Worker — 数学冒险世界 PWA
// 策略: 静态资源 Cache-First / API Network-First / 离线回退 / Push Notification

const CACHE_NAME = 'math-adventure-v2';
const STATIC_ASSETS = ['/', '/index.html', '/favicon.svg'];

// ===== Install: 预缓存静态资源 =====
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {
        // 单个资源失败不阻塞 SW 安装
      });
    }).then(() => {
      // @ts-ignore
      self.skipWaiting();
    })
  );
});

// ===== Activate: 清理旧缓存 =====
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n))
      );
    }).then(() => {
      // @ts-ignore
      self.clients.claim();
    })
  );
});

// ===== Fetch: 分层策略 =====
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 非 GET 请求走网络
  if (request.method !== 'GET') return;

  // API 请求: Network-First（3 秒超时回退缓存）
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // 静态资源: Cache-First
  event.respondWith(cacheFirst(request));
});

// ===== 策略函数 =====
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    // 离线 + 无缓存 → 返回离线页面或空响应
    return new Response('Offline', { status: 503 });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response(JSON.stringify({ error: 'offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

// ===== Push Notification =====
self.addEventListener('push', (event) => {
  if (!event.data) return;
  try {
    const payload = event.data.json();
    const title = payload.title || '数学冒险世界';
    const options = {
      body: payload.body || '',
      icon: '/favicon.svg',
      badge: '/favicon.svg',
      tag: payload.tag || 'default',
      data: payload.url || '/',
      vibrate: [200, 100, 200],
      requireInteraction: payload.requireInteraction || false,
    };
    event.waitUntil(self.registration.showNotification(title, options));
  } catch {
    // 非 JSON payload → 显示纯文本
    event.waitUntil(
      self.registration.showNotification('数学冒险世界', {
        body: event.data.text(),
        icon: '/favicon.svg',
      })
    );
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      for (const client of clients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(url);
      }
    })
  );
});

// ===== Push Subscription Sync =====
self.addEventListener('pushsubscriptionchange', (event) => {
  event.waitUntil(
    fetch('/api/v1/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subscription: self.registration.pushManager.getSubscription() }),
    })
  );
});
