/**
 * CIARAN CAIRNS PORTFOLIO - MAIN JAVASCRIPT
 * ==========================================
 *
 * Table of Contents:
 * 1. Configuration & Constants
 * 2. Utility Functions
 * 3. Theme Manager
 * 4. Sidebar Manager
 * 5. Scroll Spy
 * 6. Modal Manager
 * 7. Scroll To Top
 * 8. HTMX Integration
 * 9. Accessibility Enhancements
 * 10. Performance Optimizations
 * 11. Initialization
 */

// =========================================
// 1. CONFIGURATION & CONSTANTS
// =========================================
const CONFIG = {
    breakpoints: {
        mobile: 768,
        tablet: 1024,
        desktop: 1280
    },
    scroll: {
        threshold: 500,
        bottomOffset: 20
    },
    animation: {
        fast: 150,
        normal: 300,
        slow: 500
    },
    selectors: {
        sidebar: '#sidebar',
        sidebarOverlay: '#sidebar-overlay',
        menuToggle: '#menu-toggle',
        themeToggleDesktop: '#theme-toggle-fixed',
        themeToggleMobile: '#mobile-theme-btn',
        modal: '#universalModal',
        modalPanel: '#modalPanel',
        modalBackdrop: '#modalBackdrop',
        modalContent: '#modalContent',
        modalClose: '#closeModalBtn',
        scrollTopBtn: '#scrollTopBtn',
        navLinks: '.nav-link',
        sections: 'section[id]'
    }
};

// =========================================
// 2. UTILITY FUNCTIONS
// =========================================
const Utils = {
    /**
     * Safely query a DOM element
     */
    $(selector) {
        return document.querySelector(selector);
    },

    /**
     * Safely query all matching DOM elements
     */
    $$(selector) {
        return document.querySelectorAll(selector);
    },

    /**
     * Debounce function calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function calls using requestAnimationFrame
     */
    throttleRAF(func) {
        let ticking = false;
        return function executedFunction(...args) {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    func(...args);
                    ticking = false;
                });
                ticking = true;
            }
        };
    },

    /**
     * Check if user prefers reduced motion
     */
    prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    },

    /**
     * Check if device is mobile
     */
    isMobile() {
        return window.innerWidth < CONFIG.breakpoints.mobile;
    },

    /**
     * Announce message to screen readers
     */
    announce(message, priority = 'polite') {
        const announcement = document.createElement('div');
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', priority);
        announcement.className = 'sr-only';
        announcement.textContent = message;
        document.body.appendChild(announcement);

        setTimeout(() => announcement.remove(), 1000);
    },

    /**
     * Get focusable elements within a container
     */
    getFocusableElements(container) {
        const focusableSelectors = [
            'a[href]',
            'button:not([disabled])',
            'textarea:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
        ].join(', ');

        return container.querySelectorAll(focusableSelectors);
    },

    /**
     * Trap focus within a container
     */
    trapFocus(container, onEscape) {
        const focusableElements = this.getFocusableElements(container);
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        const handleKeydown = (e) => {
            if (e.key === 'Escape' && onEscape) {
                onEscape();
                return;
            }

            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement?.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement?.focus();
                }
            }
        };

        container.addEventListener('keydown', handleKeydown);

        return () => container.removeEventListener('keydown', handleKeydown);
    }
};

