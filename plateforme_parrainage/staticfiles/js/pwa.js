/**
 * Gestionnaire PWA pour Genius Africa
 * Gère l'installation, les notifications hors ligne, etc.
 */

(function() {
    'use strict';

    let deferredPrompt;
    let installButton;
    let isOnline = navigator.onLine;

    // Écouter les événements de connexion/déconnexion
    window.addEventListener('online', () => {
        isOnline = true;
        hideOfflineNotification();
        console.log('[PWA] En ligne');
    });

    window.addEventListener('offline', () => {
        isOnline = false;
        showOfflineNotification();
        console.log('[PWA] Hors ligne');
    });

    // Vérifier l'état initial
    if (!isOnline) {
        showOfflineNotification();
    }

    /**
     * Affiche la notification "Vous êtes hors ligne"
     */
    function showOfflineNotification() {
        // Supprimer l'ancienne notification si elle existe
        const existing = document.getElementById('offline-notification');
        if (existing) {
            existing.remove();
        }

        const notification = document.createElement('div');
        notification.id = 'offline-notification';
        notification.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: var(--warning);
                color: white;
                padding: var(--spacing-sm) var(--spacing-md);
                text-align: center;
                font-weight: 600;
                font-size: 0.875rem;
                z-index: 10000;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                gap: var(--spacing-sm);
            ">
                <i class="fas fa-wifi" style="font-size: 1rem;"></i>
                <span>Vous êtes hors ligne</span>
            </div>
        `;
        document.body.appendChild(notification);

        // Ajuster le padding du body pour éviter que le contenu soit caché
        document.body.style.paddingTop = '40px';
    }

    /**
     * Cache la notification "Vous êtes hors ligne"
     */
    function hideOfflineNotification() {
        const notification = document.getElementById('offline-notification');
        if (notification) {
            notification.remove();
            document.body.style.paddingTop = '';
        }
    }

    /**
     * Affiche le prompt d'installation
     */
    function showInstallPrompt() {
        // Supprimer l'ancien prompt si il existe
        const existing = document.getElementById('install-prompt');
        if (existing) {
            existing.remove();
        }

        const prompt = document.createElement('div');
        prompt.id = 'install-prompt';
        prompt.innerHTML = `
            <div style="
                position: fixed;
                bottom: 80px;
                left: var(--spacing-md);
                right: var(--spacing-md);
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius-lg);
                padding: var(--spacing-md);
                box-shadow: var(--shadow-xl);
                z-index: 9998;
                max-width: 400px;
                margin: 0 auto;
            ">
                <div style="display: flex; align-items: center; gap: var(--spacing-sm); margin-bottom: var(--spacing-sm);">
                    <i class="fas fa-download" style="color: var(--primary); font-size: 1.5rem;"></i>
                    <div style="flex: 1;">
                        <div style="font-weight: 700; color: var(--text-primary); margin-bottom: 0.25rem;">
                            Installer l'application
                        </div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">
                            Installez Genius Africa sur votre bureau pour un accès rapide
                        </div>
                    </div>
                    <button onclick="closeInstallPrompt()" style="
                        background: none;
                        border: none;
                        color: var(--text-muted);
                        cursor: pointer;
                        font-size: 1.25rem;
                        padding: 0;
                        width: 24px;
                        height: 24px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div style="display: flex; gap: var(--spacing-sm);">
                    <button onclick="installPWA(event)" style="
                        flex: 1;
                        padding: var(--spacing-sm) var(--spacing-md);
                        background: var(--primary);
                        color: white;
                        border: none;
                        border-radius: var(--border-radius);
                        font-weight: 600;
                        cursor: pointer;
                        transition: var(--transition);
                    ">
                        Installer
                    </button>
                    <button onclick="closeInstallPrompt()" style="
                        padding: var(--spacing-sm) var(--spacing-md);
                        background: var(--bg-elevated);
                        color: var(--text-primary);
                        border: 1px solid var(--border-color);
                        border-radius: var(--border-radius);
                        font-weight: 600;
                        cursor: pointer;
                        transition: var(--transition);
                    ">
                        Plus tard
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(prompt);
    }

    /**
     * Cache le prompt d'installation
     */
    window.closeInstallPrompt = function() {
        const prompt = document.getElementById('install-prompt');
        if (prompt) {
            console.log('[PWA] Fermeture du prompt personnalisé');
            prompt.style.display = 'none';
            prompt.remove();
        }
        // Sauvegarder la préférence pour ne plus afficher le prompt
        localStorage.setItem('pwa-install-dismissed', Date.now().toString());
    };

    /**
     * Installe la PWA
     */
    window.installPWA = async function(event) {
        // Empêcher le comportement par défaut si c'est un événement
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }

        console.log('[PWA] installPWA appelé');

        // Fermer immédiatement le prompt personnalisé
        closeInstallPrompt();

        // Pour iOS, utiliser la fonction d'installation iOS
        if (isIOSDevice()) {
            console.log('[PWA] Détection iOS - Déclenchement de l\'installation');
            triggerIOSInstallAction();
            return;
        }

        // Vérifier si deferredPrompt est disponible
        if (!deferredPrompt) {
            console.warn('[PWA] Pas de prompt disponible (deferredPrompt est null)');
            console.log('[PWA] Platform:', navigator.platform);
            console.log('[PWA] Is Mobile:', isMobileDevice());
            console.log('[PWA] Affichage des instructions manuelles');

            // Afficher un message d'information avec instructions claires
            if (isMobileDevice()) {
                // Instructions Android mobile
                alert(
                    'Pour installer l\'application sur votre téléphone :\n\n' +
                    '1. Appuyez sur le menu (⋮) en haut à droite de Chrome\n' +
                    '2. Sélectionnez "Installer l\'application" ou "Ajouter à l\'écran d\'accueil"\n' +
                    '3. Validez pour ajouter Genius Africa sur votre écran d\'accueil.'
                );
            } else {
                // Instructions desktop (Chrome / Edge) - Plus détaillées
                const isChrome = /Chrome/.test(navigator.userAgent) && !/Edge|Edg/.test(navigator.userAgent);
                const isEdge = /Edge|Edg/.test(navigator.userAgent);
                
                let instructions = 'Pour installer l\'application sur votre ordinateur :\n\n';
                
                if (isChrome) {
                    instructions += '1. Regardez dans la barre d\'adresse de Chrome (en haut à droite)\n';
                    instructions += '   Vous devriez voir une icône d\'installation (⊞) ou un bouton "Installer".\n';
                    instructions += '2. Cliquez sur cette icône ou le bouton "Installer".\n';
                    instructions += '3. Confirmez l\'installation de "Genius Africa".\n\n';
                    instructions += 'OU utilisez le menu (⋮) > "Installer l\'application".';
                } else if (isEdge) {
                    instructions += 'Pour installer dans Microsoft Edge :\n\n';
                    instructions += '1. Cliquez sur le menu (⋯) en haut à droite\n';
                    instructions += '2. Sélectionnez "Outils supplémentaires" (ou "More tools")\n';
                    instructions += '3. Cliquez sur "Applications" (ou "Apps")\n';
                    instructions += '4. Cliquez sur "Installer ce site en tant qu\'application"\n';
                    instructions += '5. Confirmez l\'installation de "Genius Africa"\n\n';
                    instructions += 'OU cherchez l\'icône d\'installation (⊞) dans la barre d\'adresse.';
                } else {
                    instructions += '1. Dans la barre d\'adresse de votre navigateur,\n';
                    instructions += '   cherchez l\'icône "Installer l\'application" (⊞) ou le bouton "Installer".\n';
                    instructions += '2. Cliquez dessus et confirmez l\'installation.\n\n';
                }
                
                instructions += '\nVous pourrez ensuite lancer Genius Africa comme une application de bureau.';
                
                alert(instructions);
            }
            return;
        }
        
        console.log('[PWA] deferredPrompt disponible, lancement du prompt natif...');

        try {
            console.log('[PWA] Début de l\'installation (Android/Desktop)');
            console.log('[PWA] deferredPrompt disponible:', !!deferredPrompt);
            console.log('[PWA] Type de deferredPrompt:', typeof deferredPrompt);
            console.log('[PWA] Méthode prompt disponible:', typeof deferredPrompt.prompt);
            
            if (!deferredPrompt) {
                throw new Error('deferredPrompt est null');
            }
            
            if (typeof deferredPrompt.prompt !== 'function') {
                throw new Error('deferredPrompt.prompt n\'est pas une fonction');
            }
            
            // Lancer immédiatement le prompt d'installation natif
            console.log('[PWA] Lancement du prompt d\'installation natif...');
            console.log('[PWA] Appel de deferredPrompt.prompt()...');
            
            // Appeler prompt() qui déclenche le prompt natif du navigateur
            // Cette méthode affiche le prompt natif du navigateur
            deferredPrompt.prompt();
            console.log('[PWA] Prompt natif déclenché avec succès');

            // Attendre la réponse de l'utilisateur
            console.log('[PWA] Attente de la réponse de l\'utilisateur...');
            const choiceResult = await deferredPrompt.userChoice;
            console.log('[PWA] Choix de l\'utilisateur:', choiceResult.outcome);
            
            if (choiceResult.outcome === 'accepted') {
                console.log('[PWA] Installation acceptée par l\'utilisateur');
                // L'application va s'installer automatiquement
            } else {
                console.log('[PWA] Installation refusée par l\'utilisateur');
                // Si l'utilisateur refuse, sauvegarder la préférence
                localStorage.setItem('pwa-install-dismissed', Date.now().toString());
            }

            // Réinitialiser deferredPrompt après utilisation
            deferredPrompt = null;
        } catch (error) {
            console.error('[PWA] Erreur lors de l\'installation:', error);
            // En cas d'erreur, afficher un message avec instructions
            if (isMobileDevice()) {
                alert('Erreur lors de l\'installation. Veuillez utiliser le menu de votre navigateur (⋮) et sélectionnez "Installer l\'application".');
            } else {
                alert('Erreur lors de l\'installation. Veuillez cliquer sur l\'icône d\'installation dans la barre d\'adresse de votre navigateur.');
            }
        }
    };

    /**
     * Affiche les instructions d'installation pour iOS
     */
    function showIOSInstallInstructions() {
        console.log('[PWA] showIOSInstallInstructions appelée');
        
        // Vérifier si les instructions ne sont pas déjà affichées
        const existing = document.getElementById('ios-install-instructions');
        if (existing) {
            console.log('[PWA] Instructions iOS déjà affichées');
            return;
        }
        
        console.log('[PWA] Création et affichage des instructions iOS');

        const instructions = document.createElement('div');
        instructions.id = 'ios-install-instructions';
        instructions.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.85);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: var(--spacing-md);
                animation: fadeIn 0.3s ease-out;
            ">
                <div style="
                    background: var(--bg-card);
                    border-radius: var(--border-radius-lg);
                    padding: var(--spacing-xl);
                    max-width: 420px;
                    width: 100%;
                    box-shadow: var(--shadow-xl);
                    border: 1px solid var(--border-color);
                ">
                    <div style="text-align: center; margin-bottom: var(--spacing-lg);">
                        <i class="fas fa-mobile-alt" style="font-size: 3rem; color: var(--primary); margin-bottom: var(--spacing-md);"></i>
                        <h3 style="color: var(--text-primary); margin-bottom: var(--spacing-sm); font-size: 1.5rem;">
                            Installer l'application
                        </h3>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">
                            Ajoutez Genius Africa à votre écran d'accueil
                        </p>
                    </div>
                    <ol style="color: var(--text-secondary); line-height: 2; margin-bottom: var(--spacing-xl); padding-left: var(--spacing-lg); font-size: 0.95rem;">
                        <li style="margin-bottom: var(--spacing-md);">
                            Appuyez sur le bouton <strong style="color: var(--text-primary);">Partager</strong> 
                            <i class="fas fa-share" style="color: var(--primary); margin: 0 var(--spacing-xs);"></i> 
                            en bas de l'écran Safari
                        </li>
                        <li style="margin-bottom: var(--spacing-md);">
                            Faites défiler et sélectionnez <strong style="color: var(--text-primary);">"Sur l'écran d'accueil"</strong>
                            <i class="fas fa-plus-square" style="color: var(--primary); margin-left: var(--spacing-xs);"></i>
                        </li>
                        <li>
                            Appuyez sur <strong style="color: var(--text-primary);">"Ajouter"</strong> en haut à droite
                        </li>
                    </ol>
                    <div style="display: flex; gap: var(--spacing-sm);">
                        <button onclick="triggerIOSInstallAction()" style="
                            flex: 1;
                            padding: var(--spacing-md);
                            background: var(--primary);
                            color: white;
                            border: none;
                            border-radius: var(--border-radius);
                            font-weight: 600;
                            cursor: pointer;
                            font-size: 1rem;
                            transition: var(--transition);
                        " onmouseover="this.style.background='var(--primary-hover)'" onmouseout="this.style.background='var(--primary)'">
                            Installer
                        </button>
                        <button onclick="closeIOSInstructions()" style="
                            flex: 1;
                            padding: var(--spacing-md);
                            background: var(--bg-elevated);
                            color: var(--text-primary);
                            border: 1px solid var(--border-color);
                            border-radius: var(--border-radius);
                            font-weight: 600;
                            cursor: pointer;
                            font-size: 1rem;
                            transition: var(--transition);
                        ">
                            Plus tard
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(instructions);
        
        // Ajouter l'animation fadeIn si elle n'existe pas
        if (!document.getElementById('pwa-animations')) {
            const style = document.createElement('style');
            style.id = 'pwa-animations';
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    window.triggerIOSInstallAction = function() {
        console.log('[PWA] Action d\'installation iOS déclenchée');
        console.log('[PWA] navigator.share disponible:', !!navigator.share);
        
        // Sur iOS, on peut utiliser l'API Web Share pour ouvrir le menu partage
        // qui contient l'option "Sur l'écran d'accueil"
        if (navigator.share) {
            console.log('[PWA] Ouverture du menu partage...');
            navigator.share({
                title: 'Installer Genius Africa',
                text: 'Ajoutez Genius Africa à votre écran d\'accueil',
                url: window.location.href
            }).then(() => {
                console.log('[PWA] Menu partage ouvert avec succès');
                // Fermer les instructions après avoir ouvert le menu partage
                closeIOSInstructions();
            }).catch((error) => {
                console.log('[PWA] Partage annulé ou erreur:', error);
                console.log('[PWA] Type d\'erreur:', error.name);
                // Si l'utilisateur annule, ne rien faire (les instructions restent affichées)
                if (error.name !== 'AbortError' && error.name !== 'NotAllowedError') {
                    // Pour les autres erreurs, afficher un message
                    alert('Erreur lors de l\'ouverture du menu partage. Utilisez manuellement le bouton "Partager" en bas de l\'écran Safari, puis sélectionnez "Sur l\'écran d\'accueil"');
                } else {
                    console.log('[PWA] L\'utilisateur a annulé le partage');
                }
            });
        } else {
            // Si Web Share API n'est pas disponible, afficher un message
            console.log('[PWA] Web Share API non disponible');
            alert('Pour installer l\'application:\n1. Appuyez sur le bouton "Partager" (icône carré avec flèche) en bas de l\'écran Safari\n2. Sélectionnez "Sur l\'écran d\'accueil"\n3. Appuyez sur "Ajouter"');
        }
    };

    window.closeIOSInstructions = function() {
        const instructions = document.getElementById('ios-install-instructions');
        if (instructions) {
            instructions.remove();
        }
        closeInstallPrompt();
    };

    /**
     * Enregistre le Service Worker
     */
    function registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            // Vérifier si on est en HTTPS ou localhost
            const isSecure = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
            
            if (!isSecure && !location.hostname.match(/^192\.168\.|^10\.|^172\./)) {
                console.warn('[PWA] Service Worker nécessite HTTPS (sauf localhost/IP locale). Testez avec http://localhost:8000 ou utilisez un tunnel HTTPS.');
            }
            
            navigator.serviceWorker.register('/service-worker.js')
                .then((registration) => {
                    console.log('[PWA] Service Worker enregistré avec succès:', registration.scope);

                    // Vérifier les mises à jour
                    registration.addEventListener('updatefound', () => {
                        const newWorker = registration.installing;
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                console.log('[PWA] Nouvelle version disponible');
                            }
                        });
                    });
                })
                .catch((error) => {
                    console.error('[PWA] Erreur lors de l\'enregistrement du Service Worker:', error);
                    console.log('[PWA] Astuce: Pour tester depuis un téléphone, utilisez l\'IP locale (ex: http://192.168.1.100:8000) ou un tunnel HTTPS (ngrok)');
                });
        } else {
            console.warn('[PWA] Service Worker non supporté par ce navigateur');
        }
    }

    /**
     * Vérifie si l'installation est possible
     */
    function canInstall() {
        // Vérifier si l'app est déjà installée
        if (window.matchMedia('(display-mode: standalone)').matches) {
            console.log('[PWA] canInstall: false - App déjà installée');
            return false;
        }

        // Vérifier si l'utilisateur a déjà refusé récemment
        // Mais permettre quand même l'affichage après un délai plus court pour les tests
        const dismissed = localStorage.getItem('pwa-install-dismissed');
        if (dismissed) {
            const dismissedTime = parseInt(dismissed, 10);
            const oneDay = 24 * 60 * 60 * 1000; // Réduire à 1 jour au lieu de 7 jours pour faciliter les tests
            if (Date.now() - dismissedTime < oneDay) {
                console.log('[PWA] canInstall: false - Refusé récemment (dans les dernières 24h)');
                return false;
            } else {
                // Nettoyer l'ancien refus
                localStorage.removeItem('pwa-install-dismissed');
                console.log('[PWA] Ancien refus expiré, nettoyage effectué');
            }
        }

        console.log('[PWA] canInstall: true - Installation possible');
        return true;
    }

    /**
     * Détecte si on est sur iOS
     */
    function isIOSDevice() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) || 
               (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    }

    /**
     * Détecte si on est sur un appareil mobile (Android / iOS)
     */
    function isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    /**
     * Détecte si on est sur Safari iOS
     */
    function isIOSSafari() {
        const ua = navigator.userAgent;
        const isIOS = isIOSDevice();
        const isSafari = /Safari/.test(ua) && !/Chrome|CriOS|FxiOS|OPiOS|mercury/.test(ua);
        return isIOS && isSafari;
    }

    /**
     * Initialise la PWA
     */
    function initPWA() {
        console.log('[PWA] Initialisation de la PWA');
        
        // Enregistrer le Service Worker
        registerServiceWorker();

        const isIOS = isIOSDevice();
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
        
        console.log('[PWA] iOS détecté:', isIOS);
        console.log('[PWA] App installée:', isStandalone);
        console.log('[PWA] User Agent:', navigator.userAgent);

        // Détecter si l'app est déjà installée
        if (isStandalone) {
            console.log('[PWA] Application déjà installée');
            return;
        }

        // Pour iOS, afficher les instructions d'installation automatiquement
        if (isIOS) {
            console.log('[PWA] Détection iOS - Vérification des conditions');
            if (canInstall()) {
                console.log('[PWA] Conditions remplies - Affichage des instructions iOS dans 3 secondes');
                // Attendre un peu pour que la page soit chargée
                setTimeout(() => {
                    console.log('[PWA] Affichage des instructions iOS maintenant');
                    showIOSInstallInstructions();
                }, 3000);
            } else {
                console.log('[PWA] Conditions non remplies pour iOS, mais affichage quand même après 5 secondes');
                // Afficher quand même après un délai plus long
                setTimeout(() => {
                    console.log('[PWA] Affichage forcé des instructions iOS');
                    showIOSInstallInstructions();
                }, 5000);
            }
            return; // Ne pas écouter beforeinstallprompt sur iOS
        }

        // Pour Android/Chrome/Desktop, écouter l'événement beforeinstallprompt
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('[PWA] beforeinstallprompt déclenché (Android/Chrome/Desktop)');
            e.preventDefault();
            deferredPrompt = e;
            console.log('[PWA] deferredPrompt stocké:', !!deferredPrompt);
            console.log('[PWA] Platform:', navigator.platform);
            console.log('[PWA] User Agent:', navigator.userAgent);

            // Afficher le prompt même si canInstall() retourne false
            // car l'utilisateur peut vouloir réessayer
            console.log('[PWA] Affichage du prompt dans 3 secondes');
            setTimeout(() => {
                console.log('[PWA] Affichage du prompt personnalisé maintenant');
                // Toujours afficher le prompt si deferredPrompt est disponible
                showInstallPrompt();
            }, 3000);
        });

        // Fallback pour Android/Desktop si beforeinstallprompt ne se déclenche pas
        // Afficher le prompt même sans beforeinstallprompt pour permettre l'installation manuelle
        setTimeout(() => {
            if (!isStandalone && !isIOS) {
                console.log('[PWA] Vérification du fallback après 5 secondes');
                console.log('[PWA] deferredPrompt disponible:', !!deferredPrompt);
                console.log('[PWA] canInstall():', canInstall());
                console.log('[PWA] Platform:', navigator.platform);
                console.log('[PWA] Is Mobile:', isMobileDevice());
                console.log('[PWA] Is Standalone:', isStandalone);
                
                // Vérifier si le prompt n'est pas déjà affiché
                const existing = document.getElementById('install-prompt');
                if (existing) {
                    console.log('[PWA] Prompt déjà affiché, pas besoin de le réafficher');
                    return;
                }
                
            if (!deferredPrompt) {
                console.log('[PWA] beforeinstallprompt non déclenché - Affichage du prompt manuel');
                // Sur desktop, toujours afficher le prompt pour guider l'utilisateur
                // même sans deferredPrompt, car l'utilisateur peut installer via l'icône dans la barre d'adresse
                if (!isMobileDevice()) {
                    // Desktop : toujours afficher le prompt pour guider l'utilisateur
                    console.log('[PWA] Desktop détecté - Affichage FORCÉ du prompt pour guider l\'installation');
                    setTimeout(() => {
                        showInstallPrompt();
                    }, 2000);
                } else {
                    // Mobile : afficher seulement si conditions remplies
                    if (canInstall() || !localStorage.getItem('pwa-install-dismissed')) {
                        setTimeout(() => {
                            showInstallPrompt();
                        }, 2000);
                    }
                }
            } else {
                // Afficher le prompt même si canInstall() retourne false
                console.log('[PWA] deferredPrompt disponible - Affichage du prompt maintenant');
                setTimeout(() => {
                    showInstallPrompt();
                }, 1000);
            }
            }
        }, 5000);
    }

    // Initialiser au chargement
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPWA);
    } else {
        initPWA();
    }

    // Exposer les fonctions globalement
    window.PWAManager = {
        install: installPWA,
        closePrompt: closeInstallPrompt
    };
})();
