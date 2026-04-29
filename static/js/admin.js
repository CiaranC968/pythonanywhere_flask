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
        wrapper.appendChild(input);

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

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.structured-editor').forEach(initEditor);

        document.addEventListener('click', (event) => {
            const button = event.target.closest('[data-action="add-row"]');
            if (!button) return;
            const editor = button.closest('.structured-editor');
            createRow(editor, {});
            syncEditor(editor);
        });

        document.querySelectorAll('[data-admin-form]').forEach((form) => {
            form.addEventListener('submit', () => {
                form.querySelectorAll('.structured-editor').forEach(syncEditor);
            });
        });
    });
})();