// =========================================
// 3. THEME MANAGER
// =========================================
const ThemeManager = {
    html: document.documentElement,
    desktopToggle: null,
    mobileToggle: null,

    init() {
        this.desktopToggle = Utils.$(CONFIG.selectors.themeToggleDesktop);
        this.mobileToggle = Utils.$(CONFIG.selectors.themeToggleMobile);

        // Sync toggle state with current theme
        const isDark = this.html.classList.contains('dark');
        if (this.desktopToggle) {
            this.desktopToggle.checked = isDark;
        }

        this.attachListeners();
        this.watchSystemPreference();
    },

    toggle() {
        const isDark = this.html.classList.contains('dark');
        this.apply(!isDark);
    },

    apply(isDark) {
        // Add transition class for smooth theme switch
        document.body.classList.add('theme-transition');

        this.html.classList.toggle('dark', isDark);
        localStorage.setItem('theme', isDark ? 'dark' : 'light');

        if (this.desktopToggle) {
            this.desktopToggle.checked = isDark;
        }

        // Update meta theme-color
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', isDark ? '#111827' : '#facc15');
        }

        Utils.announce(isDark ? 'Dark mode enabled' : 'Light mode enabled');

        // Remove transition class after animation
        setTimeout(() => {
            document.body.classList.remove('theme-transition');
        }, CONFIG.animation.fast);
    },

    attachListeners() {
        this.desktopToggle?.addEventListener('change', (e) => {
            this.apply(e.target.checked);
        });

        this.mobileToggle?.addEventListener('click', () => {
            this.toggle();
        });
    },

    watchSystemPreference() {
        // Only watch if user hasn't set a preference
        if (localStorage.getItem('theme')) return;

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            this.apply(e.matches);
        });
    }
};

// =========================================
// 4. SIDEBAR MANAGER
// =========================================
const SidebarManager = {
    sidebar: null,
    overlay: null,
    menuToggle: null,
    navLinks: null,
    isOpen: false,
    lastFocusedElement: null,
    cleanupFocusTrap: null,

    init() {
        this.sidebar = Utils.$(CONFIG.selectors.sidebar);
        this.overlay = Utils.$(CONFIG.selectors.sidebarOverlay);
        this.menuToggle = Utils.$(CONFIG.selectors.menuToggle);
        this.navLinks = Utils.$$(CONFIG.selectors.navLinks);

        if (!this.sidebar) return;

        this.attachListeners();
    },

    open() {
        if (this.isOpen) return;

        this.isOpen = true;
        this.lastFocusedElement = document.activeElement;

        this.sidebar.classList.remove('-translate-x-full');
        this.overlay?.classList.remove('hidden');

        requestAnimationFrame(() => {
            this.overlay?.classList.add('visible');
        });

        document.body.style.overflow = 'hidden';
        this.sidebar.setAttribute('aria-hidden', 'false');
        this.menuToggle?.setAttribute('aria-expanded', 'true');

        // Focus first nav link after animation
        setTimeout(() => {
            const firstLink = this.sidebar.querySelector('.nav-link');
            firstLink?.focus();
        }, CONFIG.animation.normal);

        // Set up focus trap
        this.cleanupFocusTrap = Utils.trapFocus(this.sidebar, () => this.close());

        Utils.announce('Navigation menu opened');
    },

    close() {
        if (!this.isOpen) return;

        this.isOpen = false;

        this.sidebar.classList.add('-translate-x-full');
        this.overlay?.classList.remove('visible');

        setTimeout(() => {
            this.overlay?.classList.add('hidden');
        }, CONFIG.animation.normal);

        document.body.style.overflow = '';
        this.sidebar.setAttribute('aria-hidden', 'true');
        this.menuToggle?.setAttribute('aria-expanded', 'false');

        // Restore focus
        this.lastFocusedElement?.focus();

        // Clean up focus trap
        this.cleanupFocusTrap?.();

        Utils.announce('Navigation menu closed');
    },

    toggle() {
        this.isOpen ? this.close() : this.open();
    },

    attachListeners() {
        this.menuToggle?.addEventListener('click', () => this.toggle());
        this.overlay?.addEventListener('click', () => this.close());

        // Close on nav link click (mobile)
        this.navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (Utils.isMobile()) {
                    this.close();
                }
            });
        });

        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // Close on resize to desktop
        window.addEventListener('resize', Utils.debounce(() => {
            if (!Utils.isMobile() && this.isOpen) {
                this.close();
            }
        }, 150));
    }
};

