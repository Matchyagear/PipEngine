// =============================================================================
// SHADOWBETA SERVICE WORKER - OFFLINE-FIRST PERFORMANCE
// =============================================================================

const CACHE_NAME = 'shadowbeta-v1.2.1';
const API_CACHE_NAME = 'shadowbeta-api-v1.2.1';

// Files to cache for offline functionality
const STATIC_ASSETS = [
    '/',
    '/static/js/bundle.js',
    '/static/css/main.css',
    '/manifest.json',
    '/pipengine_logo.png'
];

// API endpoints to cache for offline data
const API_ENDPOINTS = [
    '/api/market/overview/instant',
    '/api/news/general/instant'
];

// =============================================================================
// SERVICE WORKER INSTALLATION
// =============================================================================

self.addEventListener('install', (event) => {
    console.log('🔧 SERVICE WORKER: Installing...');

    event.waitUntil(
        Promise.all([
            // Cache static assets
            caches.open(CACHE_NAME).then((cache) => {
                console.log('📦 SERVICE WORKER: Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            }),

            // Pre-cache API data
            caches.open(API_CACHE_NAME).then(async (cache) => {
                console.log('📊 SERVICE WORKER: Pre-caching API data');

                for (const endpoint of API_ENDPOINTS) {
                    try {
                        const response = await fetch(`http://localhost:8000${endpoint}`);
                        if (response.ok) {
                            await cache.put(endpoint, response);
                            console.log(`✅ SERVICE WORKER: Cached ${endpoint}`);
                        }
                    } catch (error) {
                        console.log(`❌ SERVICE WORKER: Failed to cache ${endpoint}`);
                    }
                }
            })
        ]).then(() => {
            console.log('✅ SERVICE WORKER: Installation complete');
            self.skipWaiting(); // Activate immediately
        })
    );
});

// =============================================================================
// SERVICE WORKER ACTIVATION
// =============================================================================

self.addEventListener('activate', (event) => {
    console.log('🚀 SERVICE WORKER: Activating...');

    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Delete old caches
                    if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                        console.log(`🗑️ SERVICE WORKER: Deleting old cache ${cacheName}`);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('✅ SERVICE WORKER: Activation complete');
            self.clients.claim(); // Take control immediately
        })
    );
});

// =============================================================================
// NETWORK REQUEST INTERCEPTION - CACHE-FIRST STRATEGY
// =============================================================================

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Handle API requests with cache-first strategy
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
        return;
    }

    // Handle static assets with cache-first strategy
    event.respondWith(handleStaticRequest(request));
});

async function handleApiRequest(request) {
    const url = new URL(request.url);

    // For instant endpoints (except scan), try cache first for ultra-fast loading
    if (url.pathname.includes('/instant') && !url.pathname.includes('/scan')) {
        try {
            // Try cache first
            const cache = await caches.open(API_CACHE_NAME);
            const cachedResponse = await cache.match(request);

            if (cachedResponse) {
                console.log(`⚡ SERVICE WORKER: Serving ${url.pathname} from cache`);

                // Update cache in background
                updateCacheInBackground(request, cache);

                return cachedResponse;
            }
        } catch (error) {
            console.log(`❌ SERVICE WORKER: Cache error for ${url.pathname}`);
        }
    }

    // Fallback to network
    try {
        // For scan endpoints, add cache-busting to ensure fresh data
        let fetchRequest = request;
        if (url.pathname.includes('/scan') && !url.pathname.includes('/instant')) {
            const urlWithCacheBust = new URL(request.url);
            urlWithCacheBust.searchParams.set('_t', Date.now());
            fetchRequest = new Request(urlWithCacheBust.toString(), request);
        }

        const response = await fetch(fetchRequest);

        // Cache successful responses (but not scan endpoints)
        if (response.ok && request.method === 'GET' && !url.pathname.includes('/scan')) {
            const cache = await caches.open(API_CACHE_NAME);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        console.log(`❌ SERVICE WORKER: Network error for ${url.pathname}`);

        // Return cached version if available
        const cache = await caches.open(API_CACHE_NAME);
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            console.log(`📱 SERVICE WORKER: Serving offline data for ${url.pathname}`);
            return cachedResponse;
        }

        // Return offline fallback
        return new Response(
            JSON.stringify({
                error: 'Offline - data not available',
                cached: false,
                timestamp: new Date().toISOString()
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

async function handleStaticRequest(request) {
    try {
        // Try cache first
        const cache = await caches.open(CACHE_NAME);
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // Fallback to network
        const response = await fetch(request);

        // Cache successful responses
        if (response.ok) {
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        // Return cached version if available
        const cache = await caches.open(CACHE_NAME);
        return await cache.match(request) || new Response('Offline');
    }
}

async function updateCacheInBackground(request, cache) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            await cache.put(request, response);
            console.log(`🔄 SERVICE WORKER: Background cache update for ${request.url}`);
        }
    } catch (error) {
        console.log(`❌ SERVICE WORKER: Background update failed for ${request.url}`);
    }
}

// =============================================================================
// BACKGROUND SYNC FOR OFFLINE ACTIONS
// =============================================================================

self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        console.log('🔄 SERVICE WORKER: Background sync triggered');
        event.waitUntil(performBackgroundSync());
    }
});

async function performBackgroundSync() {
    try {
        // Refresh critical API caches
        const cache = await caches.open(API_CACHE_NAME);

        for (const endpoint of API_ENDPOINTS) {
            try {
                const response = await fetch(`http://localhost:8000${endpoint}`);
                if (response.ok) {
                    await cache.put(endpoint, response);
                    console.log(`✅ SERVICE WORKER: Background sync updated ${endpoint}`);
                }
            } catch (error) {
                console.log(`❌ SERVICE WORKER: Background sync failed for ${endpoint}`);
            }
        }
    } catch (error) {
        console.log('❌ SERVICE WORKER: Background sync error:', error);
    }
}

// =============================================================================
// PUSH NOTIFICATIONS (Future Enhancement)
// =============================================================================

self.addEventListener('push', (event) => {
    const data = event.data?.json() || {};

    const options = {
        body: data.body || 'Market update available',
        icon: '/pipengine_logo.png',
        badge: '/pipengine_logo.png',
        data: data.data || {},
        actions: [
            {
                action: 'view',
                title: 'View Dashboard'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(
            data.title || 'ShadowBeta Update',
            options
        )
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

console.log('🎯 SERVICE WORKER: ShadowBeta Performance Service Worker loaded');
