(() => {
    const searchInput = document.getElementById('job-search');
    const resultCount = document.getElementById('tracker-result-count');
    const emptyState = document.getElementById('tracker-empty');
    const companyRows = [...document.querySelectorAll('[data-company-search]')];
    const sectionTabs = [...document.querySelectorAll('[data-tracker-section]')];
    const sectionPanels = [...document.querySelectorAll('[data-tracker-panel]')];
    const advancedFilters = {
        company: document.getElementById('filter-company'),
        source: document.getElementById('filter-source'),
        location: document.getElementById('filter-location'),
        badge: document.getElementById('filter-badge'),
        dateFrom: document.getElementById('filter-date-from'),
        dateTo: document.getElementById('filter-date-to')
    };
    let activeFilter = 'all';
    let lastDialogOpener = null;

    function activateTrackerSection(tab, moveFocus = false) {
        if (!tab) return;
        const section = tab.dataset.trackerSection;

        sectionTabs.forEach((item) => {
            const isActive = item === tab;
            item.classList.toggle('active', isActive);
            item.setAttribute('aria-selected', String(isActive));
            item.tabIndex = isActive ? 0 : -1;
        });
        sectionPanels.forEach((panel) => {
            panel.hidden = panel.dataset.trackerPanel !== section;
        });
        if (moveFocus) tab.focus();
    }

    sectionTabs.forEach((tab, index) => {
        tab.addEventListener('click', () => activateTrackerSection(tab));
        tab.addEventListener('keydown', (event) => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
            event.preventDefault();
            let nextIndex = index;
            if (event.key === 'ArrowLeft') nextIndex = (index - 1 + sectionTabs.length) % sectionTabs.length;
            if (event.key === 'ArrowRight') nextIndex = (index + 1) % sectionTabs.length;
            if (event.key === 'Home') nextIndex = 0;
            if (event.key === 'End') nextIndex = sectionTabs.length - 1;
            activateTrackerSection(sectionTabs[nextIndex], true);
        });
    });

    function filterApplications() {
        const query = searchInput?.value.trim().toLowerCase() || '';
        let visible = 0;

        document.querySelectorAll('.application-card').forEach((card) => {
            const matchesSearch = !query || card.dataset.search.includes(query);
            const matchesStatus = activeFilter === 'all' || card.dataset.stage === activeFilter;
            const matchesCompany = !advancedFilters.company?.value || card.dataset.company === advancedFilters.company.value;
            const matchesSource = !advancedFilters.source?.value || card.dataset.source === advancedFilters.source.value;
            const matchesLocation = !advancedFilters.location?.value || card.dataset.location === advancedFilters.location.value;
            const matchesBadge = !advancedFilters.badge?.value || card.dataset.badges.split(',').map((badge) => badge.trim()).includes(advancedFilters.badge.value);
            const matchesStart = !advancedFilters.dateFrom?.value || Boolean(card.dataset.applied && card.dataset.applied >= advancedFilters.dateFrom.value);
            const matchesEnd = !advancedFilters.dateTo?.value || Boolean(card.dataset.applied && card.dataset.applied <= advancedFilters.dateTo.value);
            card.hidden = !(matchesSearch && matchesStatus && matchesCompany && matchesSource && matchesLocation && matchesBadge && matchesStart && matchesEnd);
            if (!card.hidden) visible += 1;
        });

        companyRows.forEach((row) => {
            const matchesSearch = !query || row.dataset.companySearch.includes(query);
            const matchesCompany = !advancedFilters.company?.value || row.dataset.company === advancedFilters.company.value;
            row.hidden = !(matchesSearch && matchesCompany);
        });

        if (resultCount) {
            resultCount.textContent = `${visible} ${visible === 1 ? 'application' : 'applications'}`;
        }
        emptyState?.classList.toggle('hidden', visible !== 0);
    }

    function formatDates(root = document) {
        root.querySelectorAll('.format-date').forEach((element) => {
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
    Object.values(advancedFilters).forEach((filter) => filter?.addEventListener('change', filterApplications));

    document.addEventListener('click', (event) => {
        const tab = event.target.closest('[data-filter]');
        if (tab) {
            activeFilter = tab.dataset.filter;
            document.querySelectorAll('[data-filter]').forEach((item) => {
                item.classList.toggle('active', item === tab);
                item.setAttribute('aria-selected', String(item === tab));
            });
            filterApplications();
            return;
        }

        const opener = event.target.closest('[data-dialog-open]');
        if (opener) {
            const dialog = document.getElementById(opener.dataset.dialogOpen);
            if (!dialog) return;
            lastDialogOpener = opener;
            dialog.showModal();
            requestAnimationFrame(() => {
                dialog.querySelector('[autofocus], input, select, textarea')?.focus();
            });
            return;
        }

        const closer = event.target.closest('[data-dialog-close]');
        if (closer) {
            closer.closest('dialog')?.close();
            return;
        }

        if (event.target.closest('[data-clear-filters]')) {
            searchInput && (searchInput.value = '');
            Object.values(advancedFilters).forEach((filter) => {
                if (filter) filter.value = '';
            });
            activeFilter = 'all';
            document.querySelectorAll('[data-filter]').forEach((item) => {
                const selected = item.dataset.filter === 'all';
                item.classList.toggle('active', selected);
                item.setAttribute('aria-selected', String(selected));
            });
            filterApplications();
        }
    });

    document.querySelectorAll('.tracker-dialog').forEach((dialog) => {
        dialog.addEventListener('click', (event) => {
            if (event.target === dialog) dialog.close();
        });
        dialog.addEventListener('close', () => lastDialogOpener?.focus());
    });

    document.body.addEventListener('htmx:afterSwap', (event) => {
        const card = event.detail.target.closest?.('.application-card') || event.detail.target;
        if (!card?.classList?.contains('application-card')) return;

        formatDates(card);
        filterApplications();
        const applicationId = card.id.replace('application-', '');
        const editDialog = document.getElementById(`edit-job-${applicationId}`);
        const stageInput = editDialog?.querySelector('[name="stage"]');
        if (stageInput) stageInput.value = card.dataset.stage;

        const feedback = card.querySelector('.quick-update-feedback');
        if (feedback) {
            window.setTimeout(() => feedback.remove(), 2500);
        }
    });

    async function moveKanbanCard(card, destination) {
        const previousColumn = card.closest('[data-kanban-stage]');
        const stage = destination.dataset.kanbanStage;
        if (!previousColumn || previousColumn === destination) return;

        destination.querySelector('[data-kanban-items]').appendChild(card);
        try {
            const response = await fetch(`/admin/job-tracker/${card.dataset.applicationId}/stage`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stage })
            });
            if (!response.ok) throw new Error('Could not update application status.');
            card.querySelector('[data-kanban-select]').value = stage;
            updateKanbanCounts();
            showKanbanFeedback(`${card.dataset.role} moved to ${stage}.`, false);
        } catch (_error) {
            previousColumn.querySelector('[data-kanban-items]').appendChild(card);
            card.querySelector('[data-kanban-select]').value = previousColumn.dataset.kanbanStage;
            updateKanbanCounts();
            showKanbanFeedback(`Could not move ${card.dataset.role}. Please try again.`, true);
        }
    }

    function showKanbanFeedback(message, isError) {
        const feedback = document.getElementById('kanban-announcer');
        if (!feedback) return;
        feedback.textContent = message;
        feedback.classList.toggle('is-error', isError);
        feedback.hidden = false;
    }

    function updateKanbanCounts() {
        document.querySelectorAll('[data-kanban-stage]').forEach((column) => {
            const count = column.querySelectorAll('.kanban-card').length;
            const output = column.querySelector('[data-kanban-count]');
            if (output) output.textContent = count;
        });
    }

    const kanbanBoard = document.querySelector('[data-kanban-board]');
    const kanbanScrollButtons = document.querySelectorAll('[data-kanban-scroll]');

    function updateKanbanScrollControls() {
        if (!kanbanBoard) return;
        const maximumScroll = kanbanBoard.scrollWidth - kanbanBoard.clientWidth;
        kanbanScrollButtons.forEach((button) => {
            const atStart = kanbanBoard.scrollLeft <= 1;
            const atEnd = kanbanBoard.scrollLeft >= maximumScroll - 1;
            button.disabled = button.dataset.kanbanScroll === 'previous' ? atStart : atEnd;
        });
    }

    if (kanbanBoard) {
        kanbanScrollButtons.forEach((button) => {
            button.addEventListener('click', () => {
                const direction = button.dataset.kanbanScroll === 'previous' ? -1 : 1;
                kanbanBoard.scrollBy({
                    left: direction * Math.max(240, kanbanBoard.clientWidth * 0.75),
                    behavior: 'smooth'
                });
            });
        });

        kanbanBoard.addEventListener('scroll', updateKanbanScrollControls, { passive: true });
        kanbanBoard.addEventListener('keydown', (event) => {
            if (event.target !== kanbanBoard || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
            event.preventDefault();
            const direction = event.key === 'ArrowLeft' ? -1 : 1;
            kanbanBoard.scrollBy({ left: direction * 280, behavior: 'smooth' });
        });
        kanbanBoard.addEventListener('dragover', (event) => {
            const bounds = kanbanBoard.getBoundingClientRect();
            const edgeSize = 64;
            if (event.clientX < bounds.left + edgeSize) kanbanBoard.scrollLeft -= 16;
            if (event.clientX > bounds.right - edgeSize) kanbanBoard.scrollLeft += 16;
        });
        window.addEventListener('resize', updateKanbanScrollControls);
        updateKanbanScrollControls();
    }

    document.querySelectorAll('.kanban-card').forEach((card) => {
        card.addEventListener('dragstart', (event) => {
            card.classList.add('is-dragging');
            event.dataTransfer.setData('text/plain', card.dataset.applicationId);
            event.dataTransfer.effectAllowed = 'move';
        });
        card.addEventListener('dragend', () => card.classList.remove('is-dragging'));
        card.querySelector('[data-kanban-select]')?.addEventListener('change', (event) => {
            const destination = document.querySelector(`[data-kanban-stage="${CSS.escape(event.target.value)}"]`);
            if (destination) moveKanbanCard(card, destination);
        });
    });

    document.querySelectorAll('[data-kanban-stage]').forEach((column) => {
        column.addEventListener('dragover', (event) => {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'move';
            column.classList.add('is-drag-over');
        });
        column.addEventListener('dragleave', () => column.classList.remove('is-drag-over'));
        column.addEventListener('drop', (event) => {
            event.preventDefault();
            column.classList.remove('is-drag-over');
            const applicationId = event.dataTransfer.getData('text/plain');
            const card = document.querySelector(`.kanban-card[data-application-id="${CSS.escape(applicationId)}"]`);
            if (card) moveKanbanCard(card, column);
        });
    });

    formatDates();
})();