// =========================================
// 5. SCROLL SPY
// =========================================
const ScrollSpy = {
    sections: null,
    navLinks: null,
    observer: null,
    currentActive: null,

    init() {
        this.sections = Utils.$$(CONFIG.selectors.sections);
        this.navLinks = Utils.$$(CONFIG.selectors.navLinks);

        if (!this.sections.length) return;

        this.setupIntersectionObserver();
        this.setupScrollListener();
    },

    setActive(link) {
        if (!link || link === this.currentActive) return;

        this.currentActive = link;

        this.navLinks.forEach(navLink => {
            const isActive = navLink === link;

            // Update classes
            navLink.classList.toggle('bg-gray-100', isActive);
            navLink.classList.toggle('dark:bg-gray-800', isActive);
            navLink.classList.toggle('text-brand-accent', isActive);

            // Update icon
            const icon = navLink.querySelector('i');
            icon?.classList.toggle('text-brand-accent', isActive);

            // Update ARIA
            navLink.setAttribute('aria-current', isActive ? 'page' : 'false');
        });
    },

    setupIntersectionObserver() {
        const options = {
            rootMargin: '-20% 0px -60% 0px',
            threshold: 0
        };

        this.observer = new IntersectionObserver((entries) => {
            // Don't update if at bottom of page
            if (this.isAtBottom()) return;

            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const activeLink = Utils.$(
                        `.nav-link[href="#${entry.target.id}"]`
                    );
                    this.setActive(activeLink);
                }
            });
        }, options);

        this.sections.forEach(section => this.observer.observe(section));
    },

    setupScrollListener() {
        const checkBottom = Utils.throttleRAF(() => {
            if (this.isAtBottom()) {
                const lastLink = this.navLinks[this.navLinks.length - 1];
                this.setActive(lastLink);
            }
        });

        window.addEventListener('scroll', checkBottom, { passive: true });
    },

    isAtBottom() {
        const scrollPosition = window.scrollY + window.innerHeight;
        const docHeight = document.documentElement.scrollHeight;
        return scrollPosition >= docHeight - CONFIG.scroll.bottomOffset;
    }
};

// =========================================
// 6. MODAL MANAGER
// =========================================
const ModalManager = {
    modal: null,
    panel: null,
    backdrop: null,
    content: null,
    closeBtn: null,
    isOpen: false,
    lastFocusedElement: null,
    cleanupFocusTrap: null,

    init() {
        this.modal = Utils.$(CONFIG.selectors.modal);
        this.panel = Utils.$(CONFIG.selectors.modalPanel);
        this.backdrop = Utils.$(CONFIG.selectors.modalBackdrop);
        this.content = Utils.$(CONFIG.selectors.modalContent);
        this.closeBtn = Utils.$(CONFIG.selectors.modalClose);

        if (!this.modal) return;

        this.attachListeners();
        this.setupHtmxListener();

        // Expose for inline calls
        window.openModal = () => this.open();
        window.closeModal = () => this.close();
    },

    open() {
        if (this.isOpen) return;

        this.isOpen = true;
        this.lastFocusedElement = document.activeElement;

        this.modal.classList.remove('hidden');
        this.modal.classList.add('flex');
        this.modal.setAttribute('aria-hidden', 'false');

        requestAnimationFrame(() => {
            this.backdrop?.classList.remove('opacity-0');
            this.panel?.classList.remove('scale-95', 'opacity-0');
            this.panel?.classList.add('scale-100', 'opacity-100');
        });

        document.body.style.overflow = 'hidden';

        // Focus close button after animation
        setTimeout(() => {
            this.closeBtn?.focus();
            this.cleanupFocusTrap = Utils.trapFocus(this.modal, () => this.close());
        }, CONFIG.animation.normal);

        Utils.announce('Modal opened');
    },

    close() {
        if (!this.isOpen) return;

        this.isOpen = false;

        this.backdrop?.classList.add('opacity-0');
        this.panel?.classList.add('scale-95', 'opacity-0');
        this.panel?.classList.remove('scale-100', 'opacity-100');

        setTimeout(() => {
            this.modal.classList.add('hidden');
            this.modal.classList.remove('flex');
            this.modal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';

            // Restore focus
            this.lastFocusedElement?.focus();
        }, CONFIG.animation.normal);

        this.cleanupFocusTrap?.();

        Utils.announce('Modal closed');
    },

    attachListeners() {
        this.closeBtn?.addEventListener('click', () => this.close());

        // Close on backdrop click
        this.modal?.addEventListener('click', (e) => {
            if (e.target === this.modal || e.target === this.backdrop) {
                this.close();
            }
        });

        // Close on escape (handled by focus trap, but fallback here)
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    },

    setupHtmxListener() {
        document.body.addEventListener('htmx:afterSwap', (evt) => {
            if (evt.detail.target.id === 'modalContent') {
                this.open();
            }
        });
    }
};

