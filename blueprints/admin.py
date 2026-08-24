import json
import os
import re
import calendar as calendar_module
from collections import Counter
from datetime import datetime, timedelta
from functools import wraps
from importlib import import_module
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename
from sqlalchemy import func
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy import text as sql_text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash

from extensions import db
from blueprints.job_tracker_analytics import (
    JOB_INTERVIEW_STAGES,
    JOB_STAGES,
    JOB_STAGE_VALUES,
    company_key as _company_key,
    job_tracker_metrics as _job_tracker_metrics,
    normalise_job_datetime as _normalise_job_datetime,
    parse_job_datetime as _parse_job_datetime,
)
from models import (
    Experience,
    JobApplication,
    JobAttachment,
    JobContact,
    JobStatusEvent,
    Profile,
    Project,
    ResumeTemplate,
    Skill,
)
from portfolio_data import get_portfolio, get_profile

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

JOB_ATTACHMENT_EXTENSIONS = {".doc", ".docx", ".jpeg", ".jpg", ".pdf", ".png", ".txt"}
JOB_OPTIONAL_FIELDS = {
    "stage_updated_at",
    "interview_date",
    "assessment_date",
    "application_deadline",
    "job_url",
    "company_url",
    "company_address",
    "linkedin_url",
    "salary",
    "location",
    "follow_up_date",
}
JOB_TEXT_FIELDS = (
    "company",
    "role",
    "applied_date",
    "stage_updated_at",
    "interview_date",
    "assessment_date",
    "application_deadline",
    "badges",
    "notes",
    "job_url",
    "company_url",
    "company_address",
    "linkedin_url",
    "salary",
    "location",
    "source",
    "follow_up_date",
    "reminder_note",
)
JOB_FIELD_LIMITS = {
    "company": 180,
    "role": 180,
    "applied_date": 80,
    "stage_updated_at": 80,
    "interview_date": 80,
    "assessment_date": 80,
    "application_deadline": 80,
    "badges": 500,
    "job_url": 500,
    "company_url": 500,
    "company_address": 500,
    "linkedin_url": 500,
    "salary": 120,
    "location": 180,
    "source": 120,
    "follow_up_date": 80,
}
JOB_DATE_FIELDS = {
    "applied_date",
    "stage_updated_at",
    "interview_date",
    "assessment_date",
    "application_deadline",
    "follow_up_date",
}

from blueprints.admin_config import (
    IMAGE_FIELDS,
    ICON_FIELDS,
    STYLE_FIELDS,
    FIELD_GROUPS,
    ICON_CHOICES,
    STYLE_CHOICES,
    SECTIONS,
    DOCUMENT_SECTION_CONFIG,
    ALLOWED_RESUME_TEMPLATE_TARGETS,
    RESUME_SENTENCE_TEMPLATES,
    RESUME_ROLE_PRESETS,
    FIELD_HELP,
    JSON_EXAMPLES,
    JSON_EDITOR_KINDS,
)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin.login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped


def _admin_login_destination():
    destination = request.args.get("next", "")
    if destination.startswith("/") and not destination.startswith("//"):
        return destination
    return url_for("admin.dashboard")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        configured_hash = current_app.config.get("ADMIN_PASSWORD_HASH", "")
        configured_password = current_app.config.get("ADMIN_PASSWORD", "")

        if not configured_hash and not configured_password:
            flash("Admin login is not configured. Set ADMIN_PASSWORD or ADMIN_PASSWORD_HASH.", "error")
            return render_template("admin/login.html"), 503

        valid = False
        if configured_hash:
            valid = check_password_hash(configured_hash, password)
        elif configured_password:
            valid = password == configured_password

        if valid:
            session["admin_authenticated"] = True
            return redirect(_admin_login_destination())

        flash("Incorrect admin password.", "error")

    return render_template("admin/login.html")


@admin_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_required
def dashboard():
    counts = {}
    database_error = ""
    try:
        for section, config in SECTIONS.items():
            model = config["model"]
            if config.get("singleton"):
                counts[section] = 1
            else:
                query = model.query
                if hasattr(model, "is_visible"):
                    query = query.filter_by(is_visible=True)
                counts[section] = query.count()
        counts["job_applications"] = JobApplication.query.count()
        cutoff = datetime.now() - timedelta(days=24)
        counts["stale_job_applications"] = sum(
            bool(applied_at and applied_at <= cutoff)
            for application in JobApplication.query.filter_by(stage="Applied")
            if (applied_at := _parse_job_datetime(application.applied_date))
        )
    except SQLAlchemyError as exc:
        database_error = str(exc)
        counts = {section: 0 for section in SECTIONS}
        counts["job_applications"] = 0
        counts["stale_job_applications"] = 0

    admin_password_missing = not current_app.config.get("ADMIN_PASSWORD_HASH") and not current_app.config.get(
        "ADMIN_PASSWORD")
    return render_template(
        "admin/dashboard.html",
        sections=SECTIONS,
        counts=counts,
        admin_password_missing=admin_password_missing,
        database_error=database_error,
    )


@admin_bp.route("/diagnostics")
@admin_required
def diagnostics():
    database_status = "ok"
    database_error = ""
    table_names = []

    try:
        db.session.execute(sql_text("SELECT 1"))
        table_names = sqlalchemy_inspect(db.engine).get_table_names()
    except SQLAlchemyError as exc:
        database_status = "error"
        database_error = str(exc)

    return render_template(
        "admin/diagnostics.html",
        database_status=database_status,
        database_error=database_error,
        database_uri=_mask_database_uri(current_app.config["SQLALCHEMY_DATABASE_URI"]),
        table_names=table_names,
        engine_options=current_app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}),
    )


