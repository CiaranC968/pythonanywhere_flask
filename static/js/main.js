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
        scrollProgress: '#scroll-progress',
        navLinks: '.nav-link',
        sections: 'section[id]',
        revealItems: 'section[id] > div, .card-item'
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
            if (!first || !last) {
                e.preventDefault();
                return;
            }

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
    },

    async copyText(value) {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(value);
            return;
        }

        const field = document.createElement('textarea');
        field.value = value;
        field.setAttribute('readonly', '');
        field.style.position = 'fixed';
        field.style.opacity = '0';
        document.body.appendChild(field);
        field.select();
        document.execCommand('copy');
        field.remove();
    }
};

// =========================================
// 2. GLOBAL EVENT DELEGATION
// =========================================
const GlobalEvents = {
    init() {
        document.addEventListener('click', (e) => {
            const target = e.target;

            if (target.closest('[data-reload-page]')) {
                window.location.reload();
                return;
            }

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

            const cardToggle = target.closest('[data-card-toggle]');
            if (cardToggle) {
                CardToggle.toggle(cardToggle);
                return;
            }

            // F. Copy Email Button
            const copyBtn = target.closest('.copy-btn');
            if (copyBtn) {
                const email = copyBtn.dataset.email;
                Utils.copyText(email).then(() => {
                    // Visual Feedback
                    const icon = copyBtn.querySelector('i');
                    const originalClass = icon.className;

                    icon.className = 'fas fa-check text-green-500';
                    Utils.announce('Email copied successfully');

                    setTimeout(() => {
                        icon.className = originalClass;
                    }, 2000);
                }).catch(() => {
                    Utils.announce('Could not copy email address');
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
        this.sync();
    },

    toggle() {
        // 1. Toggle the class on the HTML tag
        const isDark = document.documentElement.classList.toggle('dark');

        // 2. Update LocalStorage
        localStorage.setItem('theme', isDark ? 'dark' : 'light');

        // 3. Sync Desktop Checkbox
        this.sync();

        // 4. Update Meta Theme Color
        document.querySelector('meta[name="theme-color"]')?.setAttribute(
            'content', isDark ? '#111827' : '#facc15'
        );

        Utils.announce(isDark ? 'Dark mode enabled' : 'Light mode enabled');
    },

    sync() {
        const isDark = document.documentElement.classList.contains('dark');
        Utils.$$('#theme-toggle-fixed').forEach(toggle => toggle.checked = isDark);
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
        sidebar.classList.add('is-transitioning');

        // Update aria-expanded
        menuToggle?.setAttribute('aria-expanded', 'true');

        requestAnimationFrame(() => overlay?.classList.add('visible'));
        setTimeout(() => sidebar.classList.remove('is-transitioning'), CONFIG.animation.normal);

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

        setTimeout(() => {
            overlay?.classList.add('hidden');
            sidebar?.classList.remove('is-transitioning');
        }, CONFIG.animation.normal);

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
        Utils.$(CONFIG.selectors.modalPanel)?.classList.add('is-transitioning');

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
            panel.classList.remove('is-transitioning');
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
// 8. SCROLL PROGRESS
// =========================================
const ScrollProgress = {
    init() {
        const bar = Utils.$(CONFIG.selectors.scrollProgress);
        if (!bar) return;

        const update = Utils.throttle(() => {
            const max = document.documentElement.scrollHeight - window.innerHeight;
            const progress = max > 0 ? Math.min(window.scrollY / max, 1) : 0;
            bar.style.transform = `scaleX(${progress})`;
        });

        update();
        window.addEventListener('scroll', update, { passive: true });
        window.addEventListener('resize', update);
    }
};

// =========================================
// 9. REVEAL ANIMATIONS
// =========================================
const RevealManager = {
    observer: null,

    init() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add('reveal-visible');
                this.observer.unobserve(entry.target);
            });
        }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });

        this.observe();
        document.body.addEventListener('htmx:afterSwap', (event) => this.observe(event.detail.target));
    },

    observe(root = document) {
        if (!this.observer) return;
        const items = [
            ...(root.matches?.(CONFIG.selectors.revealItems) ? [root] : []),
            ...root.querySelectorAll(CONFIG.selectors.revealItems)
        ];
        items.forEach(item => {
            if (item.classList.contains('reveal-ready')) return;
            item.classList.add('reveal-ready');
            this.observer.observe(item);
        });
    }
};

// =========================================
// 10. PROJECT CAROUSEL
// =========================================
const ProjectCarousel = {
    init() {
        this.mount(document);
        document.body.addEventListener('htmx:afterSwap', (event) => this.mount(event.detail.target));
    },

    mount(root) {
        const track = root.matches?.('#projects-track') ? root : root.querySelector?.('#projects-track');
        if (!track || track.dataset.carouselReady) return;
        track.dataset.carouselReady = 'true';

        const cards = [...track.querySelectorAll('.card-item')];
        const carousel = track.closest('.projects-carousel');
        const previous = carousel?.querySelector('[data-carousel-direction="-1"]');
        const next = carousel?.querySelector('[data-carousel-direction="1"]');
        const dots = carousel?.nextElementSibling;
        let index = 0;
        let resizeTimer;

        const visibleCards = () => window.innerWidth >= 1024 ? 3 : window.innerWidth >= 768 ? 2 : 1;
        const positionCount = () => Math.max(cards.length - visibleCards() + 1, 1);

        const render = () => {
            const positions = positionCount();
            index = Math.min(index, positions - 1);
            const cardWidth = cards[0]?.offsetWidth || 0;
            track.style.transform = `translateX(-${index * (cardWidth + 32)}px)`;

            [previous, next].forEach((button) => {
                if (button) button.hidden = positions <= 1;
            });
            if (!dots) return;

            dots.hidden = positions <= 1;
            dots.replaceChildren();
            for (let position = 0; position < positions; position += 1) {
                const dot = document.createElement('button');
                dot.type = 'button';
                dot.className = position === index
                    ? 'w-6 h-2.5 rounded-full bg-brand-accent transition-all'
                    : 'w-2.5 h-2.5 rounded-full bg-gray-300 dark:bg-gray-600 transition-all';
                dot.setAttribute('aria-label', `Go to project group ${position + 1}`);
                dot.addEventListener('click', () => {
                    index = position;
                    render();
                });
                dots.appendChild(dot);
            }
        };

        carousel?.addEventListener('click', (event) => {
            const button = event.target.closest('[data-carousel-direction]');
            if (!button) return;
            const positions = positionCount();
            index = (index + Number(button.dataset.carouselDirection) + positions) % positions;
            render();
        });

        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(render, 100);
        });
        requestAnimationFrame(render);
    }
};