// =========================================
// 7. SCROLL TO TOP
// =========================================
const ScrollToTop = {
    btn: null,
    isVisible: false,

    init() {
        this.btn = Utils.$(CONFIG.selectors.scrollTopBtn);
        if (!this.btn) return;

        this.attachListeners();
    },

    show() {
        if (this.isVisible) return;
        this.isVisible = true;
        this.btn.classList.remove('translate-y-20', 'opacity-0');
    },

    hide() {
        if (!this.isVisible) return;
        this.isVisible = false;
        this.btn.classList.add('translate-y-20', 'opacity-0');
    },

    scroll() {
        const behavior = Utils.prefersReducedMotion() ? 'auto' : 'smooth';
        window.scrollTo({ top: 0, behavior });

        // Announce for screen readers
        Utils.announce('Scrolled to top of page');

        // Move focus to main content
        const mainContent = Utils.$('#main-content');
        mainContent?.focus();
    },

    attachListeners() {
        const handleScroll = Utils.throttleRAF(() => {
            if (window.scrollY > CONFIG.scroll.threshold) {
                this.show();
            } else {
                this.hide();
            }
        });

        window.addEventListener('scroll', handleScroll, { passive: true });
        this.btn.addEventListener('click', () => this.scroll());
    }
};

// =========================================
// 8. HTMX INTEGRATION
// =========================================
const HtmxIntegration = {
    init() {
        this.setupErrorHandling();
        this.setupLoadingStates();
    },

    setupErrorHandling() {
        document.body.addEventListener('htmx:responseError', (evt) => {
            console.error('HTMX request failed:', evt.detail);
            this.showError(evt.detail.target, evt.detail.xhr?.status);
        });

        document.body.addEventListener('htmx:sendError', (evt) => {
            console.error('HTMX network error:', evt.detail);
            this.showError(evt.detail.target, 'network');
        });

        document.body.addEventListener('htmx:timeout', (evt) => {
            console.error('HTMX timeout:', evt.detail);
            this.showError(evt.detail.target, 'timeout');
        });
    },

    setupLoadingStates() {
        // Update aria-busy on requests
        document.body.addEventListener('htmx:beforeRequest', (evt) => {
            evt.detail.target?.setAttribute('aria-busy', 'true');
        });

        document.body.addEventListener('htmx:afterRequest', (evt) => {
            evt.detail.target?.setAttribute('aria-busy', 'false');
        });
    },

    showError(target, errorType) {
        if (!target) return;

        const messages = {
            network: 'Network error. Please check your connection.',
            timeout: 'Request timed out. Please try again.',
            404: 'Content not found.',
            500: 'Server error. Please try again later.',
            default: 'Failed to load content. Please refresh the page.'
        };

        const message = messages[errorType] || messages.default;
        const sectionName = target.id?.replace('-container', '') || 'content';

        target.innerHTML = `
            <div class="load-error col-span-full" role="alert">
                <i class="fas fa-exclamation-triangle text-3xl mb-3" aria-hidden="true"></i>
                <p class="font-medium">Unable to load ${sectionName}</p>
                <p class="text-sm mt-1 opacity-75">${message}</p>
                <button
                    onclick="htmx.trigger(this.closest('[hx-get]'), 'load')"
                    class="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm font-medium">
                    <i class="fas fa-redo mr-2" aria-hidden="true"></i>Retry
                </button>
            </div>
        `;

        Utils.announce(`Failed to load ${sectionName}. ${message}`);
    },

    // Expose for inline error handlers
    handleLoadError(container, section) {
        this.showError(container, 'default');
    }
};

