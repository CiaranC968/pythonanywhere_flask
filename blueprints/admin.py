import json
import re
from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash

from extensions import db
from models import Certificate, Education, Experience, Profile, Project, Skill

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.after_request
def noindex_admin(response):
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


SECTIONS = {
    "profile": {
        "label": "Profile",
        "description": "Name, title, contact details, hero copy, and CV header.",
        "model": Profile,
        "singleton": True,
        "fields": [
            ("full_name", "Name", "text"),
            ("title", "Title", "text"),
            ("tagline", "Hero badge", "text"),
            ("cv_subtitle", "CV subtitle", "text"),
            ("about", "About text", "textarea"),
            ("email", "Email", "text"),
            ("phone", "Phone", "text"),
            ("address", "Address", "text"),
            ("linkedin_url", "LinkedIn URL", "text"),
            ("github_url", "GitHub URL", "text"),
            ("website_url", "Website URL", "text"),
            ("location", "Location", "text"),
            ("availability_text", "Contact badge", "text"),
            ("contact_intro", "Contact intro", "textarea"),
            ("profile_image", "Profile image filename", "text"),
            ("hero_icon", "Hero icon CSS class", "text"),
        ],
        "title_field": "full_name",
    },
    "experience": {
        "label": "Experience",
        "description": "Companies, roles, job history, timeline entries, bullets, and tech stack.",
        "model": Experience,
        "fields": [
            ("id", "Slug ID", "text"),
            ("company", "Company", "text"),
            ("role", "Role", "text"),
            ("period", "Period", "text"),
            ("brief", "Brief", "textarea"),
            ("details", "Bullet points", "json"),
            ("tech_stack", "Tech stack", "json"),
            ("timeline", "Job timeline / promotions", "json"),
            ("skills", "Skills", "json"),
            ("logo", "Logo filename", "text"),
            ("location", "Location", "text"),
            ("type", "Work type", "text"),
            ("icon", "Icon CSS class", "text"),
            ("bgIcon", "Background icon CSS class", "text"),
            ("iconColor", "Icon colour class", "text"),
            ("bgColor", "Background colour class", "text"),
            ("hoverColor", "Hover colour class", "text"),
            ("current", "Current role", "checkbox"),
            ("sort_order", "Sort order", "integer"),
            ("is_visible", "Visible", "checkbox"),
        ],
        "title_field": "company",
    },
    "education": {
        "label": "Education",
        "description": "Degrees, colleges, modules, stages, progress, and results.",
        "model": Education,
        "fields": [
            ("id", "Slug ID", "text"),
            ("degree", "Degree", "text"),
            ("university", "University", "text"),
            ("year", "Year", "text"),
            ("logo", "Logo filename", "text"),
            ("description", "Description", "textarea"),
            ("stages", "Stages and modules", "json"),
            ("progress", "Progress percentage", "integer"),
            ("current", "Current", "checkbox"),
            ("status", "Status", "text"),
            ("total_credits", "Total credits", "integer"),
            ("gpa", "GPA / result", "text"),
            ("modules_completed", "Modules completed", "integer"),
            ("sort_order", "Sort order", "integer"),
            ("is_visible", "Visible", "checkbox"),
        ],
        "title_field": "degree",
    },
    "skills": {
        "label": "Skills",
        "description": "Skill groups, tags, progress bars, and card stats.",
        "model": Skill,
        "fields": [
            ("id", "Slug ID", "text"),
            ("title", "Title", "text"),
            ("desc", "Description", "textarea"),
            ("icon", "Icon CSS class", "text"),
            ("iconColor", "Icon colour class", "text"),
            ("bgColor", "Background colour class", "text"),
            ("tags", "Tags", "json"),
            ("progress", "Progress", "json"),
            ("stats", "Stats", "json"),
            ("sort_order", "Sort order", "integer"),
            ("is_visible", "Visible", "checkbox"),
        ],
        "title_field": "title",
    },
    "projects": {
        "label": "Projects",
        "description": "Portfolio projects, links, screenshots, status, features, and tags.",
        "model": Project,
        "fields": [
            ("id", "Slug ID", "text"),
            ("title", "Title", "text"),
            ("desc", "Description", "textarea"),
            ("status", "Status", "text"),
            ("icon", "Icon CSS class", "text"),
            ("iconColor", "Icon colour class", "text"),
            ("bgColor", "Background colour class", "text"),
            ("tags", "Tags", "json"),
            ("links", "Links", "json"),
            ("stats", "Stats", "json"),
            ("features", "Features", "json"),
            ("challenges", "Challenges", "textarea"),
            ("image", "Image filename", "text"),
            ("sort_order", "Sort order", "integer"),
            ("is_visible", "Visible", "checkbox"),
        ],
        "title_field": "title",
    },
    "certificates": {
        "label": "Certificates",
        "description": "Certificates, issuers, dates, credential links, and related skills.",
        "model": Certificate,
        "fields": [
            ("id", "Slug ID", "text"),
            ("title", "Title", "text"),
            ("issuer", "Issuer", "text"),
            ("date", "Date", "text"),
            ("desc", "Description", "textarea"),
            ("image_path", "Image URL/path", "text"),
            ("logo", "Logo filename", "text"),
            ("link", "Credential link", "text"),
            ("credential_id", "Credential ID", "text"),
            ("skills", "Skills", "json"),
            ("verified", "Verified", "checkbox"),
            ("sort_order", "Sort order", "integer"),
            ("is_visible", "Visible", "checkbox"),
        ],
        "title_field": "title",
    },
}

