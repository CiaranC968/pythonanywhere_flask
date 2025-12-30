/**
 * CIARAN CAIRNS PORTFOLIO - MAIN JAVASCRIPT
 * Optimized for Tailwind v4 & HTMX
 */

const CONFIG = {
    breakpoints: { mobile: 768 },
    scroll: { threshold: 500 },
    animation: { normal: 300 },
    selectors: {
        sidebar: '#sidebar',
        sidebarOverlay: '#sidebar-overlay',
        modal: '#universalModal',
        modalPanel: '#modalPanel',
        modalBackdrop: '#modalBackdrop',
        modalContent: '#modalContent',
        scrollTopBtn: '#scrollTopBtn',
        navLinks: '.nav-link',
        sections: 'section[id]'
    }
};

// =========================================
// 1. UTILITY FUNCTIONS
// =========================================
const Utils = {
    $(selector) { return document.querySelector(selector); },
    $$(selector) { return document.querySelectorAll(selector); },

    // Throttle for scroll performance
    throttle(func) {
        let ticking = false;
        return (...args) => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    func(...args);
                    ticking = false;
                });
                ticking = true;
            }
        };
    },

    isMobile: () => window.innerWidth < CONFIG.breakpoints.mobile,

    // Screen Reader Announcements
    announce(message) {
        let polite = document.getElementById('a11y-polite');
        if (!polite) {
            polite = document.createElement('div');
            polite.id = 'a11y-polite';
            polite.className = 'sr-only';
            polite.setAttribute('aria-live', 'polite');
            document.body.appendChild(polite);
        }
        polite.textContent = message;
    },

    // Focus Trap for Modals/Sidebar
    trapFocus(container, onEscape) {
        const focusables = container.querySelectorAll('a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])');
        const first = focusables[0];
        const last = focusables[focusables.length - 1];

        const handleKey = (e) => {
            if (e.key === 'Escape' && onEscape) return onEscape();
            if (e.key !== 'Tab') return;

            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last?.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first?.focus();
            }
        };

        container.addEventListener('keydown', handleKey);
        return () => container.removeEventListener('keydown', handleKey);
    }
};

// =========================================
// 2. GLOBAL EVENT DELEGATION
// =========================================
const GlobalEvents = {
    init() {
        document.addEventListener('click', (e) => {
            const target = e.target;

            // A. Theme Toggle
            if (target.closest('#mobile-theme-btn') || target.closest('#theme-toggle-fixed')) {
                ThemeManager.toggle();
                return;
            }

            // B. Menu Toggle
            if (target.closest('#menu-toggle')) {
                SidebarManager.toggle();
                return;
            }

            // C. Sidebar Overlay or Close Links
            if (target.closest(CONFIG.selectors.sidebarOverlay) ||
                (target.closest('.nav-link') && Utils.isMobile())) {
                SidebarManager.close();
                return;
            }

            // D. Modal Close (close button OR clicking backdrop)
            if (target.closest('#closeModalBtn') || target.closest('#modalBackdrop')) {
                ModalManager.close();
                return;
            }

            // E. Scroll Top
            if (target.closest(CONFIG.selectors.scrollTopBtn)) {
                ScrollToTop.scroll();
                return;
            }

            // F. Copy Email Button
            const copyBtn = target.closest('.copy-btn');
            if (copyBtn) {
                const email = copyBtn.dataset.email;
                navigator.clipboard.writeText(email).then(() => {
                    // Visual Feedback
                    const icon = copyBtn.querySelector('i');
                    const originalClass = icon.className;

                    icon.className = 'fas fa-check text-green-500';
                    Utils.announce('Email copied successfully');

                    setTimeout(() => {
                        icon.className = originalClass;
                    }, 2000);
                });
            }
        });

        // Global Escape Key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (SidebarManager.isOpen) SidebarManager.close();
                if (ModalManager.isOpen) ModalManager.close();
            }
        });
    }
};

// =========================================
// 3. THEME MANAGER
// =========================================
const ThemeManager = {
    init() {
        // Sync checkbox state on load
        const toggle = Utils.$('#theme-toggle-fixed');
        if (toggle) toggle.checked = document.documentElement.classList.contains('dark');
    },

    toggle() {
        // 1. Toggle the class on the HTML tag
        const isDark = document.documentElement.classList.toggle('dark');

        // 2. Update LocalStorage
        localStorage.setItem('theme', isDark ? 'dark' : 'light');

        // 3. Sync Desktop Checkbox
        const desktopToggle = Utils.$('#theme-toggle-fixed');
        if (desktopToggle) desktopToggle.checked = isDark;

        // 4. Update Meta Theme Color
        document.querySelector('meta[name="theme-color"]')?.setAttribute(
            'content', isDark ? '#111827' : '#facc15'
        );

        Utils.announce(isDark ? 'Dark mode enabled' : 'Light mode enabled');
    }
};

// =========================================
// 4. SIDEBAR MANAGER
// =========================================
const SidebarManager = {
    isOpen: false,
    trapCleanup: null,

    toggle() { this.isOpen ? this.close() : this.open(); },

    open() {
        const sidebar = Utils.$(CONFIG.selectors.sidebar);
        const overlay = Utils.$(CONFIG.selectors.sidebarOverlay);
        const menuToggle = Utils.$('#menu-toggle');
        if (!sidebar) return;

        this.isOpen = true;
        sidebar.classList.remove('-translate-x-full');
        overlay?.classList.remove('hidden');

        // Update aria-expanded
        menuToggle?.setAttribute('aria-expanded', 'true');

        requestAnimationFrame(() => overlay?.classList.add('visible'));

        document.body.style.overflow = 'hidden';
        this.trapCleanup = Utils.trapFocus(sidebar, () => this.close());
        Utils.announce('Menu opened');
    },

    close() {
        if (!this.isOpen) return;
        const sidebar = Utils.$(CONFIG.selectors.sidebar);
        const overlay = Utils.$(CONFIG.selectors.sidebarOverlay);
        const menuToggle = Utils.$('#menu-toggle');

        this.isOpen = false;
        sidebar.classList.add('-translate-x-full');
        overlay?.classList.remove('visible');

        // Update aria-expanded
        menuToggle?.setAttribute('aria-expanded', 'false');

        setTimeout(() => overlay?.classList.add('hidden'), CONFIG.animation.normal);

        document.body.style.overflow = '';
        if (this.trapCleanup) this.trapCleanup();
        Utils.announce('Menu closed');
    }
};

