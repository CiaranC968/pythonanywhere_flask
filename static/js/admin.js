(function () {
    const fieldSets = {
        list: [{ key: 'value', label: 'Item', type: 'text', wide: true }],
        links: [
            { key: 'label', label: 'Label', type: 'text' },
            { key: 'url', label: 'URL', type: 'url', wide: true },
            { key: 'icon', label: 'Icon class', type: 'text', placeholder: 'fas fa-external-link-alt' }
        ],
        stats: [
            { key: 'label', label: 'Label', type: 'text' },
            { key: 'value', label: 'Value', type: 'text' },
            { key: 'icon', label: 'Icon class', type: 'text', placeholder: 'fas fa-calendar' }
        ],
        timeline: [
            { key: 'role', label: 'Role', type: 'text' },
            { key: 'period', label: 'Period', type: 'text', placeholder: 'Jan 2026 - Present' },
            { key: 'loc', label: 'Location', type: 'text' },
            { key: 'desc', label: 'Description', type: 'textarea', wide: true }
        ],
        stages: [
            { key: 'stage', label: 'Stage', type: 'text', placeholder: 'Stage 1' },
            { key: 'code', label: 'Module code', type: 'text', placeholder: 'TM111' },
            { key: 'title', label: 'Module title', type: 'text', wide: true },
            { key: 'grade', label: 'Grade', type: 'text' },
            { key: 'credits', label: 'Credits', type: 'number' }
        ]
    };

    function parseJson(value, fallback) {
        try {
            return value ? JSON.parse(value) : fallback;
        } catch (_error) {
            return fallback;
        }
    }

    function createInput(field, value) {
        const wrapper = document.createElement('label');
        wrapper.className = field.wide ? 'block md:col-span-2' : 'block';

        const text = document.createElement('span');
        text.className = 'mb-1 block text-xs font-black uppercase tracking-wider text-warm-500';
        text.textContent = field.label;
        wrapper.appendChild(text);

        const input = field.type === 'textarea' ? document.createElement('textarea') : document.createElement('input');
        input.className = 'admin-input text-sm';
        input.dataset.key = field.key;
        input.value = value ?? '';
        if (field.type !== 'textarea') input.type = field.type;
        if (field.placeholder) input.placeholder = field.placeholder;
        if (field.type === 'textarea') input.rows = 3;

        if (field.key === 'icon') {
            const inputRow = document.createElement('span');
            inputRow.className = 'flex items-center gap-3';
            input.dataset.iconInput = '';
            input.type = 'hidden';
            inputRow.appendChild(input);

            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'icon-square-button flex h-12 w-12 items-center justify-center rounded-xl border border-warm-200 bg-white text-xl text-warm-900 hover:border-brand-accent';
            button.dataset.openIconPicker = '';
            button.setAttribute('aria-label', `Choose ${field.label}`);
            const preview = document.createElement('i');
            preview.className = value || field.placeholder || 'fas fa-code';
            preview.dataset.iconPreviewFor = '';
            preview.setAttribute('aria-hidden', 'true');
            button.appendChild(preview);
            inputRow.appendChild(button);

            const helper = document.createElement('span');
            helper.className = 'text-xs font-bold text-warm-500';
            helper.dataset.iconText = '';
            helper.textContent = iconLabel(value || field.placeholder) || 'Choose icon';
            inputRow.appendChild(helper);
            wrapper.appendChild(inputRow);
        } else {
            wrapper.appendChild(input);
        }

        return wrapper;
    }

    function createRow(editor, data = {}) {
        const kind = editor.dataset.kind;
        const rows = editor.querySelector('[data-role="rows"]');
        const row = document.createElement('div');
        
        const kindNames = {
            links: 'Link',
            stats: 'Metric',
            timeline: 'Timeline Item',
            stages: 'Module'
        };
        const kindName = kindNames[kind] || 'Item';

        function renumberRows() {
            const allRows = rows.querySelectorAll('.structured-row');
            allRows.forEach((r, idx) => {
                const t = r.querySelector('.structured-row-title');
                if (t) t.textContent = `${kindName} #${idx + 1}`;
            });
        }

        if (kind === 'list') {
            const field = fieldSets.list[0];
            const value = data.value;
            row.className = 'structured-row flex items-center gap-3 bg-white p-3 rounded-2xl border border-warm-200 shadow-sm';
            
            const input = document.createElement('input');
            input.className = 'admin-input text-sm grow';
            input.dataset.key = field.key;
            input.value = value ?? '';
            input.type = 'text';
            input.placeholder = 'Enter bullet point...';
            
            const remove = document.createElement('button');
            remove.type = 'button';
            remove.className = 'rounded-xl border border-red-200 bg-red-50/20 hover:bg-red-50 p-2.5 text-red-600 flex items-center justify-center transition-colors cursor-pointer shrink-0';
            remove.innerHTML = '<i class="fas fa-trash-alt text-sm"></i>';
            remove.title = 'Remove item';
            remove.addEventListener('click', () => {
                row.remove();
                syncEditor(editor);
            });
            
            row.append(input, remove);
            rows.appendChild(row);
            row.addEventListener('input', () => syncEditor(editor));
            return;
        }

        row.className = 'structured-row bg-white border border-warm-200 rounded-2xl p-5 shadow-sm';

        const header = document.createElement('div');
        header.className = 'mb-4 pb-3 border-b border-warm-100 flex items-center justify-between gap-3';
        
        const title = document.createElement('p');
        title.className = 'structured-row-title text-sm font-black text-warm-900';
        const index = rows.querySelectorAll('.structured-row').length + 1;
        title.textContent = `${kindName} #${index}`;

        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'rounded-xl border border-red-200 bg-red-50/20 hover:bg-red-50 px-3.5 py-1.5 text-xs font-black text-red-650 transition-colors flex items-center gap-1.5 cursor-pointer';
        remove.innerHTML = '<i class="fas fa-trash-alt text-[10px]"></i> Remove';
        remove.addEventListener('click', () => {
            row.remove();
            renumberRows();
            syncEditor(editor);
        });
        
        header.append(title, remove);
        row.appendChild(header);

        const grid = document.createElement('div');
        grid.className = 'grid gap-3 md:grid-cols-2';
        const fields = fieldSets[kind] || fieldSets.list;
        fields.forEach((field) => {
            const value = data[field.key];
            grid.appendChild(createInput(field, value));
        });
        row.appendChild(grid);
        rows.appendChild(row);
        row.addEventListener('input', () => syncEditor(editor));
    }

    function renderProgress(editor, value) {
        const rows = editor.querySelector('[data-role="rows"]');
        rows.innerHTML = '';
        const data = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
        const row = document.createElement('div');
        row.className = 'structured-row grid gap-3 md:grid-cols-4';
        [
            { key: 'label', label: 'Label', type: 'text', placeholder: 'Experience' },
            { key: 'value', label: 'Value', type: 'number' },
            { key: 'unit', label: 'Unit', type: 'text', placeholder: 'years' },
            { key: 'max', label: 'Max', type: 'number' }
        ].forEach((field) => row.appendChild(createInput(field, data[field.key])));
        row.addEventListener('input', () => syncEditor(editor));
        rows.appendChild(row);
    }

    function normaliseInitial(kind, value) {
        if (kind === 'list') {
            return Array.isArray(value) ? value.map((item) => ({ value: String(item ?? '') })) : [];
        }
        if (kind === 'stages') {
            const rows = [];
            Object.entries(value || {}).forEach(([stage, modules]) => {
                (modules || []).forEach((module) => rows.push({ stage, ...module }));
            });
            return rows;
        }
        if (kind === 'progress') return value || {};
        return Array.isArray(value) ? value : [];
    }

    function initEditor(editor) {
        const output = document.getElementById(editor.dataset.target);
        const kind = editor.dataset.kind;
        const initial = normaliseInitial(kind, parseJson(output.value, kind === 'progress' ? {} : []));

        if (kind === 'progress') {
            renderProgress(editor, initial);
            syncEditor(editor);
            return;
        }

        if (initial.length) {
            initial.forEach((row) => createRow(editor, row));
        } else {
            createRow(editor, {});
        }
        syncEditor(editor);
    }

    function rowData(row, kind) {
        const data = {};
        row.querySelectorAll('[data-key]').forEach((input) => {
            const value = input.value.trim();
            if (!value) return;
            data[input.dataset.key] = input.type === 'number' ? Number(value) : value;
        });
        if (kind === 'list') return data.value || '';
        return data;
    }

    function syncEditor(editor) {
        const output = document.getElementById(editor.dataset.target);
        const kind = editor.dataset.kind;
        const rows = [...editor.querySelectorAll('.structured-row')];

        if (kind === 'progress') {
            const data = rowData(rows[0], kind);
            output.value = JSON.stringify(Object.keys(data).length ? data : {});
            return;
        }

        if (kind === 'stages') {
            const grouped = {};
            rows.map((row) => rowData(row, kind)).forEach((data) => {
                if (!data.stage || !data.title) return;
                const stage = data.stage;
                delete data.stage;
                grouped[stage] = grouped[stage] || [];
                grouped[stage].push(data);
            });
            output.value = JSON.stringify(grouped);
            return;
        }

        const data = rows.map((row) => rowData(row, kind)).filter((item) => {
            if (typeof item === 'string') return item.length > 0;
            return Object.keys(item).length > 0;
        });
        output.value = JSON.stringify(data);
    }

    let iconPickerTarget = null;

    function iconChoices() {
        const form = document.querySelector('[data-admin-form]');
        if (!form) return [];
        return parseJson(form.dataset.iconChoices, []);
    }

    function iconLabel(className) {
        const match = iconChoices().find(([value]) => value === className);
        return match ? match[1] : '';
    }

    function setIconPickerTarget(target) {
        iconPickerTarget = typeof target === 'string' ? document.getElementById(target) : target;
        renderIconPicker();
        const dialog = document.getElementById('iconPicker');
        if (!dialog) return;
        if (typeof dialog.showModal === 'function') dialog.showModal();
        else dialog.setAttribute('open', 'open');
    }

    function closeIconPicker() {
        const dialog = document.getElementById('iconPicker');
        if (!dialog) return;
        if (typeof dialog.close === 'function') dialog.close();
        else dialog.removeAttribute('open');
    }

    function renderIconPicker() {
        const list = document.querySelector('[data-icon-list]');
        if (!list) return;

        const search = (document.querySelector('[data-icon-search]')?.value || '').trim().toLowerCase();
        const choices = iconChoices().filter(([className, label]) => {
            return !search || className.toLowerCase().includes(search) || label.toLowerCase().includes(search);
        });
        list.innerHTML = '';

        choices.forEach(([className, label]) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'icon-picker-option flex flex-col items-center justify-center gap-2 rounded-2xl border border-warm-200 bg-warm-50 p-3 text-center hover:border-brand-accent hover:bg-white';
            button.innerHTML = `<i class="${className} text-2xl text-warm-900" aria-hidden="true"></i><span class="text-xs font-black text-warm-700">${label}</span>`;
            button.addEventListener('click', () => {
                if (iconPickerTarget) {
                    iconPickerTarget.value = className;
                    iconPickerTarget.dispatchEvent(new Event('input', { bubbles: true }));
                    updateIconPreview(iconPickerTarget);
                }
                closeIconPicker();
            });
            list.appendChild(button);
        });
    }

    function updateIconPreview(input) {
        const preview = input.id ? document.querySelector(`[data-icon-preview="${input.id}"]`) : input.closest('span')?.querySelector('[data-icon-preview-for]');
        if (preview) preview.className = input.value || 'fas fa-code';
        if (input.id) {
            const label = document.querySelector(`[data-icon-label="${input.id}"]`);
            if (label) label.textContent = iconLabel(input.value) || 'Custom icon selected';
            return;
        }
        const text = input.closest('span')?.querySelector('[data-icon-text]');
        if (text) text.textContent = iconLabel(input.value) || 'Custom icon';
    }

    function activateFormTab(index) {
        document.querySelectorAll('[data-form-tab]').forEach((tab) => {
            const active = tab.dataset.formTab === String(index);
            tab.setAttribute('aria-selected', active ? 'true' : 'false');
            tab.classList.toggle('border-brand-accent', active);
            tab.classList.toggle('text-warm-900', active);
            tab.classList.toggle('bg-brand-accent', active);
            tab.classList.toggle('text-brand-dark', active);
        });
        document.querySelectorAll('[data-form-panel]').forEach((panel) => {
            panel.classList.toggle('hidden', panel.dataset.formPanel !== String(index));
        });
    }

    let adminDialogOpener = null;

    function activateTemplateEditor(index) {
        const selectedIndex = String(index);
        document.querySelectorAll('[data-template-editor-tab]').forEach((tab) => {
            tab.setAttribute('aria-selected', String(tab.dataset.templateEditorTab === selectedIndex));
        });
        document.querySelectorAll('[data-template-editor-panel]').forEach((panel) => {
            panel.hidden = panel.dataset.templateEditorPanel !== selectedIndex;
        });
    }

    function showAdminDialog(dialog, opener, templateIndex) {
        if (!dialog) return;

        if (templateIndex !== undefined) activateTemplateEditor(templateIndex);
        adminDialogOpener = opener;
        if (!dialog.open) {
            if (typeof dialog.showModal === 'function') dialog.showModal();
            else dialog.setAttribute('open', 'open');
        }
        window.requestAnimationFrame(() => {
            const focusRoot = dialog.querySelector('[data-template-editor-panel]:not([hidden])') || dialog;
            focusRoot.querySelector('[autofocus], input:not([type="hidden"]), select, textarea')?.focus();
        });
    }

    function openAdminDialog(opener) {
        showAdminDialog(
            document.getElementById(opener.dataset.adminDialogOpen),
            opener,
            opener.dataset.templateIndex
        );
    }

    function closeAdminDialog(dialog) {
        if (!dialog) return;
        if (typeof dialog.close === 'function') dialog.close();
        else {
            dialog.removeAttribute('open');
            adminDialogOpener?.focus();
        }
    }

    function globalSearchLinks() {
        return [...document.querySelectorAll('#admin-search-results .admin-search-result')];
    }

    function moveGlobalSearchSelection(direction) {
        const links = globalSearchLinks();
        if (!links.length) return;
        const currentIndex = links.indexOf(document.activeElement);
        const nextIndex = currentIndex < 0
            ? (direction > 0 ? 0 : links.length - 1)
            : (currentIndex + direction + links.length) % links.length;
        links[nextIndex].focus();
    }

    function openLinkedTemplateEditor() {
        const match = window.location.hash.match(/^#template-editor-(\d+)$/);
        if (!match) return;
        const opener = document.querySelector(`[data-admin-dialog-open="template-library-dialog"][data-template-index="${match[1]}"]`)
            || document.querySelector('[data-admin-dialog-open="template-library-dialog"]');
        showAdminDialog(document.getElementById('template-library-dialog'), opener, match[1]);
    }

    function updateStyleChoice(targetName, value) {
        const input = document.getElementById(targetName);
        if (input) input.value = value;
        document.querySelectorAll(`[data-style-choice][data-target="${targetName}"]`).forEach((button) => {
            const active = button.dataset.value === value;
            button.setAttribute('aria-pressed', active ? 'true' : 'false');
            button.classList.toggle('border-brand-accent', active);
            button.classList.toggle('ring-2', active);
            button.classList.toggle('ring-brand-accent', active);
        });
    }

    function syncDocumentSection(master) {
        const key = master.dataset.documentSectionMaster;
        const container = document.querySelector(`[data-document-section-items="${key}"]`);
        if (!container) return;
        container.classList.toggle('opacity-50', !master.checked);
        container.dataset.documentEnabled = master.checked ? 'true' : 'false';
        syncDocumentLimit(key);
    }

    function syncDocumentLimit(key) {
        const container = document.querySelector(`[data-document-section-items="${key}"]`);
        if (!container) return;

        const max = Number(container.dataset.documentMax || 0);
        const enabled = container.dataset.documentEnabled !== 'false';
        const inputs = [...container.querySelectorAll(`[data-document-item="${key}"]`)];
        const checkedCount = enabled ? inputs.filter((input) => input.checked).length : 0;
        const limitReached = Boolean(enabled && max && checkedCount >= max);
        inputs.forEach((input) => {
            input.disabled = !enabled || (!input.checked && limitReached);
        });

        const countMessage = document.querySelector(`[data-document-count-message="${key}"]`);
        if (countMessage) {
            countMessage.textContent = max ? `${checkedCount}/${max} selected` : `${checkedCount}/${inputs.length} selected`;
        }

        const message = document.querySelector(`[data-document-limit-message="${key}"]`);
        if (message) {
            message.textContent = limitReached ? `Limit reached: ${checkedCount}/${max} selected` : `Choose up to ${max}.`;
        }
    }

    function insertTemplateSentence(button) {
        const target = document.getElementById(button.dataset.templateTarget);
        if (!target) return;

        const company = document.querySelector('[data-template-company]')?.value.trim() || 'the company';
        const role = document.querySelector('[data-template-role]')?.value.trim() || 'the role';
        const templateText = parseJson(button.dataset.templateText, button.dataset.templateText || '');
        const sentence = templateText
            .replaceAll('{company}', company)
            .replaceAll('{role}', role);
        const separator = target.value.trim() ? (target.id === 'company_details' ? '\n' : '\n\n') : '';
        target.value = `${target.value.trim()}${separator}${sentence}`;
        target.focus();
        target.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function applyRolePreset(button) {
        const preset = parseJson(button.dataset.rolePreset, null);
        if (!preset) return;

        const company = document.querySelector('[data-template-company]')?.value.trim() || '{company}';
        const replacements = {
            header_subtitle: preset.header_subtitle,
            target_role: preset.target_role,
            resume_keywords: preset.resume_keywords,
            resume_summary: preset.resume_summary,
            company_details: preset.company_details,
            resume_conclusion: preset.resume_conclusion
        };

        Object.entries(replacements).forEach(([id, value]) => {
            const field = document.getElementById(id);
            if (!field || value === undefined) return;
            field.value = String(value).replaceAll('{company}', company).replaceAll('{role}', preset.target_role || 'the role');
            field.dispatchEvent(new Event('input', { bubbles: true }));
        });

        document.querySelectorAll('[data-role-preset]').forEach((presetButton) => {
            const active = presetButton === button;
            presetButton.classList.toggle('border-brand-accent', active);
            presetButton.classList.toggle('bg-brand-accent/10', active);
        });
    }

    function initSortableLists() {
        document.querySelectorAll('[data-sortable-section]').forEach((tbody) => {
            let draggedRow = null;

            tbody.addEventListener('dragstart', (event) => {
                const row = event.target.closest('tr[data-sortable-id]');
                if (!row) {
                    event.preventDefault();
                    return;
                }
                draggedRow = row;
                row.classList.add('opacity-50');
                if (event.dataTransfer) {
                    event.dataTransfer.effectAllowed = 'move';
                    event.dataTransfer.setData('text/plain', row.dataset.sortableId);
                }
            });

            tbody.addEventListener('dragover', (event) => {
                if (!draggedRow) return;
                event.preventDefault();
                const afterElement = dragAfterElement(tbody, event.clientY);
                if (afterElement) tbody.insertBefore(draggedRow, afterElement);
                else {
                    const firstLockedRow = tbody.querySelector('tr:not([data-sortable-id])');
                    if (firstLockedRow) tbody.insertBefore(draggedRow, firstLockedRow);
                    else tbody.appendChild(draggedRow);
                }
            });

            tbody.addEventListener('dragend', () => {
                if (!draggedRow) return;
                draggedRow.classList.remove('opacity-50');
                draggedRow = null;
                saveSortableOrder(tbody);
            });

            tbody.addEventListener('drop', (event) => {
                if (draggedRow) event.preventDefault();
            });
        });
    }

    function dragAfterElement(container, y) {
        return [...container.querySelectorAll('tr[data-sortable-id]:not(.opacity-50)')]
            .reduce((closest, child) => {
                const box = child.getBoundingClientRect();
                const offset = y - box.top - box.height / 2;
                if (offset < 0 && offset > closest.offset) {
                    return { offset, element: child };
                }
                return closest;
            }, { offset: Number.NEGATIVE_INFINITY, element: null }).element;
    }

    async function saveSortableOrder(tbody) {
        const ids = [...tbody.querySelectorAll('tr[data-sortable-id]')].map((row) => row.dataset.sortableId);
        if (!ids.length || !tbody.dataset.sortUrl) return;

        tbody.classList.add('opacity-70');
        try {
            const response = await fetch(tbody.dataset.sortUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids })
            });
            if (!response.ok) throw new Error('Could not save order');
            tbody.querySelectorAll('[data-sort-order-cell]').forEach((cell, index) => {
                cell.textContent = String((index + 1) * 10);
            });
        } catch (_error) {
            window.alert('Could not save the new project order. Refresh and try again.');
        } finally {
            tbody.classList.remove('opacity-70');
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.structured-editor').forEach(initEditor);
        initSortableLists();
        renderIconPicker();
        activateFormTab(0);

        document.addEventListener('click', (event) => {
            const button = event.target.closest('[data-action="add-row"]');
            if (!button) return;
            const editor = button.closest('.structured-editor');
            createRow(editor, {});
            syncEditor(editor);
        });

        document.addEventListener('click', (event) => {
            const button = event.target.closest('[data-open-icon-picker]');
            if (!button) return;
            const target = button.dataset.target ? document.getElementById(button.dataset.target) : button.previousElementSibling;
            setIconPickerTarget(target);
        });

        document.addEventListener('click', (event) => {
            const linkedRow = event.target.closest('[data-row-href]');
            if (linkedRow && !event.target.closest('a, button, form, input, select, textarea')) {
                window.location.assign(linkedRow.dataset.rowHref);
                return;
            }

            const adminDialogButton = event.target.closest('[data-admin-dialog-open]');
            if (adminDialogButton) {
                openAdminDialog(adminDialogButton);
                return;
            }

            const adminDialogClose = event.target.closest('[data-admin-dialog-close]');
            if (adminDialogClose) {
                closeAdminDialog(adminDialogClose.closest('dialog'));
                return;
            }

            const templateEditorTab = event.target.closest('[data-template-editor-tab]');
            if (templateEditorTab) {
                activateTemplateEditor(templateEditorTab.dataset.templateEditorTab);
                return;
            }

            const tab = event.target.closest('[data-form-tab]');
            if (tab) {
                activateFormTab(tab.dataset.formTab);
                return;
            }

            const styleChoice = event.target.closest('[data-style-choice]');
            if (styleChoice) {
                updateStyleChoice(styleChoice.dataset.target, styleChoice.dataset.value);
            }

            const templateButton = event.target.closest('[data-template-target]');
            if (templateButton) {
                insertTemplateSentence(templateButton);
                return;
            }

            const rolePreset = event.target.closest('[data-role-preset]');
            if (rolePreset) {
                applyRolePreset(rolePreset);
            }
        });

        document.addEventListener('change', (event) => {
            const master = event.target.closest('[data-document-section-master]');
            if (master) {
                syncDocumentSection(master);
                return;
            }

            const item = event.target.closest('[data-document-item]');
            if (item) syncDocumentLimit(item.dataset.documentItem);
        });

        document.addEventListener('keydown', (event) => {
            if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
                event.preventDefault();
                const opener = document.querySelector('[data-admin-dialog-open="admin-search-dialog"]');
                showAdminDialog(document.getElementById('admin-search-dialog'), opener);
                return;
            }

            const searchDialog = document.getElementById('admin-search-dialog');
            if (searchDialog?.open && ['ArrowDown', 'ArrowUp'].includes(event.key)) {
                event.preventDefault();
                moveGlobalSearchSelection(event.key === 'ArrowDown' ? 1 : -1);
                return;
            }
            if (searchDialog?.open && event.key === 'Enter' && event.target.matches('.admin-search-box input')) {
                const firstResult = globalSearchLinks()[0];
                if (firstResult) {
                    event.preventDefault();
                    firstResult.click();
                }
                return;
            }

            const activeTab = event.target.closest('[data-template-editor-tab]');
            if (!activeTab || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;

            const tabs = [...document.querySelectorAll('[data-template-editor-tab]')];
            const direction = event.key === 'ArrowRight' ? 1 : -1;
            const nextTab = tabs[(tabs.indexOf(activeTab) + direction + tabs.length) % tabs.length];
            event.preventDefault();
            activateTemplateEditor(nextTab.dataset.templateEditorTab);
            nextTab.focus();
        });

        document.addEventListener('submit', (event) => {
            const form = event.target.closest('[data-confirm]');
            if (form && !window.confirm(form.dataset.confirm)) event.preventDefault();
        });

        document.querySelector('[data-close-icon-picker]')?.addEventListener('click', closeIconPicker);
        document.querySelector('[data-icon-search]')?.addEventListener('input', renderIconPicker);
        document.querySelectorAll('[data-icon-input]').forEach((input) => {
            input.addEventListener('input', () => updateIconPreview(input));
            updateIconPreview(input);
        });
        document.querySelectorAll('[data-style-input]').forEach((input) => {
            updateStyleChoice(input.id, input.value);
        });
        document.querySelectorAll('.admin-dialog').forEach((dialog) => {
            dialog.addEventListener('click', (event) => {
                if (event.target === dialog) closeAdminDialog(dialog);
            });
            dialog.addEventListener('close', () => adminDialogOpener?.focus());
        });
        window.addEventListener('hashchange', openLinkedTemplateEditor);
        openLinkedTemplateEditor();

        document.querySelectorAll('[data-admin-form]').forEach((form) => {
            form.addEventListener('submit', () => {
                form.querySelectorAll('.structured-editor').forEach(syncEditor);
            });
        });
        document.querySelectorAll('[data-document-section-master]').forEach(syncDocumentSection);
    });
})();
