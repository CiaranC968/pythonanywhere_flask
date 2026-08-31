document.addEventListener('DOMContentLoaded', () => {
    const listContainer = document.getElementById('applications-list');
    const viewButtons = document.querySelectorAll('[data-view-toggle]');
    
    if (!listContainer || !viewButtons.length) return;

    // Load saved preference
    const savedView = localStorage.getItem('tracker-layout-view') || 'card';
    applyView(savedView);

    viewButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.viewToggle;
            applyView(view);
            localStorage.setItem('tracker-layout-view', view);
        });
    });

    function applyView(view) {
        if (view === 'table') {
            listContainer.classList.add('table-view');
        } else {
            listContainer.classList.remove('table-view');
        }

        viewButtons.forEach(btn => {
            if (btn.dataset.viewToggle === view) {
                btn.setAttribute('aria-pressed', 'true');
            } else {
                btn.setAttribute('aria-pressed', 'false');
            }
        });
    }
});
