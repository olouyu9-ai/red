/**
 * Gestionnaire de thèmes pour Genius Africa
 * Supporte: dark, light, system
 */

(function() {
    'use strict';

    const THEME_STORAGE_KEY = 'genius-africa-theme';
    const THEMES = {
        DARK: 'dark',
        LIGHT: 'light',
        SYSTEM: 'system'
    };

    /**
     * Obtient le thème système (préférence OS)
     */
    function getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return THEMES.DARK;
        }
        return THEMES.LIGHT;
    }

    /**
     * Applique un thème au document
     */
    function applyTheme(theme) {
        const html = document.documentElement;
        
        if (theme === THEMES.SYSTEM) {
            const systemTheme = getSystemTheme();
            html.setAttribute('data-theme', systemTheme);
            html.setAttribute('data-theme-mode', THEMES.SYSTEM);
        } else {
            html.setAttribute('data-theme', theme);
            html.setAttribute('data-theme-mode', theme);
        }
    }

    /**
     * Obtient le thème actuel depuis le localStorage ou retourne 'dark' par défaut
     */
    function getCurrentTheme() {
        const stored = localStorage.getItem(THEME_STORAGE_KEY);
        if (stored && Object.values(THEMES).includes(stored)) {
            return stored;
        }
        return THEMES.DARK; // Par défaut: dark
    }

    /**
     * Sauvegarde le thème dans le localStorage
     */
    function saveTheme(theme) {
        localStorage.setItem(THEME_STORAGE_KEY, theme);
    }

    /**
     * Initialise le thème au chargement de la page
     */
    function initTheme() {
        const theme = getCurrentTheme();
        applyTheme(theme);
        updateThemeSelector(theme);
    }

    /**
     * Change le thème
     */
    function setTheme(theme) {
        if (!Object.values(THEMES).includes(theme)) {
            console.error('Thème invalide:', theme);
            return;
        }
        
        applyTheme(theme);
        saveTheme(theme);
        updateThemeSelector(theme);
    }

    /**
     * Met à jour l'interface du sélecteur de thème
     */
    function updateThemeSelector(theme) {
        const selectors = document.querySelectorAll('.theme-selector');
        selectors.forEach(selector => {
            const buttons = selector.querySelectorAll('.theme-option');
            buttons.forEach(btn => {
                const btnTheme = btn.getAttribute('data-theme');
                if (btnTheme === theme) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        });
    }

    /**
     * Écoute les changements de préférence système
     */
    function watchSystemTheme() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                const currentMode = document.documentElement.getAttribute('data-theme-mode');
                if (currentMode === THEMES.SYSTEM) {
                    applyTheme(THEMES.SYSTEM);
                }
            });
        }
    }

    // Initialisation au chargement
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initTheme();
            watchSystemTheme();
        });
    } else {
        initTheme();
        watchSystemTheme();
    }

    // Expose les fonctions globalement
    window.ThemeManager = {
        setTheme: setTheme,
        getCurrentTheme: getCurrentTheme,
        THEMES: THEMES
    };

    // Gestion des clics sur les boutons de thème
    document.addEventListener('click', (e) => {
        const themeBtn = e.target.closest('.theme-option');
        if (themeBtn) {
            e.preventDefault();
            const theme = themeBtn.getAttribute('data-theme');
            if (theme) {
                setTheme(theme);
            }
        }
    });
})();
