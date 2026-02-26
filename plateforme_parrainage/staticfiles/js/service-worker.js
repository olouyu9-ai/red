/**
 * Service Worker pour Genius Africa PWA
 * Gère le cache et l'affichage hors ligne
 * Version: 1.1.0
 */

const CACHE_NAME = 'genius-africa-v1.1';
const OFFLINE_URL = '/offline/';
const RUNTIME_CACHE = 'genius-africa-runtime-v1';

// Fichiers critiques à mettre en cache lors de l'installation
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/css/dashboard.css',
  '/static/css/pages.css',
  '/static/css/connexion.css',
  '/static/css/accueil.css',
  '/static/js/theme.js',
  '/static/js/pwa.js',
  '/static/image/Genius_Africa.png',
  '/offline/',
  '/manifest.json'
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installation - Version', CACHE_NAME);
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Mise en cache des fichiers critiques');
        // Utiliser addAll avec gestion d'erreur individuelle
        return Promise.allSettled(
          urlsToCache.map(url => 
            cache.add(url).catch(err => {
              console.warn(`[Service Worker] Impossible de mettre en cache ${url}:`, err);
              return null;
            })
          )
        );
      })
      .then(() => {
        console.log('[Service Worker] Installation terminée');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[Service Worker] Erreur lors de l\'installation:', error);
        // Ne pas bloquer l'installation même en cas d'erreur
        return self.skipWaiting();
      })
  );
});

// Activation du Service Worker
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activation - Version', CACHE_NAME);
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Supprimer tous les anciens caches
          if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
            console.log('[Service Worker] Suppression de l\'ancien cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
    .then(() => {
      console.log('[Service Worker] Activation terminée');
      return self.clients.claim();
    })
    .catch((error) => {
      console.error('[Service Worker] Erreur lors de l\'activation:', error);
      return self.clients.claim();
    })
  );
});

// Interception des requêtes réseau
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorer les requêtes non-GET (POST, PUT, DELETE, etc.)
  if (request.method !== 'GET') {
    return;
  }

  // Ignorer les requêtes vers l'API, admin, connexion (pour éviter les problèmes CSRF), et les fichiers non-HTTP
  // IMPORTANT: Ne JAMAIS mettre en cache les pages de connexion/déconnexion pour éviter les problèmes CSRF
  if (url.pathname.startsWith('/api/') || 
      url.pathname.startsWith('/admin/') ||
      url.pathname === '/connexion/' ||
      url.pathname.startsWith('/connexion/') ||
      url.pathname === '/deconnexion/' ||
      url.pathname.startsWith('/deconnexion/') ||
      url.pathname.startsWith('/inscription/') ||
      url.pathname.startsWith('/comptes/inscription') ||
      url.protocol !== 'http:' && url.protocol !== 'https:') {
    // Supprimer de tous les caches si présent (au cas où)
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          return caches.open(cacheName).then((cache) => {
            return cache.delete(request);
          });
        })
      );
    }).catch(() => {
      // Ignorer les erreurs
    });
    // Ne pas intercepter ces requêtes du tout - laisser passer directement
    return;
  }

  // Stratégie: Cache First pour les ressources statiques, Network First pour les pages
  event.respondWith(
    (async () => {
      // Pour les ressources statiques (CSS, JS, images), utiliser Cache First
      if (url.pathname.startsWith('/static/') || 
          url.pathname.startsWith('/media/') ||
          url.pathname.endsWith('.png') ||
          url.pathname.endsWith('.jpg') ||
          url.pathname.endsWith('.jpeg') ||
          url.pathname.endsWith('.gif') ||
          url.pathname.endsWith('.svg') ||
          url.pathname.endsWith('.css') ||
          url.pathname.endsWith('.js')) {
        
        // Cache First
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
          return cachedResponse;
        }

        try {
          const networkResponse = await fetch(request);
          if (networkResponse && networkResponse.status === 200) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, networkResponse.clone());
          }
          return networkResponse;
        } catch (error) {
          console.warn('[Service Worker] Erreur réseau pour ressource statique:', request.url);
          // Retourner une réponse par défaut si possible
          if (request.destination === 'image') {
            return new Response('', { status: 404 });
          }
          throw error;
        }
      }

      // Pour les pages HTML, utiliser Network First avec fallback cache
      try {
        // Essayer d'abord le réseau
        const networkResponse = await fetch(request);
        
        // Mettre en cache les réponses réussies
        if (networkResponse && networkResponse.status === 200) {
          const cache = await caches.open(RUNTIME_CACHE);
          cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
      } catch (error) {
        console.log('[Service Worker] Hors ligne, recherche dans le cache:', request.url);
        
        // Si hors ligne, chercher dans le cache
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
          return cachedResponse;
        }

        // Si c'est une navigation et qu'on n'a pas de cache, afficher la page offline
        if (request.mode === 'navigate') {
          const offlinePage = await caches.match(OFFLINE_URL);
          if (offlinePage) {
            return offlinePage;
          }
        }

        // Fallback: réponse d'erreur
        return new Response('Ressource non disponible hors ligne', {
          status: 503,
          statusText: 'Service Unavailable',
          headers: new Headers({
            'Content-Type': 'text/plain; charset=utf-8'
          })
        });
      }
    })()
  );
});

// Gestion des messages depuis le client
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message reçu:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'SKIP_CACHE') {
    // Ne pas mettre en cache cette URL
    console.log('[Service Worker] Skip cache pour:', event.data.url);
    // Supprimer de tous les caches si présent
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          return caches.open(cacheName).then((cache) => {
            return cache.delete(event.data.url);
          });
        })
      );
    });
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => caches.delete(cacheName))
      );
    }).then(() => {
      console.log('[Service Worker] Cache vidé');
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({ success: true });
      }
    });
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    if (event.ports && event.ports[0]) {
      event.ports[0].postMessage({ version: CACHE_NAME });
    }
  }
});

// Notification de mise à jour disponible
self.addEventListener('updatefound', () => {
  console.log('[Service Worker] Nouvelle version disponible');
});

// Gestion des erreurs non capturées
self.addEventListener('error', (event) => {
  console.error('[Service Worker] Erreur non capturée:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
  console.error('[Service Worker] Promise rejetée non gérée:', event.reason);
});