// =========================================
// 5. SCROLL SPY
// =========================================
const ScrollSpy = {
    init() {
        const sections = Utils.$$(CONFIG.selectors.sections);
        const navLinks = Utils.$$(CONFIG.selectors.navLinks);
        if (!sections.length) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.updateActive(navLinks, entry.target.id);
                }
            });
        }, { rootMargin: '-20% 0px -55% 0px' });

        sections.forEach(s => observer.observe(s));
    },

    updateActive(links, id) {
        links.forEach(link => {
            const isActive = link.getAttribute('href') === `#${id}`;

            // Tailwind classes for active state
            link.classList.toggle('text-brand-accent', isActive);
            link.classList.toggle('bg-gray-100', isActive);
            link.classList.toggle('dark:bg-gray-800', isActive);

            // Toggle Icon Color
            link.querySelector('i')?.classList.toggle('text-brand-accent', isActive);
            link.setAttribute('aria-current', isActive ? 'page' : 'false');
        });
    }
};

// =========================================
// 6. MODAL MANAGER (HTMX Aware)
// =========================================
const ModalManager = {
    isOpen: false,
    trapCleanup: null,
    previouslyFocused: null,

    init() {
        // Auto-open modal when HTMX populates it
        document.body.addEventListener('htmx:afterSwap', (evt) => {
            if (evt.detail.target.id === 'modalContent') this.open();
        });
    },

    open() {
        const modal = Utils.$(CONFIG.selectors.modal);
        if (!modal) return;

        // Store currently focused element to restore later
        this.previouslyFocused = document.activeElement;

        this.isOpen = true;
        modal.classList.remove('hidden', 'opacity-0');
        modal.classList.add('flex');
        modal.removeAttribute('aria-hidden');

        // Animation
        requestAnimationFrame(() => {
            Utils.$(CONFIG.selectors.modalBackdrop).classList.remove('opacity-0');
            const panel = Utils.$(CONFIG.selectors.modalPanel);
            panel.classList.remove('scale-95', 'opacity-0');
            panel.classList.add('scale-100', 'opacity-100');
        });

        document.body.style.overflow = 'hidden';
        this.trapCleanup = Utils.trapFocus(modal, () => this.close());

        // Focus the close button
        Utils.$('#closeModalBtn')?.focus();
    },

    close() {
        const modal = Utils.$(CONFIG.selectors.modal);
        if (!this.isOpen || !modal) return;

        this.isOpen = false;
        Utils.$(CONFIG.selectors.modalBackdrop).classList.add('opacity-0');

        const panel = Utils.$(CONFIG.selectors.modalPanel);
        panel.classList.add('scale-95', 'opacity-0');
        panel.classList.remove('scale-100', 'opacity-100');

        setTimeout(() => {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            modal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        }, CONFIG.animation.normal);

        if (this.trapCleanup) this.trapCleanup();

        // Restore focus to previously focused element
        this.previouslyFocused?.focus();
    }
};

// =========================================
// 7. SCROLL TO TOP
// =========================================
const ScrollToTop = {
    init() {
        const btn = Utils.$(CONFIG.selectors.scrollTopBtn);
        if (!btn) return;

        window.addEventListener('scroll', Utils.throttle(() => {
            const show = window.scrollY > CONFIG.scroll.threshold;
            btn.classList.toggle('translate-y-20', !show);
            btn.classList.toggle('opacity-0', !show);
        }));
    },

    scroll() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        Utils.$('#main-content')?.focus();
    }
};

// =========================================
// 8. HTMX ERROR HANDLING
// =========================================
const HtmxErrors = {
    init() {
        document.body.addEventListener('htmx:responseError', (e) => this.handle(e.detail));
        document.body.addEventListener('htmx:sendError', (e) => this.handle(e.detail, 'Network Error'));
    },

    handle(detail, customMsg) {
        const target = detail.target;
        if (!target) return;

        const msg = customMsg || `Error ${detail.xhr?.status || 'Unknown'}`;

        target.innerHTML = `
            <div class="col-span-full py-8 text-center text-red-500">
                <i class="fas fa-exclamation-circle text-2xl mb-2" aria-hidden="true"></i>
                <p class="font-medium">${msg}</p>
                <button class="retry-btn mt-4 underline hover:text-red-700">Try Again</button>
            </div>
        `;

        // Attach listener to new button
        target.querySelector('.retry-btn')?.addEventListener('click', () => {
            htmx.trigger(target, 'load');
        });
    }
};

// =========================================
// 9. INITIALIZATION
// =========================================
document.addEventListener('DOMContentLoaded', () => {
    // 1. Set Footer Year
    const year = new Date().getFullYear();
    Utils.$$('.current-year').forEach(el => el.textContent = year);

    // 2. Initialize Modules
    GlobalEvents.init();
    ThemeManager.init();
    ScrollSpy.init();
    ModalManager.init();
    ScrollToTop.init();
    HtmxErrors.init();

    console.log('Portfolio Ready');
});