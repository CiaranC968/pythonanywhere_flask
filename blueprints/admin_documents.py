import re

from flask import make_response, request

from blueprints.admin_config import DOCUMENT_SECTION_CONFIG


def document_sections(portfolio):
    sections = []
    for config in DOCUMENT_SECTION_CONFIG:
        key = config["key"]
        max_items = document_max_items(config)
        source_items = portfolio.get(key, [])
        item_list = [
            {
                "id": str(getattr(item, "id", "")),
                "label": document_item_label(key, item),
                "meta": document_item_meta(key, item),
                "checked": not max_items or index < max_items,
            }
            for index, item in enumerate(source_items)
        ]
        warning = ""
        if max_items and len(source_items) > max_items:
            warning = config.get("overflow_warning") or (
                f"This section is capped at {max_items} items to protect the PDF layout."
            )
        sections.append({**config, "item_list": item_list, "warning": warning})
    return sections


def document_item_label(section, item):
    if section == "experience":
        role = getattr(item, "role", "")
        company = getattr(item, "company", "")
        return " - ".join(part for part in [role, company] if part) or getattr(item, "id", "Experience")
    if section == "education":
        return getattr(item, "degree", "") or getattr(item, "university", "") or getattr(item, "id", "Education")
    if section == "certificates":
        return getattr(item, "title", "") or getattr(item, "issuer", "") or getattr(item, "id", "Certificate")
    return getattr(item, "title", "") or getattr(item, "id", section.title())


def document_item_meta(section, item):
    if section == "experience":
        return " | ".join(
            part for part in [getattr(item, "period", ""), getattr(item, "location", "")] if part
        )
    if section == "projects":
        return getattr(item, "status", "")
    if section == "skills":
        return ", ".join((getattr(item, "tags", None) or [])[:6])
    if section == "education":
        return " | ".join(
            part for part in [getattr(item, "university", ""), getattr(item, "year", "")] if part
        )
    if section == "certificates":
        return " | ".join(
            part for part in [getattr(item, "issuer", ""), getattr(item, "date", "")] if part
        )
    return ""


def selected_document_portfolio(portfolio, include_sections):
    selected = {}
    include_sections = set(include_sections)
    for config in DOCUMENT_SECTION_CONFIG:
        key = config["key"]
        if key not in include_sections:
            selected[key] = []
            continue

        selected_ids = set(request.form.getlist(f"{key}_ids"))
        selected[key] = [
            item
            for item in portfolio.get(key, [])
            if str(getattr(item, "id", "")) in selected_ids
        ]
        max_items = document_max_items(config)
        if max_items:
            selected[key] = selected[key][:max_items]
    return selected


def cv_options():
    return {
        "header_subtitle": request.form.get("header_subtitle", "").strip(),
        "document_title": "Custom CV",
    }


def resume_options():
    header_subtitle = request.form.get("header_subtitle", "").strip()
    company_name = request.form.get("company_name", "").strip()
    target_role = request.form.get("target_role", "").strip()

    if not header_subtitle:
        header_subtitle = target_role or "Resume Letter"

    def replace_tags(content):
        if not content:
            return content
        company = company_name or "your organisation"
        role = target_role or "the advertised role"
        content = re.sub(re.escape("{company}"), company, content, flags=re.IGNORECASE)
        return re.sub(re.escape("{role}"), role, content, flags=re.IGNORECASE)

    return {
        "header_subtitle": header_subtitle,
        "company_name": company_name,
        "target_role": target_role,
        "summary": replace_tags(request.form.get("resume_summary", "").strip()),
        "details": replace_tags(request.form.get("company_details", "").strip()),
        "keywords": request.form.get("resume_keywords", "").strip(),
        "conclusion": replace_tags(request.form.get("resume_conclusion", "").strip()),
        "document_title": " | ".join(part for part in ["Resume Letter", company_name] if part),
    }


def document_filename(full_name, document_type, options, safe_filename):
    base = safe_filename(full_name)
    if document_type == "resume":
        target = options.get("company_name") or options.get("target_role") or "Resume_Letter"
        return f"{base}_{safe_filename(target)}_Resume_Letter.pdf"
    return f"{base}_Custom_CV.pdf"


def document_max_items(config: dict) -> int:
    value = config.get("max_items", 0)
    return value if isinstance(value, int) else 0


def pdf_response(pdf_bytes, filename):
    disposition = (
        "inline"
        if request.form.get("disposition") == "inline" or request.args.get("disposition") == "inline"
        else "attachment"
    )
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    response.headers["Cache-Control"] = "no-store"
    return response
