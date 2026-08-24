(() => {
    const dataElement = document.getElementById('resume-builder-data');
    const form = document.getElementById('resume-builder-form');
    if (!dataElement || !form) return;

    const presets = JSON.parse(dataElement.textContent);
    const fields = {
        company: document.getElementById('company_name'),
        role: document.getElementById('target_role'),
        recipient: document.getElementById('recipient_name'),
        extraPoints: document.getElementById('additional_points'),
        header: document.getElementById('header_subtitle'),
        keywords: document.getElementById('resume_keywords'),
        summary: document.getElementById('resume_summary'),
        details: document.getElementById('company_details'),
        conclusion: document.getElementById('resume_conclusion')
    };
    const preview = {
        date: document.getElementById('preview-date'),
        salutation: document.getElementById('preview-salutation'),
        intro: document.getElementById('preview-intro'),
        bullets: document.getElementById('preview-bullets'),
        conclusion: document.getElementById('preview-conclusion')
    };
    let activePreset = 0;

    function lines(value) {
        return (value || '').split('\n').map((line) => line.trim()).filter(Boolean);
    }

    function replaceTokens(value) {
        const company = fields.company.value.trim() || '[Company]';
        const role = fields.role.value.trim() || '[Job role]';
        return (value || '').replace(/\{company\}/gi, company).replace(/\{role\}/gi, role);
    }

    function allPoints(preset) {
        return [...lines(preset.company_details), ...lines(fields.extraPoints.value)];
    }

    function syncForm() {
        const preset = presets[activePreset];
        fields.header.value = preset.header_subtitle || preset.label;
        fields.keywords.value = preset.resume_keywords || '';
        fields.summary.value = preset.resume_summary || '';
        fields.details.value = allPoints(preset).join('\n');
        fields.conclusion.value = preset.resume_conclusion || '';
    }

    function renderPreview() {
        const preset = presets[activePreset];
        syncForm();
        preview.salutation.textContent = `Dear ${fields.recipient.value.trim() || 'Hiring Manager'},`;
        preview.intro.textContent = replaceTokens(preset.resume_summary);
        preview.conclusion.textContent = replaceTokens(preset.resume_conclusion);
        preview.bullets.replaceChildren();

        allPoints(preset).forEach((point) => {
            const item = document.createElement('li');
            item.textContent = replaceTokens(point);
            preview.bullets.appendChild(item);
        });
    }

    function selectPreset(index) {
        const previousRole = presets[activePreset]?.target_role || '';
        activePreset = index;
        const nextRole = presets[activePreset]?.target_role || '';
        if (!fields.role.value.trim() || fields.role.value === previousRole) fields.role.value = nextRole;

        document.querySelectorAll('[data-resume-template]').forEach((button) => {
            button.setAttribute('aria-pressed', String(Number(button.dataset.resumeTemplate) === activePreset));
        });
        renderPreview();
    }

    function openLinkedTemplateEditor() {
        if (!window.location.hash) return;
        const target = document.querySelector(window.location.hash);
        if (target instanceof HTMLDetailsElement && target.classList.contains('preset-editor')) {
            target.open = true;
        }
    }

    document.querySelectorAll('[data-resume-template]').forEach((button) => {
        button.addEventListener('click', () => selectPreset(Number(button.dataset.resumeTemplate)));
    });
    [fields.company, fields.role, fields.recipient, fields.extraPoints].forEach((field) => {
        field.addEventListener('input', renderPreview);
    });
    form.addEventListener('submit', syncForm);

    preview.date.textContent = new Intl.DateTimeFormat('en-GB', {
        day: 'numeric', month: 'long', year: 'numeric'
    }).format(new Date());
    window.addEventListener('hashchange', openLinkedTemplateEditor);
    openLinkedTemplateEditor();
    selectPreset(0);
})();