// Expose for inline use
window.handleLoadError = (container, section) => {
    HtmxIntegration.handleLoadError(container, section);
};

// =========================================
// 9. ACCESSIBILITY ENHANCEMENTS
// =========================================
const AccessibilityEnhancements = {
    init() {
        this.setupReducedMotion();
        this.setupHighContrast();
        this.setupKeyboardNavigation();
    },

    setupReducedMotion() {
        if (Utils.prefersReducedMotion()) {
            document.documentElement.style.scrollBehavior = 'auto';
        }

        // Watch for changes
        window.matchMedia('(prefers-reduced-motion: reduce)')
            .addEventListener('change', (e) => {
                document.documentElement.style.scrollBehavior =
                    e.matches ? 'auto' : 'smooth';
            });
    },

    setupHighContrast() {
        const mediaQuery = window.matchMedia('(prefers-contrast: high)');

        if (mediaQuery.matches) {
            document.documentElement.classList.add('high-contrast');
        }

        mediaQuery.addEventListener('change', (e) => {
            document.documentElement.classList.toggle('high-contrast', e.matches);
        });
    },

    setupKeyboardNavigation() {
        // Add keyboard hint class when user is using keyboard
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
    }
};

// =========================================
// 10. PERFORMANCE OPTIMIZATIONS
// =========================================
const PerformanceOptimizations = {
    init() {
        this.setupLazyLoading();
        this.setupConnectionAwareness();
    },

    setupLazyLoading() {
        // Native lazy loading is already enabled via HTML
        // This adds intersection observer fallback if needed
        if (!('loading' in HTMLImageElement.prototype)) {
            const images = Utils.$$('img[loading="lazy"]');

            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src || img.src;
                        imageObserver.unobserve(img);
                    }
                });
            });

            images.forEach(img => imageObserver.observe(img));
        }
    },

    setupConnectionAwareness() {
        // Reduce animations on slow connections
        if ('connection' in navigator) {
            const connection = navigator.connection;

            if (connection.saveData || connection.effectiveType === 'slow-2g') {
                document.documentElement.classList.add('reduce-data');
            }

            connection.addEventListener('change', () => {
                document.documentElement.classList.toggle(
                    'reduce-data',
                    connection.saveData || connection.effectiveType === 'slow-2g'
                );
            });
        }
    }
};

// =========================================
// 11. INITIALIZATION
// =========================================
const App = {
    init() {
        // Set footer year
        this.setYear();

        // Initialize all managers
        ThemeManager.init();
        SidebarManager.init();
        ScrollSpy.init();
        ModalManager.init();
        ScrollToTop.init();
        HtmxIntegration.init();
        AccessibilityEnhancements.init();
        PerformanceOptimizations.init();

        console.log('Portfolio initialized successfully');
    },

    setYear() {
        const year = new Date().getFullYear();
        Utils.$$('#year, #footer-year').forEach(el => {
            if (el) el.textContent = year;
        });
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => App.init());
} else {
    App.init();
}

// Export for testing or external use
window.PortfolioApp = {
    ThemeManager,
    SidebarManager,
    ModalManager,
    ScrollSpy,
    ScrollToTop,
    Utils
};