@admin_bp.route("/deployment-checklist")
@admin_required
def deployment_checklist():
    table_names = []
    database_error = ""
    database_ok = False
    database_dialect = "unknown"
    required_tables = {
        "profile",
        "experience",
        "project",
        "skill",
        "education",
        "certificate",
        "resume_template",
    }

    try:
        db.session.execute(sql_text("SELECT 1"))
        inspector = sqlalchemy_inspect(db.engine)
        table_names = inspector.get_table_names()
        database_dialect = db.engine.dialect.name
        database_ok = True
    except SQLAlchemyError as exc:
        database_error = str(exc)

    table_set = set(table_names)
    upload_root = _static_upload_root()
    checks = [
        {
            "label": "Database connection",
            "ok": database_ok,
            "detail": database_error or f"{database_dialect} connection is responding.",
        },
        {
            "label": "Required tables",
            "ok": required_tables.issubset(table_set),
            "detail": "Missing: " + ", ".join(sorted(required_tables - table_set))
            if required_tables - table_set
            else "All portfolio and resume-template tables are present.",
        },
        {
            "label": "Admin password",
            "ok": bool(current_app.config.get("ADMIN_PASSWORD_HASH") or current_app.config.get("ADMIN_PASSWORD")),
            "detail": "ADMIN_PASSWORD_HASH or ADMIN_PASSWORD is configured.",
        },
        {
            "label": "Secret key",
            "ok": bool(current_app.config.get("SECRET_KEY")),
            "detail": "SECRET_KEY is configured for sessions.",
        },
        {
            "label": "Static upload path",
            "ok": bool(upload_root and os.path.isdir(upload_root)),
            "detail": upload_root or "No upload path found.",
        },
        {
            "label": "ReportLab PDF library",
            "ok": _module_available("reportlab"),
            "detail": "Needed for CV and resume PDF exports.",
        },
        {
            "label": "Pillow image library",
            "ok": _module_available("PIL"),
            "detail": "Needed for image handling in generated PDFs.",
        },
    ]

    return render_template(
        "admin/deployment_checklist.html",
        checks=checks,
        database_uri=_mask_database_uri(current_app.config["SQLALCHEMY_DATABASE_URI"]),
        database_dialect=database_dialect,
        table_names=table_names,
    )


@admin_bp.route("/cv-builder")
@admin_required
def cv_builder():
    portfolio = get_portfolio()
    return render_template(
        "admin/cv_builder.html",
        profile=get_profile(),
        document_sections=_document_sections(portfolio),
    )


@admin_bp.route("/cv-builder/pdf", methods=["POST"])
@admin_required
def cv_builder_pdf():
    from blueprints.cv import build_cv_pdf, _safe_filename

    dependency_error = _pdf_dependency_error("admin.cv_builder")
    if dependency_error:
        return dependency_error

    portfolio = get_portfolio()
    include_sections = request.form.getlist("sections")
    selected_portfolio = _selected_document_portfolio(portfolio, include_sections)
    resume_options = _cv_options()

    has_selected_content = any(selected_portfolio.get(section) for section in include_sections)
    if not include_sections or not has_selected_content:
        flash("Choose at least one section and one item before generating the PDF.", "error")
        return redirect(url_for("admin.cv_builder"))

    pdf_bytes = build_cv_pdf(
        profile=get_profile(),
        portfolio=selected_portfolio,
        include_sections=include_sections,
        resume_options=resume_options,
    )

    profile = get_profile()
    filename = _document_filename(profile.full_name, "cv", resume_options, _safe_filename)
    return _pdf_response(pdf_bytes, filename)


@admin_bp.route("/resume-builder")
@admin_required
def resume_builder():
    return render_template(
        "admin/resume_builder.html",
        profile=get_profile(),
        resume_presets=(RESUME_ROLE_PRESETS[0], RESUME_ROLE_PRESETS[-1]),
    )


@admin_bp.route("/resume-builder/templates", methods=["POST"])
@admin_required
def add_resume_template():
    values = _validated_resume_template_form_values()
    if not values:
        return redirect(url_for("admin.resume_builder"))

    max_order = db.session.query(func.max(ResumeTemplate.sort_order)).scalar()
    template = ResumeTemplate()
    _apply_resume_template_values(template, values)
    template.sort_order = (max_order or 0) + 10
    template.is_visible = True
    db.session.add(template)
    if _commit_or_flash():
        flash("Template sentence added.", "success")
    return redirect(url_for("admin.resume_builder"))


@admin_bp.route("/resume-builder/templates/<int:template_id>/edit", methods=["POST"])
@admin_required
def edit_resume_template(template_id: int):
    template = db.session.get(ResumeTemplate, template_id)
    if not template:
        abort(404)

    values = _validated_resume_template_form_values()
    if not values:
        return redirect(url_for("admin.resume_builder"))

    _apply_resume_template_values(template, values)
    template.sort_order = _form_integer("sort_order", template.sort_order)
    if _commit_or_flash():
        flash("Template sentence saved.", "success")
    return redirect(url_for("admin.resume_builder"))


@admin_bp.route("/resume-builder/templates/<int:template_id>/delete", methods=["POST"])
@admin_required
def delete_resume_template(template_id: int):
    return _set_resume_template_visibility(template_id, visible=False)


@admin_bp.route("/resume-builder/templates/<int:template_id>/restore", methods=["POST"])
@admin_required
def restore_resume_template(template_id: int):
    return _set_resume_template_visibility(template_id, visible=True)


def _set_resume_template_visibility(template_id, visible):
    template = db.session.get(ResumeTemplate, template_id)
    if not template:
        abort(404)

    template.is_visible = visible
    if _commit_or_flash():
        action = "restored" if visible else "archived"
        flash(f"Template sentence {action}.", "success")
    return redirect(url_for("admin.resume_builder"))


@admin_bp.route("/resume-builder/pdf", methods=["POST"])
@admin_required
def resume_builder_pdf():
    from blueprints.cv import build_resume_letter_pdf, _safe_filename

    dependency_error = _pdf_dependency_error("admin.resume_builder")
    if dependency_error:
        return dependency_error

    resume_options = _resume_options()
    pdf_bytes = build_resume_letter_pdf(profile=get_profile(), resume_options=resume_options)

    profile = get_profile()
    filename = _document_filename(profile.full_name, "resume", resume_options, _safe_filename)
    return _pdf_response(pdf_bytes, filename)


@admin_bp.route("/projects/reorder", methods=["POST"])
@admin_required
def reorder_projects():
    payload = request.get_json(silent=True) or {}
    item_ids = [str(item_id) for item_id in payload.get("ids", []) if item_id]
    if not item_ids:
        return jsonify({"ok": False, "error": "No project ids supplied."}), 400

    projects = {
        project.id: project
        for project in Project.query.filter(Project.id.in_(item_ids)).all()
    }
    for index, item_id in enumerate(item_ids, start=1):
        project = projects.get(item_id)
        if project and project.is_visible:
            project.sort_order = index * 10

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.exception("Could not reorder projects: %s", exc)
        return jsonify({"ok": False, "error": "Could not save the project order."}), 500

    return jsonify({"ok": True})


