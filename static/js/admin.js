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
            inputRow.className = 'flex gap-2';
            input.dataset.iconInput = '';
            inputRow.appendChild(input);

            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'rounded-xl bg-warm-900 px-3 py-2 text-xs font-black text-white hover:bg-warm-700';
            button.textContent = 'Pick';
            button.dataset.openIconPicker = '';
            button.addEventListener('click', () => setIconPickerTarget(input));
            inputRow.appendChild(button);
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
        row.className = 'structured-row';

        const header = document.createElement('div');
        header.className = 'mb-3 flex items-center justify-between gap-3';
        const title = document.createElement('p');
        title.className = 'text-sm font-black text-warm-800';
        title.textContent = editor.dataset.label || 'Item';
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'rounded-lg border border-red-200 px-3 py-1.5 text-xs font-black text-red-600 hover:bg-red-50';
        remove.textContent = 'Remove';
        remove.addEventListener('click', () => {
            row.remove();
            syncEditor(editor);
        });
        header.append(title, remove);
        row.appendChild(header);

        const grid = document.createElement('div');
        grid.className = 'grid gap-3 md:grid-cols-2';
        const fields = fieldSets[kind] || fieldSets.list;
        fields.forEach((field) => {
            const value = kind === 'list' ? data.value : data[field.key];
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
            button.className = 'flex items-center gap-3 rounded-xl border border-warm-200 bg-warm-50 p-3 text-left hover:border-brand-accent hover:bg-white';
            button.innerHTML = `<span class="flex h-10 w-10 items-center justify-center rounded-lg bg-white text-lg text-warm-900"><i class="${className}" aria-hidden="true"></i></span><span><span class="block text-sm font-black text-warm-900">${label}</span><span class="block text-xs font-semibold text-warm-500">${className}</span></span>`;
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
        if (!input.id) return;
        const preview = document.querySelector(`[data-icon-preview="${input.id}"]`);
        if (preview) preview.className = input.value || 'fas fa-code';
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.structured-editor').forEach(initEditor);
        renderIconPicker();

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

        document.querySelector('[data-close-icon-picker]')?.addEventListener('click', closeIconPicker);
        document.querySelector('[data-icon-search]')?.addEventListener('input', renderIconPicker);
        document.querySelectorAll('[data-icon-input]').forEach((input) => {
            input.addEventListener('input', () => updateIconPreview(input));
            updateIconPreview(input);
        });

        document.querySelectorAll('[data-admin-form]').forEach((form) => {
            form.addEventListener('submit', () => {
                form.querySelectorAll('.structured-editor').forEach(syncEditor);
            });
        });
    });
})();
