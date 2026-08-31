(() => {
    const searchInput = document.getElementById('job-search');
    const resultCount = document.getElementById('tracker-result-count');
    const emptyState = document.getElementById('tracker-empty');
    const companyEmptyState = document.getElementById('company-search-empty');
    const companyRows = [...document.querySelectorAll('[data-company-search]')];
    const answerEntries = [...document.querySelectorAll('[data-answer-search]')];
    const sectionTabs = [...document.querySelectorAll('[data-tracker-section]')];
    const sectionPanels = [...document.querySelectorAll('[data-tracker-panel]')];
    const parseEmbeddedJson = (id) => {
        const element = document.getElementById(id);
        if (!element) return {};
        try {
            return JSON.parse(element.textContent);
        } catch (_error) {
            return {};
        }
    };
    const answerBank = parseEmbeddedJson('interview-answer-bank-data');
    const companyApplicationHistory = parseEmbeddedJson('company-application-history');
    const advancedFilters = {
        company: document.getElementById('filter-company'),
        source: document.getElementById('filter-source'),
        location: document.getElementById('filter-location'),
        arrangement: document.getElementById('filter-arrangement'),
        badge: document.getElementById('filter-badge'),
        dateFrom: document.getElementById('filter-date-from'),
        dateTo: document.getElementById('filter-date-to')
    };
    let activeFilters = ['all'];
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
        filterApplications();
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
        const queryTerms = (searchInput?.value.trim().toLowerCase() || '').split(/\s+/).filter(Boolean);
        const matchesQuery = (searchText = '') => queryTerms.every((term) => searchText.includes(term));
        let visibleApplications = 0;
        let visibleCompanies = 0;
        let visibleAnswers = 0;

        document.querySelectorAll('.application-card').forEach((card) => {
            const matchesSearch = matchesQuery(card.dataset.search);
            const matchesStatus = activeFilters.includes('all') || activeFilters.includes(card.dataset.stage);
            const matchesCompany = !advancedFilters.company?.value || card.dataset.company === advancedFilters.company.value;
            const matchesSource = !advancedFilters.source?.value || card.dataset.source === advancedFilters.source.value;
            const matchesLocation = !advancedFilters.location?.value || card.dataset.location === advancedFilters.location.value;
            const matchesArrangement = !advancedFilters.arrangement?.value || card.dataset.arrangement === advancedFilters.arrangement.value;
            const matchesBadge = !advancedFilters.badge?.value || card.dataset.badges.split(',').map((badge) => badge.trim()).includes(advancedFilters.badge.value);
            const matchesStart = !advancedFilters.dateFrom?.value || Boolean(card.dataset.applied && card.dataset.applied >= advancedFilters.dateFrom.value);
            const matchesEnd = !advancedFilters.dateTo?.value || Boolean(card.dataset.applied && card.dataset.applied <= advancedFilters.dateTo.value);
            card.hidden = !(matchesSearch && matchesStatus && matchesCompany && matchesSource && matchesLocation && matchesArrangement && matchesBadge && matchesStart && matchesEnd);
            if (!card.hidden) visibleApplications += 1;
        });

        companyRows.forEach((row) => {
            const matchesSearch = matchesQuery(row.dataset.globalSearch || row.dataset.companySearch);
            const matchesCompany = !advancedFilters.company?.value || row.dataset.company === advancedFilters.company.value;
            row.hidden = !(matchesSearch && matchesCompany);
            if (!row.hidden) visibleCompanies += 1;
        });

        answerEntries.forEach((entry) => {
            entry.hidden = !matchesQuery(entry.dataset.answerSearch);
            if (!entry.hidden) visibleAnswers += 1;
        });

        if (resultCount) {
            const activeSection = document.querySelector('[data-tracker-section][aria-selected="true"]')?.dataset.trackerSection;
            if (activeSection === 'companies') {
                resultCount.textContent = `${visibleCompanies} ${visibleCompanies === 1 ? 'company' : 'companies'}`;
            } else if (activeSection === 'answer-bank') {
                resultCount.textContent = `${visibleAnswers} saved ${visibleAnswers === 1 ? 'answer' : 'answers'}`;
            } else {
                resultCount.textContent = `${visibleApplications} ${visibleApplications === 1 ? 'application' : 'applications'}`;
            }
        }
        emptyState?.classList.toggle('hidden', visibleApplications !== 0);
        companyEmptyState?.classList.toggle('hidden', visibleCompanies !== 0);
    }

    function formatDates(root = document) {
        root.querySelectorAll('.format-date').forEach((element) => {
            const raw = element.getAttribute('datetime') || element.textContent.trim();
            const date = new Date(raw.length === 10 ? `${raw}T00:00:00` : raw);
            if (Number.isNaN(date.getTime())) return;

            const includesTime = raw.includes('T') || raw.includes(' ');
            const compact = element.classList.contains('format-date--compact');
            element.textContent = new Intl.DateTimeFormat('en-GB', {
                day: '2-digit',
                month: 'short',
                ...(!compact ? { year: 'numeric' } : {}),
                ...(includesTime ? { hour: '2-digit', minute: '2-digit' } : {})
            }).format(date);
        });
    }

    searchInput?.addEventListener('input', filterApplications);
    const requestedSection = new URLSearchParams(window.location.search).get('section');
    if (requestedSection) {
        activateTrackerSection(sectionTabs.find((tab) => tab.dataset.trackerSection === requestedSection));
    }
    document.addEventListener('keydown', (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k' && searchInput) {
            event.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
    });
    Object.values(advancedFilters).forEach((filter) => filter?.addEventListener('change', filterApplications));

    function appendPreparationText(field, value) {
        if (!field || !value) return;
        field.value = field.value.trim() ? `${field.value.trim()}\n\n${value}` : value;
        field.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function updateCoolingWarning(form) {
        const output = form.querySelector('[data-cooling-warning]');
        const companyInput = form.querySelector('[name="company"]');
        const appliedInput = form.querySelector('[name="applied_date"]');
        if (!output || !companyInput || !appliedInput?.value) return;

        const companyKey = companyInput.value.trim().toLowerCase().replace(/\s+/g, ' ');
        const currentId = Number(form.dataset.applicationId || 0);
        const currentDate = new Date(`${appliedInput.value}T00:00:00`);
        const previousDates = (companyApplicationHistory[companyKey] || [])
            .filter((item) => item.id !== currentId && item.date <= appliedInput.value)
            .sort((left, right) => right.date.localeCompare(left.date));
        const previous = previousDates[0];
        if (!previous || Number.isNaN(currentDate.getTime())) {
            output.hidden = true;
            output.textContent = '';
            return;
        }

        const previousDate = new Date(`${previous.date}T00:00:00`);
        const days = Math.round((currentDate - previousDate) / 86400000);
        if (days < 0 || days >= 30) {
            output.hidden = true;
            output.textContent = '';
            return;
        }
        output.innerHTML = `<i class="fas fa-triangle-exclamation" aria-hidden="true"></i> Last application to this company was ${days === 0 ? 'on the same day' : `${days} days earlier`}.`;
        output.hidden = false;
    }

    document.querySelectorAll('[data-application-form]').forEach((form) => {
        const companyInput = form.querySelector('[name="company"]');
        const appliedInput = form.querySelector('[name="applied_date"]');
        companyInput?.addEventListener('input', () => updateCoolingWarning(form));
        appliedInput?.addEventListener('change', () => updateCoolingWarning(form));
        updateCoolingWarning(form);
    });

    document.addEventListener('click', (event) => {
        const insertAnswerButton = event.target.closest('[data-insert-answer]');
        if (insertAnswerButton) {
            const picker = insertAnswerButton.closest('.answer-bank-picker');
            const selectedId = picker?.querySelector('[data-answer-bank-select]')?.value;
            const savedAnswer = answerBank[selectedId];
            const form = insertAnswerButton.closest('form');
            const feedback = picker?.querySelector('[data-answer-insert-feedback]');
            if (!savedAnswer || !form) {
                if (feedback) feedback.textContent = 'Choose a saved answer first.';
                return;
            }
            
            let formattedAnswer = '';
            if (savedAnswer.situation) formattedAnswer += `Situation: ${savedAnswer.situation}\n`;
            if (savedAnswer.task) formattedAnswer += `Task: ${savedAnswer.task}\n`;
            if (savedAnswer.action || savedAnswer.answer) formattedAnswer += `Action: ${savedAnswer.action || savedAnswer.answer}\n`;
            if (savedAnswer.result) formattedAnswer += `Result: ${savedAnswer.result}\n`;
            formattedAnswer = formattedAnswer.trim();

            appendPreparationText(form.querySelector('[name="interview_questions"]'), savedAnswer.question);
            appendPreparationText(form.querySelector('[name="interview_answers"]'), formattedAnswer);
            if (feedback) feedback.textContent = 'Added to interview preparation.';
            return;
        }

        const copyAnswerButton = event.target.closest('[data-copy-answer]');
        if (copyAnswerButton) {
            const savedAnswer = answerBank[copyAnswerButton.dataset.copyAnswer];
            if (!savedAnswer) return;
            
            let formattedAnswer = '';
            if (savedAnswer.situation) formattedAnswer += `Situation: ${savedAnswer.situation}\n`;
            if (savedAnswer.task) formattedAnswer += `Task: ${savedAnswer.task}\n`;
            if (savedAnswer.action || savedAnswer.answer) formattedAnswer += `Action: ${savedAnswer.action || savedAnswer.answer}\n`;
            if (savedAnswer.result) formattedAnswer += `Result: ${savedAnswer.result}\n`;
            formattedAnswer = formattedAnswer.trim();
            
            navigator.clipboard.writeText(`${savedAnswer.question}\n\n${formattedAnswer}`)
                .then(() => {
                    copyAnswerButton.title = 'Copied';
                    window.setTimeout(() => { copyAnswerButton.title = 'Copy answer'; }, 1500);
                })
                .catch(() => { copyAnswerButton.title = 'Could not copy'; });
            return;
        }

        const tab = event.target.closest('[data-filter]');
        if (tab) {
            const filter = tab.dataset.filter;
            if (filter === 'all') {
                activeFilters = ['all'];
            } else {
                if (activeFilters.includes('all')) {
                    activeFilters = [filter];
                } else if (activeFilters.includes(filter)) {
                    activeFilters = activeFilters.filter(f => f !== filter);
                    if (activeFilters.length === 0) activeFilters = ['all'];
                } else {
                    activeFilters.push(filter);
                }
            }
            document.querySelectorAll('[data-filter]').forEach((item) => {
                const isActive = activeFilters.includes(item.dataset.filter);
                item.classList.toggle('active', isActive);
                item.setAttribute('aria-selected', String(isActive));
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

    function updateKanbanAgeWarning(card, stage) {
        const activeStages = new Set(['Applied', 'Assessment', 'Interview', 'Offer']);
        const appliedAt = card.dataset.applied ? new Date(`${card.dataset.applied}T00:00:00`) : null;
        const ageDays = appliedAt && !Number.isNaN(appliedAt.getTime())
            ? Math.max(0, Math.floor((Date.now() - appliedAt.getTime()) / 86400000))
            : 0;
        card.classList.remove('application-age-attention', 'application-age-overdue');
        const ageSignal = card.querySelector('[data-kanban-age-signal]');
        if (!activeStages.has(stage) || ageDays < 14) {
            if (ageSignal) ageSignal.hidden = true;
            return;
        }
        const state = ageDays >= 30 ? 'overdue' : 'attention';
        card.classList.add(`application-age-${state}`);
        if (ageSignal) {
            ageSignal.hidden = false;
            ageSignal.className = `age-${state}`;
            ageSignal.textContent = `Waiting ${ageDays}d`;
        }
    }

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
            card.dataset.stage = stage;
            updateKanbanAgeWarning(card, stage);
            updateKanbanCounts();
            showKanbanFeedback(`${card.dataset.role} moved to ${stage}.`, false);
        } catch (_error) {
            previousColumn.querySelector('[data-kanban-items]').appendChild(card);
            card.querySelector('[data-kanban-select]').value = previousColumn.dataset.kanbanStage;
            card.dataset.stage = previousColumn.dataset.kanbanStage;
            updateKanbanAgeWarning(card, previousColumn.dataset.kanbanStage);
            updateKanbanCounts();
            showKanbanFeedback(`Could not move ${card.dataset.role}. Please try again.`, true);
        }
    }

    let kanbanFeedbackTimer;

    function showKanbanFeedback(message, isError) {
        const feedback = document.getElementById('kanban-announcer');
        if (!feedback) return;
        window.clearTimeout(kanbanFeedbackTimer);
        feedback.textContent = message;
        feedback.classList.toggle('is-error', isError);
        feedback.hidden = false;
        kanbanFeedbackTimer = window.setTimeout(() => {
            feedback.hidden = true;
        }, 3000);
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
        const controls = kanbanScrollButtons[0]?.parentElement;
        if (controls) controls.hidden = maximumScroll <= 1;
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

    const applicationContextMenu = document.querySelector('[data-application-context-menu]');
    const applicationContextFeedback = document.querySelector('[data-context-feedback]');
    let contextApplicationCard = null;
    let contextMenuTrigger = null;
    let contextFeedbackTimer;

    function applicationCardDetails(card) {
        const companyLink = card.querySelector('a[href*="/job-tracker/company/"]');
        const company = companyLink?.textContent.trim() || '';
        const role = card.dataset.role || card.querySelector('.application-role, h3')?.textContent.trim() || '';
        const stage = card.dataset.stage || card.querySelector('[data-kanban-select], .quick-status select')?.value || '';
        return { company, companyUrl: companyLink?.href || '#', role, stage };
    }

    function closeApplicationContextMenu(restoreFocus = false) {
        if (!applicationContextMenu || applicationContextMenu.hidden) return;
        applicationContextMenu.hidden = true;
        contextApplicationCard = null;
        if (restoreFocus) contextMenuTrigger?.focus();
        contextMenuTrigger = null;
    }

    function openApplicationContextMenu(card, x, y, trigger) {
        if (!applicationContextMenu) return;
        const details = applicationCardDetails(card);
        contextApplicationCard = card;
        contextMenuTrigger = trigger;

        applicationContextMenu.querySelector('[data-context-title]').textContent = details.role;
        applicationContextMenu.querySelector('[data-context-company]').href = details.companyUrl;
        applicationContextMenu.querySelectorAll('[data-context-stage]').forEach((button) => {
            const isCurrent = button.dataset.contextStage === details.stage;
            button.setAttribute('aria-checked', String(isCurrent));
            button.disabled = isCurrent;
        });

        applicationContextMenu.hidden = false;
        applicationContextMenu.style.left = '0';
        applicationContextMenu.style.top = '0';
        const bounds = applicationContextMenu.getBoundingClientRect();
        const left = Math.max(8, Math.min(x, window.innerWidth - bounds.width - 8));
        const top = Math.max(8, Math.min(y, window.innerHeight - bounds.height - 8));
        applicationContextMenu.style.left = `${left}px`;
        applicationContextMenu.style.top = `${top}px`;
        applicationContextMenu.querySelector('[role^="menuitem"]:not(:disabled)')?.focus();
    }

    function showApplicationContextFeedback(message, isError = false) {
        if (!applicationContextFeedback) return;
        window.clearTimeout(contextFeedbackTimer);
        applicationContextFeedback.textContent = message;
        applicationContextFeedback.classList.toggle('is-error', isError);
        applicationContextFeedback.hidden = false;
        contextFeedbackTimer = window.setTimeout(() => {
            applicationContextFeedback.hidden = true;
        }, 3000);
    }

    function adjustStatusFilterCount(stage, amount) {
        const output = document.querySelector(`[data-filter="${CSS.escape(stage)}"] span`);
        if (!output) return;
        output.textContent = String(Math.max(0, Number(output.textContent || 0) + amount));
    }

    async function updateListApplicationStage(card, stage) {
        const previousStage = card.dataset.stage;
        const response = await fetch(`/admin/job-tracker/${card.dataset.applicationId}/update-stage-ajax`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'HX-Request': 'true'
            },
            body: new URLSearchParams({ stage })
        });
        if (!response.ok) throw new Error('Could not update application status.');

        const template = document.createElement('template');
        template.innerHTML = (await response.text()).trim();
        const replacement = template.content.firstElementChild;
        if (!replacement?.classList.contains('application-card')) {
            throw new Error('The updated application card was not returned.');
        }

        card.replaceWith(replacement);
        window.htmx?.process(replacement);
        formatDates(replacement);
        filterApplications();
        adjustStatusFilterCount(previousStage, -1);
        adjustStatusFilterCount(stage, 1);
    }

    async function moveApplicationFromContextMenu(card, stage) {
        const destination = document.querySelector(`[data-kanban-stage="${CSS.escape(stage)}"]`);
        if (card.classList.contains('kanban-card') && destination) {
            await moveKanbanCard(card, destination);
            return;
        }
        await updateListApplicationStage(card, stage);
        showApplicationContextFeedback(`${card.dataset.role} moved to ${stage}.`);
    }

    document.addEventListener('contextmenu', (event) => {
        if (event.target.closest('input, textarea, select')) return;
        const card = event.target.closest('.kanban-card, .application-card');
        if (!card || !applicationContextMenu) return;
        event.preventDefault();
        openApplicationContextMenu(card, event.clientX, event.clientY, event.target);
    });

    applicationContextMenu?.addEventListener('click', async (event) => {
        const stageButton = event.target.closest('[data-context-stage]');
        const copyButton = event.target.closest('[data-context-copy]');
        const card = contextApplicationCard;
        if (!card) return;

        if (stageButton) {
            const stage = stageButton.dataset.contextStage;
            closeApplicationContextMenu();
            try {
                await moveApplicationFromContextMenu(card, stage);
            } catch (_error) {
                showApplicationContextFeedback(`Could not move ${card.dataset.role}. Please try again.`, true);
            }
            return;
        }

        if (copyButton) {
            const details = applicationCardDetails(card);
            closeApplicationContextMenu();
            try {
                await navigator.clipboard.writeText(`${details.company} - ${details.role}`);
                showApplicationContextFeedback('Company and role copied.');
            } catch (_error) {
                showApplicationContextFeedback('Could not copy the application details.', true);
            }
            return;
        }

        const prepSheetBtn = event.target.closest('[data-context-prep-sheet]');
        if (prepSheetBtn) {
            closeApplicationContextMenu();
            window.open(`/admin/job-tracker/${card.dataset.applicationId}/prep-sheet`, '_blank');
            return;
        }

        const updateButton = event.target.closest('[data-context-update]');
        if (updateButton) {
            closeApplicationContextMenu();
            const detailsElement = card.querySelector('details.application-workspace');
            if (detailsElement) {
                detailsElement.open = true;
                const noteInput = detailsElement.querySelector('form.workspace-inline-form input[name="note"]');
                if (noteInput) {
                    noteInput.focus();
                }
            } else {
                const note = window.prompt(`Add a timeline update for ${card.dataset.role}:`);
                if (note && note.trim()) {
                    fetch(`/admin/job-tracker/${card.dataset.applicationId}/add-note-ajax`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                            'HX-Request': 'true'
                        },
                        body: new URLSearchParams({ note: note.trim() })
                    }).then(async (response) => {
                        if (response.ok) {
                            showApplicationContextFeedback('Update added.');
                            // The card returned is a list card, so for kanban we just need to let the user know it succeeded.
                            // If they refresh or go to list view, it will be there.
                        } else {
                            showApplicationContextFeedback('Could not add update.', true);
                        }
                    }).catch(() => {
                        showApplicationContextFeedback('Could not add update.', true);
                    });
                }
            }
            return;
        }
    });

    document.addEventListener('pointerdown', (event) => {
        if (!applicationContextMenu?.hidden && !applicationContextMenu.contains(event.target)) {
            closeApplicationContextMenu();
        }
    });

    document.addEventListener('keydown', (event) => {
        const card = event.target.closest?.('.kanban-card, .application-card');
        if ((event.key === 'ContextMenu' || (event.shiftKey && event.key === 'F10')) && card) {
            event.preventDefault();
            const bounds = card.getBoundingClientRect();
            openApplicationContextMenu(card, bounds.left + 12, bounds.top + 12, event.target);
            return;
        }
        if (!applicationContextMenu || applicationContextMenu.hidden) return;
        if (event.key === 'Escape') {
            event.preventDefault();
            closeApplicationContextMenu(true);
            return;
        }
        if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const items = [...applicationContextMenu.querySelectorAll('[role^="menuitem"]:not(:disabled)')];
        const currentIndex = items.indexOf(document.activeElement);
        let nextIndex = currentIndex;
        if (event.key === 'ArrowDown') nextIndex = (currentIndex + 1) % items.length;
        if (event.key === 'ArrowUp') nextIndex = (currentIndex - 1 + items.length) % items.length;
        if (event.key === 'Home') nextIndex = 0;
        if (event.key === 'End') nextIndex = items.length - 1;
        items[nextIndex]?.focus();
    });

    window.addEventListener('blur', () => closeApplicationContextMenu());
    window.addEventListener('resize', () => closeApplicationContextMenu());
    document.addEventListener('scroll', () => closeApplicationContextMenu(), true);

    let touchStartX = 0;
    let touchStartY = 0;
    let touchTarget = null;
    
    document.addEventListener('touchstart', (e) => {
        const card = e.target.closest('.application-card, .kanban-card');
        if (!card) return;
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
        touchTarget = card;
    }, { passive: true });
    
    document.addEventListener('touchend', (e) => {
        if (!touchTarget) return;
        const touchEndX = e.changedTouches[0].screenX;
        const touchEndY = e.changedTouches[0].screenY;
        
        const deltaX = touchStartX - touchEndX;
        const deltaY = Math.abs(touchStartY - touchEndY);
        
        // Swipe left threshold (e.g., 50px) and vertical variance limit
        if (deltaX > 50 && deltaY < 30) {
            contextApplicationCard = touchTarget;
            const rect = touchTarget.getBoundingClientRect();
            openApplicationContextMenu(
                touchTarget,
                Math.min(rect.right - 20, window.innerWidth - 200),
                rect.top + 20
            );
        }
        
        touchTarget = null;
    }, { passive: true });

    formatDates();
})();
