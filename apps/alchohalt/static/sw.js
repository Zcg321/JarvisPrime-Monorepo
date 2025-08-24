const CACHE = 'alchohalt-ui-v1';
const DB = 'alchohalt';
const STORE = 'checkin-queue';

function db() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { autoIncrement: true });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function queue(body) {
  const d = await db();
  const tx = d.transaction(STORE, 'readwrite');
  tx.objectStore(STORE).add(body);
  const countReq = tx.objectStore(STORE).count();
  countReq.onsuccess = () => console.log('queue length', countReq.result);
}

async function flush() {
  const d = await db();
  const tx = d.transaction(STORE, 'readwrite');
  const store = tx.objectStore(STORE);
  const all = await store.getAll();
  if (!all.length) return;
  const groups = {};
  all.forEach(i => {
    (groups[i.user_id] = groups[i.user_id] || []).push(i);
  });
  for (const [uid, items] of Object.entries(groups)) {
    const body = { user_id: Number(uid), items: items.map(i => ({ date: i.date, status: i.status, note: i.note })) };
    const res = await fetch('/alchohalt/checkins/bulk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error('bulk failed');
  }
  await store.clear();
  console.log('queue length', 0);
}

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method === 'POST' && url.pathname.startsWith('/alchohalt/checkins')) {
    event.respondWith(
      fetch(event.request.clone()).catch(async () => {
        const body = await event.request.clone().json();
        await queue(body);
        return new Response(JSON.stringify({ queued: true }), { headers: { 'Content-Type': 'application/json' } });
      })
    );
    return;
  }
  if (event.request.method === 'GET' && url.pathname.startsWith('/alchohalt/ui')) {
    event.respondWith(
      caches.open(CACHE).then(cache => cache.match(event.request).then(resp => resp || fetch(event.request).then(network => { cache.put(event.request, network.clone()); return network; })))
    );
  }
});

self.addEventListener('sync', event => {
  if (event.tag === 'alchohalt-sync') {
    event.waitUntil(flush().catch(() => {}));
  }
});

self.addEventListener('message', event => {
  if (event.data === 'online') {
    flush().catch(() => {});
  }
});
