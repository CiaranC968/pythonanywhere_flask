(() => {
    const searchInput = document.getElementById('job-search');
    const resultCount = document.getElementById('tracker-result-count');
    const emptyState = document.getElementById('tracker-empty');
    const cards = [...document.querySelectorAll('.application-card')];
    let activeFilter = 'all';

    function filterApplications() {
        const query = searchInput?.value.trim().toLowerCase() || '';
        let visible = 0;

        cards.forEach((card) => {
            const matchesSearch = !query || card.dataset.search.includes(query);
            const matchesStatus = activeFilter === 'all' || card.dataset.stage === activeFilter;
            card.hidden = !(matchesSearch && matchesStatus);
            if (!card.hidden) visible += 1;
        });

        if (resultCount) {
            resultCount.textContent = `${visible} ${visible === 1 ? 'application' : 'applications'}`;
        }
        emptyState?.classList.toggle('hidden', visible !== 0);
    }

    function formatDates() {
        document.querySelectorAll('.format-date').forEach((element) => {
            const raw = element.textContent.trim();
            const date = new Date(raw.length === 10 ? `${raw}T00:00:00` : raw);
            if (Number.isNaN(date.getTime())) return;

            const includesTime = raw.includes('T') || raw.includes(' ');
            element.textContent = new Intl.DateTimeFormat('en-GB', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
                ...(includesTime ? { hour: '2-digit', minute: '2-digit' } : {})
            }).format(date);
        });
    }

    searchInput?.addEventListener('input', filterApplications);

    document.addEventListener('click', (event) => {
        const tab = event.target.closest('[data-filter]');
        if (tab) {
            activeFilter = tab.dataset.filter;
            document.querySelectorAll('[data-filter]').forEach((item) => {
                item.classList.toggle('active', item === tab);
            });
            filterApplications();
            return;
        }

        const opener = event.target.closest('[data-dialog-open]');
        if (opener) {
            document.getElementById(opener.dataset.dialogOpen)?.showModal();
            return;
        }

        const closer = event.target.closest('[data-dialog-close]');
        closer?.closest('dialog')?.close();
    });

    document.querySelectorAll('.tracker-dialog').forEach((dialog) => {
        dialog.addEventListener('click', (event) => {
            if (event.target === dialog) dialog.close();
        });
    });

    formatDates();
})();