FIELD_HELP = {
    "id": "Leave blank when creating a new item and a slug will be generated automatically.",
    "sort_order": "Lower numbers appear first. Leave blank to place new items at the end.",
    "is_visible": "Untick to hide this item from the public site and PDF without deleting it.",
    "details": "Bullet points for a single job/role.",
    "timeline": "Use this when one company has multiple jobs or promotions.",
    "stages": "Education stages with module lists.",
    "links": "Buttons shown on project cards and modals.",
    "tags": "Short labels such as languages, tools, or topics.",
    "skills": "Short labels used on certificate and experience cards.",
    "stats": "Small facts shown on cards, such as year or project count.",
    "progress": "Optional progress object used by skill and education cards.",
}

JSON_EXAMPLES = {
    "details": [
        "Built a Flask admin tool backed by MySQL.",
        "Improved page speed and accessibility across the portfolio.",
    ],
    "tech_stack": ["Python", "Flask", "MySQL", "HTMX"],
    "timeline": [
        {
            "role": "Software Developer",
            "period": "Jan 2026 - Present",
            "loc": "Remote",
            "desc": "Building production Flask features and maintaining database-backed content.",
        }
    ],
    "skills": ["Python", "Flask", "MySQL"],
    "tags": ["Python", "Flask", "MySQL"],
    "links": [
        {
            "icon": "fab fa-github",
            "url": "https://github.com/username/project",
            "label": "GitHub",
        }
    ],
    "stats": [{"icon": "fas fa-calendar", "value": "2026", "label": "Year"}],
    "features": ["Login-protected admin", "Generated one-page PDF CV"],
    "progress": {"label": "Experience", "value": 3, "unit": "years", "max": 5},
    "stages": {
        "Stage 1": [
            {"code": "TM111", "title": "Introduction to Computing and IT Part 1"}
        ]
    },
}

JSON_EDITOR_KINDS = {
    "details": "list",
    "tech_stack": "list",
    "skills": "list",
    "tags": "list",
    "features": "list",
    "links": "links",
    "stats": "stats",
    "timeline": "timeline",
    "stages": "stages",
    "progress": "progress",
}


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin.login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped


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
            return redirect(request.args.get("next") or url_for("admin.dashboard"))

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
            counts[section] = 1 if config.get("singleton") else model.query.count()
    except Exception as exc:
        database_error = str(exc)
        counts = {section: 0 for section in SECTIONS}

    admin_password_missing = not current_app.config.get("ADMIN_PASSWORD_HASH") and not current_app.config.get("ADMIN_PASSWORD")
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
        db.session.execute(text("SELECT 1"))
        table_names = sqlalchemy_inspect(db.engine).get_table_names()
    except Exception as exc:
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


@admin_bp.route("/<section>")
@admin_required
def list_items(section):
    config = _section_config(section)
    if config.get("singleton"):
        return redirect(url_for("admin.edit_item", section=section, item_id=1))

    model = config["model"]
    items = model.query.order_by(model.sort_order.asc(), model.id.asc()).all()
    return render_template("admin/list.html", section=section, config=config, items=items)


@admin_bp.route("/<section>/new", methods=["GET", "POST"])
@admin_required
def new_item(section):
    config = _section_config(section)
    if config.get("singleton"):
        abort(404)

    item = config["model"]()
    _apply_new_defaults(item, section, config)
    if request.method == "POST":
        if _populate_item(item, config, is_new=True):
            db.session.add(item)
            if _commit_or_flash():
                flash(f"{config['label']} item created.", "success")
                return redirect(url_for("admin.list_items", section=section))

    return render_template(
        "admin/form.html",
        section=section,
        config=config,
        item=item,
        action="Create",
        field_help=FIELD_HELP,
        json_examples=JSON_EXAMPLES,
        json_editor_kinds=JSON_EDITOR_KINDS,
    )


@admin_bp.route("/<section>/<item_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_item(section, item_id):
    config = _section_config(section)
    item = db.session.get(config["model"], int(item_id) if section == "profile" else item_id)
    if not item and config.get("singleton"):
        item = Profile(id=1)
        db.session.add(item)
        db.session.commit()
    if not item:
        abort(404)

    if request.method == "POST":
        if _populate_item(item, config, is_new=False):
            if _commit_or_flash():
                flash(f"{config['label']} item saved.", "success")
                return redirect(url_for("admin.dashboard" if config.get("singleton") else "admin.list_items", section=section))

    return render_template(
        "admin/form.html",
        section=section,
        config=config,
        item=item,
        action="Save",
        field_help=FIELD_HELP,
        json_examples=JSON_EXAMPLES,
        json_editor_kinds=JSON_EDITOR_KINDS,
    )


@admin_bp.route("/<section>/<item_id>/delete", methods=["POST"])
@admin_required
def delete_item(section, item_id):
    config = _section_config(section)
    if config.get("singleton"):
        abort(404)

    item = db.session.get(config["model"], item_id)
    if not item:
        abort(404)

    db.session.delete(item)
    if not _commit_or_flash():
        return redirect(url_for("admin.list_items", section=section))
    flash(f"{config['label']} item deleted.", "success")
    return redirect(url_for("admin.list_items", section=section))


def _section_config(section):
    if section not in SECTIONS:
        abort(404)
    return SECTIONS[section]


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
            else:
                value = request.form.get(name, "").strip()

            setattr(item, name, value)

        if is_new and hasattr(item, "id") and not item.id:
            item.id = _unique_slug(config["model"], _title_for_slug(item, config))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        flash(f"Could not save: {exc}", "error")
        return False

    return True


def _json_default(field_name):
    if field_name in {"stages", "progress"}:
        return {}
    return []


def _integer_default(field_name):
    return 0 if field_name == "sort_order" else None


def _apply_new_defaults(item, section, config):
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


def _commit_or_flash():
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        flash(f"Database error: {exc}", "error")
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