@admin_bp.route("/<section>")
@admin_required
def list_items(section: str):
    config = _section_config(section)
    if config.get("singleton"):
        return redirect(url_for("admin.edit_item", section=section, item_id=1))

    model = config["model"]
    order_by = [model.sort_order.asc(), model.id.asc()]
    if hasattr(model, "is_visible"):
        order_by.insert(0, model.is_visible.desc())
    items = model.query.order_by(*order_by).all()
    return render_template("admin/list.html", section=section, config=config, items=items)


@admin_bp.route("/<section>/new", methods=["GET", "POST"])
@admin_required
def new_item(section: str):
    config = _section_config(section)
    if config.get("singleton"):
        abort(404)

    item = config["model"]()
    _apply_new_defaults(item, config)
    if request.method == "POST":
        if _populate_item(item, config, is_new=True):
            db.session.add(item)
            if _commit_or_flash():
                flash(f"{config['label']} item created.", "success")
                return redirect(url_for("admin.list_items", section=section))

    return _render_item_form(section, config, item, "Create")


@admin_bp.route("/<section>/<item_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_item(section: str, item_id: str):
    config = _section_config(section)
    item = db.session.get(config["model"], _identity_for_section(section, item_id))
    if not item and config.get("singleton"):
        item = Profile()
        item.id = 1
        db.session.add(item)
        db.session.commit()
    if not item:
        abort(404)

    if request.method == "POST":
        if _populate_item(item, config, is_new=False):
            if _commit_or_flash():
                flash(f"{config['label']} item saved.", "success")
                if config.get("singleton"):
                    return redirect(url_for("admin.dashboard"))
                return redirect(url_for("admin.list_items", section=section))

    return _render_item_form(section, config, item, "Save")


@admin_bp.route("/<section>/<item_id>/delete", methods=["POST"])
@admin_required
def delete_item(section: str, item_id: str):
    config, item = _collection_item_or_404(section, item_id)
    return _set_collection_item_visibility(section, config, item, visible=False)


@admin_bp.route("/<section>/<item_id>/restore", methods=["POST"])
@admin_required
def restore_item(section: str, item_id: str):
    config, item = _collection_item_or_404(section, item_id)
    return _set_collection_item_visibility(section, config, item, visible=True)


def _set_collection_item_visibility(section, config, item, visible):
    redirect_response = redirect(url_for("admin.list_items", section=section))

    if visible:
        if not hasattr(item, "is_visible"):
            abort(404)
        item.is_visible = True
    elif hasattr(item, "is_visible"):
        item.is_visible = False
    else:
        db.session.delete(item)

    if not _commit_or_flash():
        return redirect_response
    action = "restored" if visible else "archived"
    flash(f"{config['label']} item {action}.", "success")
    return redirect_response


def _document_sections(portfolio):
    sections = []
    for config in DOCUMENT_SECTION_CONFIG:
        key = config["key"]
        max_items = _document_max_items(config)
        source_items = portfolio.get(key, [])
        item_list = [
            {
                "id": str(getattr(item, "id", "")),
                "label": _document_item_label(key, item),
                "meta": _document_item_meta(key, item),
                "checked": not max_items or index < max_items,
            }
            for index, item in enumerate(source_items)
        ]
        warning = ""
        if max_items and len(source_items) > max_items:
            warning = config.get(
                "overflow_warning") or f"This section is capped at {max_items} items to protect the PDF layout."
        sections.append({**config, "item_list": item_list, "warning": warning})
    return sections


def _resume_sentence_templates():
    templates = [{**template, "id": None, "is_custom": False} for template in RESUME_SENTENCE_TEMPLATES]
    custom_templates = _custom_resume_templates()
    templates.extend(
        {
            "id": template.id,
            "is_custom": True,
            "target": template.target,
            "label": template.label,
            "text": template.text,
        }
        for template in custom_templates
    )
    return templates


def _custom_resume_templates(include_hidden=False):
    try:
        query = ResumeTemplate.query
        if not include_hidden:
            query = query.filter_by(is_visible=True)
        return query.order_by(ResumeTemplate.is_visible.desc(), ResumeTemplate.sort_order.asc(),
                              ResumeTemplate.id.asc()).all()
    except SQLAlchemyError as exc:
        current_app.logger.exception("Could not load custom resume templates: %s", exc)
        db.session.rollback()
        return []


def _resume_template_form_values():
    values = {
        "target": request.form.get("template_target", "").strip(),
        "label": request.form.get("template_label", "").strip(),
        "text": request.form.get("template_text", "").strip(),
    }
    if values["target"] not in ALLOWED_RESUME_TEMPLATE_TARGETS:
        return None
    return values if values["label"] and values["text"] else None


def _validated_resume_template_form_values():
    values = _resume_template_form_values()
    if values is None:
        flash("Choose a section, label, and sentence before saving the template.", "error")
    return values


def _apply_resume_template_values(template, values):
    for field, value in values.items():
        setattr(template, field, value)


def _document_item_label(section, item):
    if section == "experience":
        role = getattr(item, "role", "")
        company = getattr(item, "company", "")
        return " - ".join(part for part in [role, company] if part) or getattr(item, "id", "Experience")
    if section == "education":
        return getattr(item, "degree", "") or getattr(item, "university", "") or getattr(item, "id", "Education")
    if section == "certificates":
        return getattr(item, "title", "") or getattr(item, "issuer", "") or getattr(item, "id", "Certificate")
    return getattr(item, "title", "") or getattr(item, "id", section.title())


def _document_item_meta(section, item):
    if section == "experience":
        return " | ".join(part for part in [getattr(item, "period", ""), getattr(item, "location", "")] if part)
    if section == "projects":
        return getattr(item, "status", "")
    if section == "skills":
        return ", ".join((getattr(item, "tags", None) or [])[:6])
    if section == "education":
        return " | ".join(part for part in [getattr(item, "university", ""), getattr(item, "year", "")] if part)
    if section == "certificates":
        return " | ".join(part for part in [getattr(item, "issuer", ""), getattr(item, "date", "")] if part)
    return ""


def _selected_document_portfolio(portfolio, include_sections):
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
        max_items = _document_max_items(config)
        if max_items:
            selected[key] = selected[key][:max_items]
    return selected


def _cv_options():
    return {
        "header_subtitle": request.form.get("header_subtitle", "").strip(),
        "document_title": "Custom CV",
    }


def _resume_options():
    header_subtitle = request.form.get("header_subtitle", "").strip()
    company_name = request.form.get("company_name", "").strip()
    target_role = request.form.get("target_role", "").strip()

    if not header_subtitle:
        header_subtitle = target_role or "Resume Letter"

    def replace_tags(content):
        if not content:
            return content

        c_val = company_name if company_name else "your organisation"
        r_val = target_role if target_role else "the advertised role"

        content = re.sub(re.escape("{company}"), c_val, content, flags=re.IGNORECASE)
        content = re.sub(re.escape("{role}"), r_val, content, flags=re.IGNORECASE)
        return content

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


def _document_filename(full_name, document_type, options, safe_filename):
    base = safe_filename(full_name)
    if document_type == "resume":
        target = options.get("company_name") or options.get("target_role") or "Resume_Letter"
        return f"{base}_{safe_filename(target)}_Resume_Letter.pdf"
    return f"{base}_Custom_CV.pdf"


def _document_max_items(config: dict) -> int:
    value = config.get("max_items", 0)
    return value if isinstance(value, int) else 0


def _pdf_response(pdf_bytes, filename):
    disposition = "inline" if request.form.get("disposition") == "inline" or request.args.get(
        "disposition") == "inline" else "attachment"
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    response.headers["Cache-Control"] = "no-store"
    return response


def _section_config(section: str):
    if section not in SECTIONS:
        abort(404)
    return SECTIONS[section]


def _identity_for_section(section: str, item_id: str | int) -> str | int:
    if section == "profile":
        return int(item_id)
    return str(item_id)


def _collection_item_or_404(section, item_id):
    config = _section_config(section)
    if config.get("singleton"):
        abort(404)

    item = db.session.get(config["model"], _identity_for_section(section, item_id))
    if not item:
        abort(404)
    return config, item


def _render_item_form(section, config, item, action):
    return render_template(
        "admin/form.html",
        section=section,
        config=config,
        item=item,
        action=action,
        **_form_context(section),
    )


def _form_context(section):
    return {
        "field_help": FIELD_HELP,
        "json_examples": JSON_EXAMPLES,
        "json_editor_kinds": JSON_EDITOR_KINDS,
        "field_groups": _field_groups(section),
        "image_fields": IMAGE_FIELDS,
        "icon_fields": ICON_FIELDS,
        "style_fields": STYLE_FIELDS,
        "icon_choices": ICON_CHOICES,
        "style_choices": STYLE_CHOICES,
    }


def _field_groups(section):
    configured = FIELD_GROUPS.get(section)
    if configured:
        return configured

    fields = [name for name, _label, _field_type in SECTIONS[section]["fields"]]
    return [("Content", fields)]


def _populate_item(item, config, is_new):
    try:
        for name, _label, field_type in config["fields"]:
            if name == "id" and not is_new:
                continue

            if field_type == "checkbox":
                value = name in request.form
            elif field_type == "integer":
                raw_value = request.form.get(name, "").strip()
                value = int(raw_value) if raw_value else _integer_default(name)
            elif field_type == "json":
                raw_value = request.form.get(name, "").strip()
                value = json.loads(raw_value) if raw_value else _json_default(name)
            elif name in IMAGE_FIELDS:
                value = _uploaded_asset_value(name) or request.form.get(name, "").strip()
            else:
                value = request.form.get(name, "").strip()

            setattr(item, name, value)

        if is_new and hasattr(item, "id") and not item.id:
            item.id = _unique_slug(config["model"], _title_for_slug(item, config))
    except (TypeError, ValueError) as exc:
        flash(f"Could not save: {exc}", "error")
        return False

    return True


def _json_default(field_name):
    if field_name in {"stages", "progress"}:
        return {}
    return []


def _integer_default(field_name):
    return 0 if field_name == "sort_order" else None


def _form_integer(field_name, default=0):
    raw_value = request.form.get(field_name, "").strip()
    if not raw_value:
        return default or 0
    try:
        return int(raw_value)
    except ValueError:
        return default or 0


def _module_available(module_name):
    try:
        import_module(module_name)
    except ImportError:
        return False
    return True


def _pdf_dependency_error(redirect_endpoint):
    if _module_available("reportlab"):
        return None
    flash("Install reportlab from requirements.txt before generating PDFs.", "error")
    return redirect(url_for(redirect_endpoint))


def _apply_new_defaults(item, config):
    if hasattr(item, "is_visible"):
        item.is_visible = True
    if hasattr(item, "sort_order"):
        model = config["model"]
        max_order = db.session.query(func.max(model.sort_order)).scalar()
        item.sort_order = (max_order or 0) + 10

    for name, _label, field_type in config["fields"]:
        if field_type == "json":
            setattr(item, name, JSON_EXAMPLES.get(name, _json_default(name)))


def _title_for_slug(item, config):
    for field in (config.get("title_field"), "title", "company", "degree", "full_name"):
        if field and getattr(item, field, ""):
            return getattr(item, field)
    return config["label"]


def _unique_slug(model, value):
    base = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-") or "item"
    slug = base
    counter = 2
    while db.session.get(model, slug):
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _uploaded_asset_value(field_name):
    upload = request.files.get(f"{field_name}_upload")
    if not upload or not upload.filename:
        return ""

    filename = secure_filename(upload.filename)
    if not filename:
        return ""

    _name, extension = os.path.splitext(filename)
    if extension.lower() not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        raise ValueError("Images must be JPG, PNG, GIF, WebP, or SVG files.")

    field_config = IMAGE_FIELDS[field_name]
    upload_root = _static_upload_root()
    target_dir = os.path.join(upload_root, field_config["subdir"])
    os.makedirs(target_dir, exist_ok=True)

    filename = _unique_filename(target_dir, filename)
    upload.save(os.path.join(target_dir, filename))

    if field_config["store"] == "static_url":
        return f"/static/{field_config['subdir']}/{filename}"
    return filename


def _static_upload_root():
    configured = os.environ.get("STATIC_UPLOAD_ROOT")
    if configured:
        return configured

    pythonanywhere_static = "/home/ciaranc88/mysite/static"
    if os.path.isdir(pythonanywhere_static):
        return pythonanywhere_static

    return current_app.static_folder


def _unique_filename(directory, filename):
    stem, extension = os.path.splitext(filename)
    candidate = filename
    counter = 2
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{stem}-{counter}{extension}"
        counter += 1
    return candidate


def _commit_database_changes():
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.exception("Could not save admin changes: %s", exc)
        return False
    return True


def _commit_or_flash():
    if not _commit_database_changes():
        flash("The changes could not be saved. Please try again.", "error")
        return False
    return True


def _mask_database_uri(uri):
    uri = str(uri)
    if "://" not in uri or "@" not in uri:
        return uri
    prefix, rest = uri.split("://", 1)
    credentials, host_part = rest.split("@", 1)
    if ":" in credentials:
        username, _password = credentials.split(":", 1)
        credentials = f"{username}:***"
    return f"{prefix}://{credentials}@{host_part}"


def _job_application_form_values():
    values = {}
    for field in JOB_TEXT_FIELDS:
        value = request.form.get(field, "").strip()
        if field in JOB_FIELD_LIMITS:
            value = value[:JOB_FIELD_LIMITS[field]]
        if field in JOB_DATE_FIELDS:
            value = _normalise_job_datetime(value) or ""
        values[field] = value
    stage = request.form.get("stage", "Applied").strip()
    values["stage"] = stage if stage in JOB_STAGE_VALUES else "Applied"
    values["reached_interview"] = (
        request.form.get("reached_interview") == "on" or values["stage"] in JOB_INTERVIEW_STAGES
    )
    values["reached_assessment"] = (
        request.form.get("reached_assessment") == "on" or values["stage"] == "Assessment"
    )
    values["reminder_done"] = request.form.get("reminder_done") == "on"
    return values


def _validated_job_application_form_values():
    values = _job_application_form_values()
    if not values["company"] or not values["role"]:
        flash("Company and Role are required.", "error")
        return None
    return values


def _apply_job_application_values(application, values):
    for field, value in values.items():
        if field in JOB_OPTIONAL_FIELDS:
            value = value or None
        setattr(application, field, value)


def _refresh_job_application_state(applications, now):
    modified = False
    for application in applications:
        if application.stage == "Assessment" and not application.reached_assessment:
            application.reached_assessment = True
            modified = True
        if application.stage in JOB_INTERVIEW_STAGES and not application.reached_interview:
            application.reached_interview = True
            modified = True
        if application.stage != "Not Applied Yet" or not application.application_deadline:
            continue

        deadline = _parse_job_datetime(application.application_deadline, end_of_day=True)
        if deadline and now > deadline:
            previous_stage = application.stage
            application.stage = "Missed Deadline"
            application.stage_updated_at = now.isoformat(timespec="minutes")
            _record_status_event(application, previous_stage, application.stage, now)
            modified = True
    return modified


def _record_status_event(application, from_stage, to_stage, changed_at=None, note=""):
    changed_at = changed_at or datetime.now()
    if isinstance(changed_at, datetime):
        changed_at = changed_at.isoformat(timespec="minutes")
    event = JobStatusEvent()
    event.from_stage = from_stage or ""
    event.to_stage = to_stage
    event.changed_at = changed_at
    event.note = note.strip()
    application.status_events.append(event)
    return event


def _ensure_status_history(applications, now):
    modified = False
    for application in applications:
        if application.status_events:
            continue
        changed_at = application.stage_updated_at or application.applied_date or now.isoformat(timespec="minutes")
        _record_status_event(application, "", application.stage, changed_at)
        modified = True
    return modified


def _job_application_timeline(application):
    events = []

    def add_event(date_value, label, event_type, note=""):
        if not date_value:
            return
        events.append(
            {
                "date": date_value,
                "label": label,
                "type": event_type,
                "note": note,
            }
        )

    add_event(application.applied_date, "Application submitted", "applied")
    add_event(application.assessment_date, "Assessment", "assessment")
    add_event(application.interview_date, "Interview", "interview")
    add_event(application.follow_up_date, "Follow up", "reminder", application.reminder_note)
    if application.stage == "Not Applied Yet":
        add_event(application.application_deadline, "Application deadline", "deadline")

    for status_event in application.status_events:
        if not status_event.from_stage and status_event.to_stage == "Applied":
            continue
        label = f"Status changed to {status_event.to_stage}"
        add_event(status_event.changed_at, label, "status", status_event.note)

    for attachment in application.attachments:
        add_event(attachment.uploaded_at, f"Attached {attachment.original_name}", "attachment", attachment.note)

    unique_events = {}
    for event in events:
        unique_events[(event["date"], event["label"])] = event
    return sorted(
        unique_events.values(),
        key=lambda event: _parse_job_datetime(event["date"]) or datetime.max,
    )


def _job_reminder_state(application, now):
    if not application.follow_up_date:
        return {"state": "none", "label": "No follow-up"}
    if application.reminder_done:
        return {"state": "done", "label": "Follow-up complete"}

    follow_up = _parse_job_datetime(application.follow_up_date, end_of_day=True)
    if not follow_up:
        return {"state": "none", "label": "No follow-up"}
    days_until = (follow_up.date() - now.date()).days
    if days_until < 0:
        return {"state": "overdue", "label": f"Follow-up overdue by {abs(days_until)}d"}
    if days_until == 0:
        return {"state": "today", "label": "Follow up today"}
    if days_until <= 7:
        return {"state": "upcoming", "label": f"Follow up in {days_until}d"}
    return {"state": "scheduled", "label": f"Follow up in {days_until}d"}


def _job_filter_options(applications):
    badges = {
        badge.strip()
        for application in applications
        for badge in (application.badges or "").split(",")
        if badge.strip()
    }


def _job_tracker_template_context(applications, now):
    return {
        "applications": applications,
        "job_stages": JOB_STAGES,
        "stage_counts": Counter(app.stage for app in applications),
        "tracker_metrics": _job_tracker_metrics(applications, now),
        "application_timelines": {
            app.id: _job_application_timeline(app) for app in applications
        },
        "reminder_states": {
            app.id: _job_reminder_state(app, now) for app in applications
        },
        "filter_options": _job_filter_options(applications),
        "today": now.strftime("%Y-%m-%d"),
    }


def _render_job_application_card(application, message="", is_error=False):
    now = datetime.now()
    applications = JobApplication.query.order_by(JobApplication.id.desc()).all()
    metrics = _job_tracker_metrics(applications, now)
    return render_template(
        "admin/partials/job_application_card.html",
        app=application,
        job_stages=JOB_STAGES,
        tracker_metrics=metrics,
        application_timeline=_job_application_timeline(application),
        reminder=_job_reminder_state(application, now),
        stage_update_message=message,
        stage_update_error=is_error,
    )
    return {
        "companies": sorted({app.company for app in applications}, key=str.casefold),
        "sources": sorted({app.source for app in applications if app.source}, key=str.casefold),
        "locations": sorted({app.location for app in applications if app.location}, key=str.casefold),
        "badges": sorted(badges, key=str.casefold),
    }


@admin_bp.route("/job-tracker")
@admin_required
def job_tracker():
    now = datetime.now()
    applications = JobApplication.query.order_by(JobApplication.id.desc()).all()
    state_modified = _refresh_job_application_state(applications, now)
    history_modified = _ensure_status_history(applications, now)
    if state_modified or history_modified:
        _commit_or_flash()

    return render_template(
        "admin/job_tracker.html",
        **_job_tracker_template_context(applications, now),
    )


@admin_bp.route("/job-tracker/add", methods=["POST"])
@admin_required
def add_job_application():
    values = _validated_job_application_form_values()
    if values is None:
        return redirect(url_for("admin.job_tracker"))

    values["applied_date"] = values["applied_date"] or datetime.now().strftime("%Y-%m-%d")
    values["stage_updated_at"] = values["stage_updated_at"] or datetime.now().isoformat(timespec="minutes")
    app = JobApplication()
    _apply_job_application_values(app, values)
    db.session.add(app)
    db.session.flush()
    _record_status_event(app, "", app.stage, app.stage_updated_at or app.applied_date)
    if _commit_or_flash():
        flash("Job application added successfully.", "success")
    return redirect(url_for("admin.job_tracker"))


@admin_bp.route("/job-tracker/<int:app_id>/edit", methods=["POST"])
@admin_required
def edit_job_application(app_id: int):
    app = db.session.get(JobApplication, app_id)
    if not app:
        abort(404)

    values = _validated_job_application_form_values()
    if values is None:
        return redirect(url_for("admin.job_tracker"))

    previous_stage = app.stage
    _apply_job_application_values(app, values)
    if app.stage != previous_stage and not app.stage_updated_at:
        app.stage_updated_at = datetime.now().isoformat(timespec="minutes")
    if app.stage != previous_stage:
        _record_status_event(app, previous_stage, app.stage, app.stage_updated_at)

    if _commit_or_flash():
        flash("Job application updated successfully.", "success")
    return redirect(url_for("admin.job_tracker"))


@admin_bp.route("/job-tracker/<int:app_id>/delete", methods=["POST"])
@admin_required
def delete_job_application(app_id: int):
    app = db.session.get(JobApplication, app_id)
    if not app:
        abort(404)

    attachment_paths = [
        os.path.join(_job_attachment_root(app.id), attachment.stored_name)
        for attachment in app.attachments
    ]
    db.session.delete(app)
    if _commit_or_flash():
        for file_path in attachment_paths:
            try:
                os.remove(file_path)
            except FileNotFoundError:
                continue
            except OSError as exc:
                current_app.logger.warning("Could not remove job attachment %s: %s", file_path, exc)
        flash("Job application deleted.", "success")
    return redirect(url_for("admin.job_tracker"))


@admin_bp.route("/job-tracker/<int:app_id>/reminder", methods=["POST"])
@admin_required
def update_job_reminder(app_id: int):
    application = _job_application_or_404(app_id)
    application.reminder_done = request.form.get("reminder_done") == "true"
    if _commit_or_flash():
        flash("Follow-up updated.", "success")
    return _job_application_redirect(app_id)


@admin_bp.route("/job-tracker/<int:app_id>/stage", methods=["POST"])
@admin_required
def update_job_stage(app_id: int):
    application = _job_application_or_404(app_id)
    payload = request.get_json(silent=True) or {}
    stage = str(payload.get("stage", "")).strip()
    if stage not in JOB_STAGE_VALUES:
        return jsonify({"ok": False, "error": "Invalid application status."}), 400

    previous_stage = application.stage
    if previous_stage != stage:
        application.stage = stage
        application.stage_updated_at = datetime.now().isoformat(timespec="minutes")
        application.reached_assessment = application.reached_assessment or stage == "Assessment"
        application.reached_interview = application.reached_interview or stage in JOB_INTERVIEW_STAGES
        _record_status_event(application, previous_stage, stage, application.stage_updated_at)

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.exception("Could not update job application stage: %s", exc)
        return jsonify({"ok": False, "error": "Could not update the application status."}), 500
    return jsonify({"ok": True, "stage": application.stage})


@admin_bp.route("/job-tracker/company/<path:company_name>")
@admin_required
def job_company(company_name):
    company_key = _company_key(company_name)
    applications = [
        application
        for application in JobApplication.query.order_by(JobApplication.id.desc()).all()
        if _company_key(application.company) == company_key
    ]
    if not applications:
        abort(404)

    now = datetime.now()
    if _ensure_status_history(applications, now):
        _commit_or_flash()
    contacts = [
        contact
        for contact in JobContact.query.order_by(JobContact.id.desc()).all()
        if _company_key(contact.company) == company_key
    ]
    return render_template(
        "admin/job_company.html",
        company=applications[0].company,
        applications=applications,
        contacts=contacts,
        company_metrics=_job_tracker_metrics(applications, now),
        timelines={app.id: _job_application_timeline(app) for app in applications},
        reminder_states={app.id: _job_reminder_state(app, now) for app in applications},
        job_stages=JOB_STAGES,
        today=now.strftime("%Y-%m-%d"),
    )


@admin_bp.route("/job-tracker/contacts", methods=["POST"])
@admin_required
def add_job_contact():
    company = request.form.get("company", "").strip()[:180]
    name = request.form.get("name", "").strip()[:180]
    if not company or not name:
        flash("Company and contact name are required.", "error")
        return redirect(url_for("admin.job_tracker"))

    contact = JobContact()
    contact.company = company
    contact.name = name
    contact.title = request.form.get("title", "").strip()[:180]
    contact.email = request.form.get("email", "").strip()[:255]
    contact.phone = request.form.get("phone", "").strip()[:80]
    contact.linkedin_url = request.form.get("linkedin_url", "").strip()[:500]
    contact.notes = request.form.get("notes", "").strip()
    contact.created_at = datetime.now().isoformat(timespec="minutes")
    application_id = request.form.get("application_id", "").strip()
    if application_id.isdigit():
        linked_application = db.session.get(JobApplication, int(application_id))
        if linked_application and _company_key(linked_application.company) == _company_key(company):
            contact.application_id = linked_application.id
    db.session.add(contact)
    if _commit_or_flash():
        flash("Contact added.", "success")
    return redirect(url_for("admin.job_company", company_name=company))


@admin_bp.route("/job-tracker/contacts/<int:contact_id>/delete", methods=["POST"])
@admin_required
def delete_job_contact(contact_id: int):
    contact = db.session.get(JobContact, contact_id)
    if not contact:
        abort(404)
    company = contact.company
    db.session.delete(contact)
    if _commit_or_flash():
        flash("Contact deleted.", "success")
    return redirect(url_for("admin.job_company", company_name=company))


@admin_bp.route("/job-tracker/<int:app_id>/attachments", methods=["POST"])
@admin_required
def add_job_attachment(app_id: int):
    application = _job_application_or_404(app_id)
    upload = request.files.get("attachment")
    if not upload or not upload.filename:
        flash("Choose a file to attach.", "error")
        return _job_application_redirect(app_id)

    original_name = secure_filename(upload.filename)
    extension = os.path.splitext(original_name)[1].lower()
    if not original_name or extension not in JOB_ATTACHMENT_EXTENSIONS:
        flash("Attachments must be PDF, Word, text, PNG, or JPEG files.", "error")
        return _job_application_redirect(app_id)

    stem = os.path.splitext(original_name)[0][: 255 - len(extension)]
    original_name = f"{stem}{extension}"
    stored_name = f"{uuid4().hex}{extension}"
    upload_root = _job_attachment_root(app_id)
    os.makedirs(upload_root, exist_ok=True)
    stored_path = os.path.join(upload_root, stored_name)
    try:
        upload.save(stored_path)
    except OSError as exc:
        current_app.logger.exception("Could not save job attachment: %s", exc)
        flash("The attachment could not be saved.", "error")
        return _job_application_redirect(app_id)

    attachment = JobAttachment()
    attachment.application_id = app_id
    attachment.original_name = original_name
    attachment.stored_name = stored_name
    attachment.file_type = upload.mimetype or "application/octet-stream"
    attachment.note = request.form.get("note", "").strip()[:255]
    attachment.uploaded_at = datetime.now().isoformat(timespec="minutes")
    db.session.add(attachment)
    if _commit_or_flash():
        flash("Attachment uploaded.", "success")
    else:
        try:
            os.remove(stored_path)
        except OSError:
            current_app.logger.warning("Could not clean up failed attachment upload %s", stored_path)
    return _job_application_redirect(app_id)


@admin_bp.route("/job-tracker/attachments/<int:attachment_id>")
@admin_required
def download_job_attachment(attachment_id: int):
    attachment = db.session.get(JobAttachment, attachment_id)
    if not attachment:
        abort(404)
    return send_from_directory(
        _job_attachment_root(attachment.application_id),
        attachment.stored_name,
        as_attachment=True,
        download_name=attachment.original_name,
    )


@admin_bp.route("/job-tracker/attachments/<int:attachment_id>/delete", methods=["POST"])
@admin_required
def delete_job_attachment(attachment_id: int):
    attachment = db.session.get(JobAttachment, attachment_id)
    if not attachment:
        abort(404)
    app_id = attachment.application_id
    file_path = os.path.join(_job_attachment_root(app_id), attachment.stored_name)
    db.session.delete(attachment)
    if _commit_or_flash():
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            current_app.logger.warning("Could not remove job attachment %s: %s", file_path, exc)
        flash("Attachment deleted.", "success")
    return _job_application_redirect(app_id)


@admin_bp.route("/job-tracker/kanban")
@admin_required
def job_kanban():
    applications = JobApplication.query.order_by(JobApplication.id.desc()).all()
    return render_template(
        "admin/job_kanban.html",
        applications=applications,
        job_stages=JOB_STAGES,
        stage_counts=Counter(app.stage for app in applications),
    )


@admin_bp.route("/job-tracker/calendar")
@admin_required
def job_calendar():
    month_value = request.args.get("month", datetime.now().strftime("%Y-%m"))
    try:
        month_start = datetime.strptime(month_value, "%Y-%m").date().replace(day=1)
    except ValueError:
        month_start = datetime.now().date().replace(day=1)

    applications = JobApplication.query.order_by(JobApplication.id.desc()).all()
    calendar_data = _job_calendar_data(applications, month_start)
    return render_template(
        "admin/job_calendar.html",
        calendar=calendar_data,
        today=datetime.now().date().isoformat(),
    )


def _job_application_or_404(app_id):
    application = db.session.get(JobApplication, app_id)
    if not application:
        abort(404)
    return application


def _job_application_redirect(app_id):
    application = db.session.get(JobApplication, app_id)
    company_name = request.form.get("company", "").strip()
    if company_name and application and _company_key(company_name) == _company_key(application.company):
        return redirect(url_for("admin.job_company", company_name=application.company, _anchor=f"application-{app_id}"))
    return redirect(url_for("admin.job_tracker", _anchor=f"application-{app_id}"))


def _job_attachment_root(app_id):
    base_root = current_app.config.get("JOB_ATTACHMENT_ROOT") or os.path.join(
        current_app.instance_path,
        "job_attachments",
    )
    return os.path.join(base_root, str(app_id))


def _job_calendar_data(applications, month_start):
    events_by_date = {}

    def add_event(date_value, application, label, event_type):
        parsed = _parse_job_datetime(date_value)
        if not parsed:
            return
        event_date = parsed.date().isoformat()
        events_by_date.setdefault(event_date, []).append(
            {
                "application": application,
                "label": label,
                "type": event_type,
            }
        )

    for application in applications:
        if not application.reminder_done:
            add_event(application.follow_up_date, application, "Follow up", "reminder")
        add_event(application.assessment_date, application, "Assessment", "assessment")
        add_event(application.interview_date, application, "Interview", "interview")
        add_event(application.application_deadline, application, "Deadline", "deadline")

    weeks = []
    for week in calendar_module.Calendar(firstweekday=0).monthdatescalendar(month_start.year, month_start.month):
        weeks.append(
            [
                {
                    "date": day,
                    "iso": day.isoformat(),
                    "in_month": day.month == month_start.month,
                    "events": events_by_date.get(day.isoformat(), []),
                }
                for day in week
            ]
        )

    previous_month = (month_start - timedelta(days=1)).replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return {
        "label": month_start.strftime("%B %Y"),
        "month": month_start.strftime("%Y-%m"),
        "previous": previous_month.strftime("%Y-%m"),
        "next": next_month.strftime("%Y-%m"),
        "weeks": weeks,
    }


@admin_bp.route("/quick-add", methods=["POST"])
@admin_required
def quick_add():
    section = request.form.get("section")
    if section == "experience":
        company = request.form.get("company", "").strip()
        role = request.form.get("role", "").strip()
        period = request.form.get("period", "").strip()
        brief = request.form.get("brief", "").strip()
        details_raw = request.form.get("details", "").strip()
        tech_stack_raw = request.form.get("tech_stack", "").strip()
        location = request.form.get("location", "").strip()
        work_type = request.form.get("type", "").strip()

        if not company or not role:
            flash("Company and Role are required.", "error")
            return redirect(url_for("admin.dashboard"))

        details = [line.strip() for line in details_raw.split("\n") if line.strip()]
        tech_stack = [tech.strip() for tech in tech_stack_raw.split(",") if tech.strip()]

        experience = Experience()
        _assign_model_fields(
            experience,
            {
                "company": company,
                "role": role,
                "period": period,
                "brief": brief,
                "details": details,
                "tech_stack": tech_stack,
                "location": location,
                "type": work_type,
                "icon": "fas fa-briefcase",
                "bgIcon": "fas fa-building",
                "iconColor": "text-yellow-600",
                "bgColor": "bg-yellow-50",
                "hoverColor": "text-yellow-900",
                "current": False,
                "is_visible": True,
            },
        )
        _finish_quick_add(experience, Experience, company, "Job experience added successfully.")

    elif section == "skills":
        title = request.form.get("title", "").strip()
        desc = request.form.get("desc", "").strip()
        tags_raw = request.form.get("tags", "").strip()
        progress_val = request.form.get("progress_val", "85").strip()
        theme = request.form.get("theme", "yellow").strip()

        if not title:
            flash("Skill Title is required.", "error")
            return redirect(url_for("admin.dashboard"))

        tags = [tag.strip() for tag in tags_raw.split(",") if tag.strip()]
        themes = {
            "yellow": ("text-yellow-600", "bg-yellow-50", "fas fa-code"),
            "blue": ("text-blue-600", "bg-blue-50", "fas fa-laptop-code"),
            "indigo": ("text-indigo-600", "bg-indigo-50", "fas fa-terminal"),
            "green": ("text-green-600", "bg-green-50", "fas fa-cogs"),
            "red": ("text-red-600", "bg-red-50", "fas fa-bolt"),
        }
        icon_color, bg_color, default_icon = themes.get(theme, themes["yellow"])

        try:
            val = int(progress_val)
        except ValueError:
            val = 85

        progress = {
            "label": "Experience",
            "value": val,
            "unit": "%",
            "max": 100,
        }

        skill = Skill()
        _assign_model_fields(
            skill,
            {
                "title": title,
                "desc": desc,
                "icon": default_icon,
                "iconColor": icon_color,
                "bgColor": bg_color,
                "tags": tags,
                "progress": progress,
                "stats": [],
                "is_visible": True,
            },
        )
        _finish_quick_add(skill, Skill, title, "Skill added successfully.")

    return redirect(url_for("admin.dashboard"))


def _assign_model_fields(item, values):
    for field, value in values.items():
        setattr(item, field, value)


def _finish_quick_add(item, model, slug_value, success_message):
    max_order = db.session.query(func.max(model.sort_order)).scalar()
    item.sort_order = (max_order or 0) + 10
    item.id = _unique_slug(model, slug_value)
    db.session.add(item)
    if _commit_or_flash():
        flash(success_message, "success")


@admin_bp.route("/job-tracker/<int:app_id>/update-stage-ajax", methods=["POST"])
@admin_required
def update_job_stage_ajax(app_id: int):
    app = db.session.get(JobApplication, app_id)
    if not app:
        abort(404)

    is_htmx = request.headers.get("HX-Request") == "true"
    stage = request.form.get("stage", "").strip()
    additional_notes = request.form.get("additional_notes", "").strip()
    date_val = request.form.get("date_val", "").strip()

    previous_stage = app.stage
    if stage in JOB_STAGE_VALUES:
        app.stage = stage
        if stage in JOB_INTERVIEW_STAGES:
            app.reached_interview = True
        if stage == "Assessment":
            app.reached_assessment = True
    else:
        if is_htmx:
            return _render_job_application_card(
                app,
                message="Choose a valid application status.",
                is_error=True,
            )
        flash("Choose a valid application status.", "error")
        return redirect(url_for("admin.job_tracker"))

    normalized_date = _normalise_job_datetime(date_val)
    if stage != previous_stage:
        app.stage_updated_at = normalized_date or datetime.now().isoformat(timespec="minutes")
        _record_status_event(app, previous_stage, stage, app.stage_updated_at, additional_notes)

    if stage == 'Interview':
        app.interview_date = normalized_date
    elif stage == 'Assessment':
        app.assessment_date = normalized_date
    elif stage in ('Not Applied Yet', 'Missed Deadline'):
        app.application_deadline = normalized_date
    elif stage == 'Applied':
        if normalized_date:
            app.applied_date = normalized_date

    if additional_notes:
        sep = "\n\n" if app.notes else ""
        if stage == 'Rejected':
            note_prefix = "Rejection Feedback:"
        elif stage == 'Offer':
            note_prefix = "Offer Details:"
        else:
            note_prefix = "Update:"
        app.notes = f"{app.notes}{sep}{note_prefix} {additional_notes}"

    if is_htmx:
        if not _commit_database_changes():
            return _render_job_application_card(
                app,
                message="The status could not be saved. Please try again.",
                is_error=True,
            )
        return _render_job_application_card(app, message=f"Saved as {stage}.")

    if _commit_or_flash():
        flash(f"Stage updated to '{stage}'.", "success")
    return redirect(url_for("admin.job_tracker"))
