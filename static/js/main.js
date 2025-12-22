/* ==========================================================================
   1. THEME ENGINE
   ========================================================================== */
const initTheme = () => {
    const html = document.documentElement;
    const desktopToggle = document.getElementById('theme-toggle-fixed');
    const mobileToggle = document.getElementById('theme-toggle-mobile');

    const setTheme = (isDark) => {
        html.classList.toggle('dark', isDark);
        localStorage.theme = isDark ? 'dark' : 'light';
        if (desktopToggle) desktopToggle.checked = isDark;
        if (mobileToggle) mobileToggle.checked = isDark;
    };

    const savedTheme = localStorage.theme;
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const shouldBeDark = savedTheme === 'dark' || (!savedTheme && systemDark);
    setTheme(shouldBeDark);

    desktopToggle?.addEventListener('change', (e) => setTheme(e.target.checked));
    mobileToggle?.addEventListener('change', (e) => setTheme(e.target.checked));
};

/* ==========================================================================
   2. UNIFIED MODAL ENGINE
   ========================================================================== */
const modal = {
    el: document.getElementById('universalModal'),
    content: document.querySelector('#universalModal .modal-content'),

    open() {
        this.el.classList.remove('hidden');
        this.el.classList.add('flex');
        document.body.style.overflow = 'hidden';
        setTimeout(() => {
            this.content?.classList.remove('scale-95', 'opacity-0');
            this.content?.classList.add('scale-100', 'opacity-100');
        }, 10);
    },

    close() {
        this.content?.classList.add('scale-95', 'opacity-0');
        setTimeout(() => {
            this.el.classList.add('hidden');
            this.el.classList.remove('flex');
            document.body.style.overflow = '';
        }, 300);
    }
};

/* ==========================================================================
   3. DOM READY & LISTENERS
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {
    initTheme();

    // A. HTMX Listener
    document.body.addEventListener('htmx:afterSwap', (evt) => {
        if (evt.detail.target.id === "modalContent") {
            modal.open();
        }
    });

    // B. Sidebar Logic
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    const toggleSidebar = () => {
        sidebar?.classList.toggle('open');
        overlay?.classList.toggle('hidden');
    };

    menuToggle?.addEventListener('click', toggleSidebar);
    overlay?.addEventListener('click', toggleSidebar);

    // C. Global Close Listeners
    window.addEventListener('click', (e) => { if (e.target === modal.el) modal.close(); });
    document.getElementById('closeModal')?.addEventListener('click', () => modal.close());

    // D. Scroll-To-Top
    const scrollBtn = document.getElementById('scrollTopBtn');
    window.addEventListener('scroll', () => {
        scrollBtn?.classList.toggle('hidden', window.scrollY < 500);
    });
    scrollBtn?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
});