// =========================================
// 11. CARD SHOW MORE TOGGLE
// =========================================
const CardToggle = {
    toggle(button) {
        const container = button.closest('.grid');
        if (!container) return;

        const expanded = button.getAttribute('aria-expanded') === 'true';
        container.querySelectorAll('.card-overflow').forEach((card) => {
            card.classList.toggle('hidden', expanded);
        });

        button.setAttribute('aria-expanded', expanded ? 'false' : 'true');
        const label = expanded ? button.dataset.showLabel : button.dataset.hideLabel;
        button.querySelector('[data-card-toggle-text]').textContent = label;
        button.querySelector('[data-card-toggle-icon]')?.classList.toggle('rotate-180', !expanded);
        Utils.announce(label);
    }
};

// =========================================
// 12. HTMX ERROR HANDLING
// =========================================
const HtmxErrors = {
    init() {
        document.body.addEventListener('htmx:responseError', (e) => this.handle(e.detail));
        document.body.addEventListener('htmx:sendError', (e) => this.handle(e.detail, 'Network Error'));
        document.body.addEventListener('htmx:beforeRequest', (e) => e.detail.elt?.classList.add('is-loading'));
        document.body.addEventListener('htmx:afterRequest', (e) => e.detail.elt?.classList.remove('is-loading'));
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
// 13. INITIALIZATION
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
    ScrollProgress.init();
    RevealManager.init();
    ProjectCarousel.init();
    HtmxErrors.init();
});
