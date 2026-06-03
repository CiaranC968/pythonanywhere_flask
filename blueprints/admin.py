import json
import os
import re
from functools import wraps
from importlib import import_module

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
    session,
    url_for,
)
from werkzeug.utils import secure_filename
from sqlalchemy import func
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash

from extensions import db
from models import Certificate, Education, Experience, Profile, Project, ResumeTemplate, Skill, JobApplication
from portfolio_data import get_portfolio, get_profile

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

IMAGE_FIELDS = {
    "profile_image": {"subdir": "images", "store": "filename"},
    "logo": {"subdir": "images", "store": "filename"},
    "image": {"subdir": "images/projects", "store": "filename"},
    "image_path": {"subdir": "images", "store": "static_url"},
}

ICON_FIELDS = {"hero_icon", "icon", "bgIcon"}
STYLE_FIELDS = {"iconColor", "bgColor", "hoverColor"}
FIELD_GROUPS = {
    "profile": [
        ("Profile", ["full_name", "title", "tagline", "cv_subtitle", "about"]),
        ("Contact",
         ["email", "phone", "address", "linkedin_url", "github_url", "website_url", "location", "availability_text",
          "contact_intro"]),
        ("Media", ["profile_image"]),
        ("Icon", ["hero_icon"]),
    ],
    "experience": [
        ("Core",
         ["id", "company", "role", "period", "brief", "location", "type", "current", "sort_order", "is_visible"]),
        ("Details", ["details", "tech_stack", "timeline", "skills"]),
        ("Media", ["logo"]),
        ("Icon", ["icon", "bgIcon"]),
        ("Colour customisation", ["iconColor", "bgColor", "hoverColor"]),
    ],
    "education": [
        ("Core", ["id", "degree", "university", "year", "description", "current", "status", "progress", "sort_order",
                  "is_visible"]),
        ("Modules & results", ["stages", "total_credits", "gpa", "modules_completed"]),
        ("Media", ["logo"]),
    ],
    "skills": [
        ("Core", ["id", "title", "desc", "tags", "progress", "stats", "sort_order", "is_visible"]),
        ("Icon", ["icon"]),
        ("Colour customisation", ["iconColor", "bgColor"]),
    ],
    "projects": [
        ("Core", ["id", "title", "desc", "status", "tags", "links", "stats", "features", "challenges", "sort_order",
                  "is_visible"]),
        ("Media", ["image"]),
        ("Icon", ["icon"]),
        ("Colour customisation", ["iconColor", "bgColor"]),
    ],
    "certificates": [
        ("Core", ["id", "title", "issuer", "date", "desc", "link", "credential_id", "skills", "verified", "sort_order",
                  "is_visible"]),
        ("Media", ["image_path", "logo"]),
    ],
}

ICON_CHOICES = [
    ("fas fa-terminal", "Terminal"),
    ("fas fa-code", "Code"),
    ("fas fa-laptop-code", "Developer"),
    ("fas fa-folder", "Folder"),
    ("fas fa-bolt", "Energy"),
    ("fas fa-cogs", "Settings"),
    ("fas fa-gamepad", "Game"),
    ("fas fa-cloud", "Cloud"),
    ("fas fa-flask", "Research"),
    ("fas fa-university", "Education"),
    ("fas fa-building", "Company"),
    ("fas fa-briefcase", "Briefcase"),
    ("fas fa-store", "Store"),
    ("fas fa-wine-bottle", "Retail"),
    ("fas fa-award", "Award"),
    ("fas fa-certificate", "Certificate"),
    ("fas fa-calendar", "Calendar"),
    ("fas fa-chart-line", "Growth"),
    ("fas fa-database", "Database"),
    ("fas fa-server", "Server"),
    ("fas fa-shield-alt", "Security"),
    ("fab fa-python", "Python"),
    ("fab fa-java", "Java"),
    ("fab fa-react", "React"),
    ("fab fa-github", "GitHub"),
]

STYLE_CHOICES = {
    "iconColor": [
        ("text-gray-600", "Graphite"),
        ("text-brand-accent", "Accent"),
        ("text-blue-600", "Blue"),
        ("text-indigo-600", "Indigo"),
        ("text-emerald-500", "Emerald"),
        ("text-green-600", "Green"),
        ("text-orange-600", "Orange"),
        ("text-red-600", "Red"),
        ("text-purple-600", "Purple"),
        ("text-rose-500", "Rose"),
    ],
    "bgColor": [
        ("bg-gray-100", "Graphite"),
        ("bg-brand-accent/10", "Accent"),
        ("bg-blue-100", "Blue"),
        ("bg-indigo-100", "Indigo"),
        ("bg-emerald-100", "Emerald"),
        ("bg-green-100", "Green"),
        ("bg-orange-100", "Orange"),
        ("bg-red-100", "Red"),
        ("bg-purple-100", "Purple"),
        ("bg-rose-100", "Rose"),
    ],
    "hoverColor": [
        ("text-gray-900", "Graphite"),
        ("text-brand-accent", "Accent"),
        ("text-blue-600", "Blue"),
        ("text-indigo-600", "Indigo"),
        ("text-emerald-500", "Emerald"),
        ("text-green-600", "Green"),
        ("text-orange-600", "Orange"),
        ("text-red-600", "Red"),
        ("text-purple-600", "Purple"),
        ("text-rose-500", "Rose"),
        ("group-hover:text-yellow-400", "Hover yellow"),
        ("group-hover:text-green-600", "Hover green"),
    ],
}


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
            ("hero_icon", "Hero icon", "text"),
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
            ("icon", "Icon", "text"),
            ("bgIcon", "Background icon", "text"),
            ("iconColor", "Icon colour", "text"),
            ("bgColor", "Background colour", "text"),
            ("hoverColor", "Hover colour", "text"),
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
            ("icon", "Icon", "text"),
            ("iconColor", "Icon colour", "text"),
            ("bgColor", "Background colour", "text"),
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
            ("icon", "Icon", "text"),
            ("iconColor", "Icon colour", "text"),
            ("bgColor", "Background colour", "text"),
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

DOCUMENT_SECTION_CONFIG = [
    {
        "key": "experience",
        "label": "Experience",
        "description": "Roles, promotions, bullet points, and work history.",
    },
    {
        "key": "projects",
        "label": "Projects",
        "description": "Selected portfolio projects and their tags. The PDF prints up to 3.",
        "max_items": 3,
        "overflow_warning": "Project sections are capped at 3 items so the one-page PDF does not overflow.",
    },
    {
        "key": "skills",
        "label": "Skills",
        "description": "Skill groups used to build the CV skill tags.",
    },
    {
        "key": "education",
        "label": "Education",
        "description": "Degrees, modules, stages, and results.",
    },
    {
        "key": "certificates",
        "label": "Certificates",
        "description": "Certificates, issuers, dates, and credentials.",
    },
]

ALLOWED_RESUME_TEMPLATE_TARGETS = {
    "resume_summary": "Introduction",
    "company_details": "What I bring",
    "resume_conclusion": "Conclusion",
}

RESUME_SENTENCE_TEMPLATES = [
    {
        "target": "resume_summary",
        "label": "Software role intro",
        "text": "I am writing to apply for the {role} position at {company}. As a Computing and IT student with hands-on software development experience, I am eager to contribute to your team while continuing to grow as a developer.",
    },
    {
        "target": "resume_summary",
        "label": "Testing focus",
        "text": "I am particularly interested in {company} because the role aligns with my experience in backend development, testing, documentation, and building reliable software with a practical user focus.",
    },
    {
        "target": "resume_summary",
        "label": "Graduate tone",
        "text": "As an Open University Computing and IT student, I bring a mix of academic learning, self-directed project work, and real workplace experience that would let me contribute quickly to {company}.",
    },
    {
        "target": "company_details",
        "label": "Python strength",
        "text": "Proficient in Python, with practical experience using Flask, SQL, APIs, and automation to build maintainable software.",
    },
    {
        "target": "company_details",
        "label": "Frontend/backend",
        "text": "Comfortable working across backend and frontend code, including Flask, FastAPI, React, TypeScript, HTML, CSS, and database-backed applications.",
    },
    {
        "target": "company_details",
        "label": "Agile/testing",
        "text": "Practical understanding of Agile workflows, sprint planning, documentation, integration testing, and collaborating in technical teams.",
    },
    {
        "target": "company_details",
        "label": "Communication",
        "text": "Strong communication and teamwork skills developed through academic group projects, internships, and customer-facing work experience.",
    },
    {
        "target": "company_details",
        "label": "Learning mindset",
        "text": "Quick to learn new tools and frameworks, with a steady approach to debugging, documentation, and improving existing systems.",
    },
    {
        "target": "resume_conclusion",
        "label": "Standard close",
        "text": "Thank you for considering my application. I would welcome the opportunity to discuss how my skills, motivation, and experience could support {company}.\n\nYours sincerely,\n\nCiaran Cairns",
    },
    {
        "target": "resume_conclusion",
        "label": "Engineering close",
        "text": "I would be excited to support your engineering team, learn from experienced developers, and contribute to high-quality, reliable software at {company}.\n\nYours sincerely,\n\nCiaran Cairns",
    },
]

RESUME_ROLE_PRESETS = [
    {
        "label": "Software Developer",
        "header_subtitle": "Software Developer Application",
        "target_role": "Software Developer",
        "resume_keywords": "Python, Flask, SQL, APIs, JavaScript, testing",
        "resume_summary": "I am writing to apply for the {role} position at {company}. I bring practical experience building database-backed web applications, APIs, and automation tools, alongside my BSc Computing and IT studies.",
        "company_details": "Experience building maintainable Flask and Python applications with SQL-backed data.\nComfortable working across frontend and backend code, including HTML, CSS, JavaScript, TypeScript, and REST APIs.\nUsed to debugging issues carefully, documenting decisions, and improving existing systems.",
        "resume_conclusion": "I would welcome the opportunity to discuss how my software development experience, motivation, and practical project work could support {company}.\n\nYours sincerely,\n\nCiaran Cairns",
    },
    {
        "label": "QA / Test Engineer",
        "header_subtitle": "QA / Test Engineer Application",
        "target_role": "QA / Test Engineer",
        "resume_keywords": "Testing, debugging, documentation, APIs, Agile, SQL",
        "resume_summary": "I am writing to apply for the {role} position at {company}. I am interested in quality-focused engineering and bring hands-on experience testing, debugging, documenting, and improving software projects.",
        "company_details": "Practical understanding of integration testing, API validation, edge cases, and clear bug reporting.\nExperience working with Python, Flask, SQL, Git, and Agile-style project delivery.\nStrong attention to detail from combining academic projects with real workplace software tasks.",
        "resume_conclusion": "I would be excited to help {company} deliver reliable, well-tested software while continuing to grow my engineering skills.\n\nYours sincerely,\n\nCiaran Cairns",
    },
    {
        "label": "Backend Developer",
        "header_subtitle": "Backend Developer Application",
        "target_role": "Backend Developer",
        "resume_keywords": "Python, Flask, FastAPI, MySQL, REST APIs, Docker",
        "resume_summary": "I am writing to apply for the {role} position at {company}. My strongest experience is in backend development, including Python services, Flask applications, SQL databases, and API-driven workflows.",
        "company_details": "Built and maintained backend features using Python, Flask, MySQL, and structured data models.\nComfortable designing practical APIs, handling validation, and connecting frontend workflows to database-backed systems.\nInterested in writing clear, maintainable code that is easy to support and extend.",
        "resume_conclusion": "I would welcome the opportunity to bring my backend development experience and steady problem-solving approach to {company}.\n\nYours sincerely,\n\nCiaran Cairns",
    },
    {
        "label": "Placement / Internship",
        "header_subtitle": "Placement / Internship Application",
        "target_role": "Placement Software Developer",
        "resume_keywords": "Learning mindset, Python, teamwork, Agile, documentation",
        "resume_summary": "I am writing to apply for the {role} opportunity at {company}. As a Stage 2 BSc Computing and IT student, I am keen to apply my software development skills in a professional team and learn from experienced engineers.",
        "company_details": "Strong foundation in programming, databases, web development, and software engineering principles.\nPractical project experience using Python, Flask, Java, TypeScript, Git, and documentation-led development.\nMotivated, reliable, and quick to learn new tools, with a collaborative approach to team work.",
        "resume_conclusion": "Thank you for considering my application. I would be grateful for the chance to discuss how I could contribute to {company} during a placement or internship.\n\nYours sincerely,\n\nCiaran Cairns",
    },
]

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
            if config.get("singleton"):
                counts[section] = 1
            else:
                query = model.query
                if hasattr(model, "is_visible"):
                    query = query.filter_by(is_visible=True)
                counts[section] = query.count()
        counts["job_applications"] = JobApplication.query.count()
    except SQLAlchemyError as exc:
        database_error = str(exc)
        counts = {section: 0 for section in SECTIONS}
        counts["job_applications"] = 0

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
        db.session.execute(text("SELECT 1"))
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
        db.session.execute(text("SELECT 1"))
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

    portfolio = get_portfolio()
    include_sections = request.form.getlist("sections")
    selected_portfolio = _selected_document_portfolio(portfolio, include_sections)
    resume_options = _cv_options()

    has_selected_content = any(selected_portfolio.get(section) for section in include_sections)
    if not include_sections or not has_selected_content:
        flash("Choose at least one section and one item before generating the PDF.", "error")
        return redirect(url_for("admin.cv_builder"))

    try:
        pdf_bytes = build_cv_pdf(
            profile=get_profile(),
            portfolio=selected_portfolio,
            include_sections=include_sections,
            resume_options=resume_options,
        )
    except ImportError:
        flash("Install reportlab and Pillow from requirements.txt before generating PDFs.", "error")
        return redirect(url_for("admin.cv_builder"))

    profile = get_profile()
    filename = _document_filename(profile.full_name, "cv", resume_options, _safe_filename)
    return _pdf_response(pdf_bytes, filename)


@admin_bp.route("/resume-builder")
@admin_required
def resume_builder():
    return render_template(
        "admin/resume_builder.html",
        profile=get_profile(),
        sentence_templates=_resume_sentence_templates(),
        custom_sentence_templates=_custom_resume_templates(include_hidden=True),
        role_presets=RESUME_ROLE_PRESETS,
        template_targets=ALLOWED_RESUME_TEMPLATE_TARGETS,
    )


@admin_bp.route("/resume-builder/templates", methods=["POST"])
@admin_required
def add_resume_template():
    target = request.form.get("template_target", "").strip()
    label = request.form.get("template_label", "").strip()
    text_value = request.form.get("template_text", "").strip()

    if target not in ALLOWED_RESUME_TEMPLATE_TARGETS or not label or not text_value:
        flash("Choose a section, label, and sentence before saving a template.", "error")
        return redirect(url_for("admin.resume_builder"))

    max_order = db.session.query(func.max(ResumeTemplate.sort_order)).scalar()
    template = ResumeTemplate()
    template.target = target
    template.label = label
    template.text = text_value
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

    target = request.form.get("template_target", "").strip()
    label = request.form.get("template_label", "").strip()
    text_value = request.form.get("template_text", "").strip()
    if target not in ALLOWED_RESUME_TEMPLATE_TARGETS or not label or not text_value:
        flash("Choose a section, label, and sentence before saving the template.", "error")
        return redirect(url_for("admin.resume_builder"))

    template.target = target
    template.label = label
    template.text = text_value
    template.sort_order = _form_integer("sort_order", template.sort_order)
    if _commit_or_flash():
        flash("Template sentence saved.", "success")
    return redirect(url_for("admin.resume_builder"))


@admin_bp.route("/resume-builder/templates/<int:template_id>/delete", methods=["POST"])
@admin_required
def delete_resume_template(template_id: int):
    template = db.session.get(ResumeTemplate, template_id)
    if not template:
        abort(404)

    template.is_visible = False
    if _commit_or_flash():
        flash("Template sentence archived.", "success")
    return redirect(url_for("admin.resume_builder"))


@admin_bp.route("/resume-builder/templates/<int:template_id>/restore", methods=["POST"])
@admin_required
def restore_resume_template(template_id: int):
    template = db.session.get(ResumeTemplate, template_id)
    if not template:
        abort(404)

    template.is_visible = True
    if _commit_or_flash():
        flash("Template sentence restored.", "success")
    return redirect(url_for("admin.resume_builder"))


@admin_bp.route("/resume-builder/pdf", methods=["POST"])
@admin_required
def resume_builder_pdf():
    from blueprints.cv import build_resume_letter_pdf, _safe_filename

    resume_options = _resume_options()
    try:
        pdf_bytes = build_resume_letter_pdf(profile=get_profile(), resume_options=resume_options)
    except ImportError:
        flash("Install reportlab and Pillow from requirements.txt before generating PDFs.", "error")
        return redirect(url_for("admin.resume_builder"))

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
        return jsonify({"ok": False, "error": str(exc)}), 500

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

    return render_template(
        "admin/form.html",
        section=section,
        config=config,
        item=item,
        action="Create",
        **_form_context(section),
    )


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

    return render_template(
        "admin/form.html",
        section=section,
        config=config,
        item=item,
        action="Save",
        **_form_context(section),
    )


@admin_bp.route("/<section>/<item_id>/delete", methods=["POST"])
@admin_required
def delete_item(section: str, item_id: str):
    config = _section_config(section)
    if config.get("singleton"):
        abort(404)

    item = db.session.get(config["model"], _identity_for_section(section, item_id))
    if not item:
        abort(404)

    if hasattr(item, "is_visible"):
        item.is_visible = False
    else:
        db.session.delete(item)
    if not _commit_or_flash():
        return redirect(url_for("admin.list_items", section=section))
    flash(f"{config['label']} item archived.", "success")
    return redirect(url_for("admin.list_items", section=section))


@admin_bp.route("/<section>/<item_id>/restore", methods=["POST"])
@admin_required
def restore_item(section: str, item_id: str):
    config = _section_config(section)
    if config.get("singleton"):
        abort(404)

    item = db.session.get(config["model"], _identity_for_section(section, item_id))
    if not item:
        abort(404)

    if not hasattr(item, "is_visible"):
        abort(404)

    item.is_visible = True
    if not _commit_or_flash():
        return redirect(url_for("admin.list_items", section=section))
    flash(f"{config['label']} item restored.", "success")
    return redirect(url_for("admin.list_items", section=section))


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

    def replace_tags(text):
        if not text:
            return text

        c_val = company_name if company_name else "your organisation"
        r_val = target_role if target_role else "the advertised role"

        text = re.sub(r'\{company\}', c_val, text, flags=re.IGNORECASE)
        text = re.sub(r'\{role\}', r_val, text, flags=re.IGNORECASE)
        return text

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


@admin_bp.route("/job-tracker")
@admin_required
def job_tracker():
    from datetime import datetime
    today_str = datetime.today().strftime("%Y-%m-%d")
    today_now = datetime.today()

    # Dynamic check of missed deadlines
    modified = False
    all_apps = JobApplication.query.all()
    for app in all_apps:
        if app.stage == 'Not Applied Yet' and app.application_deadline:
            try:
                dl_str = app.application_deadline.strip()
                if 'T' in dl_str:
                    dl_dt = datetime.strptime(dl_str, "%Y-%m-%dT%H:%M")
                elif ' ' in dl_str:
                    dl_dt = datetime.strptime(dl_str, "%Y-%m-%d %H:%M")
                else:
                    dl_dt = datetime.strptime(dl_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

                if today_now > dl_dt:
                    app.stage = 'Missed Deadline'
                    modified = True
            except ValueError:
                date_part = app.application_deadline.split('T')[0].split(' ')[0]
                if today_str > date_part:
                    app.stage = 'Missed Deadline'
                    modified = True

    if modified:
        db.session.commit()

    applications = JobApplication.query.order_by(JobApplication.id.desc()).all()
    return render_template(
        "admin/job_tracker.html",
        applications=applications,
        today=today_str,
    )


@admin_bp.route("/job-tracker/add", methods=["POST"])
@admin_required
def add_job_application():
    from datetime import datetime
    company = request.form.get("company", "").strip()
    role = request.form.get("role", "").strip()
    stage = request.form.get("stage", "Applied").strip()
    applied_date = request.form.get("applied_date", "").strip()
    interview_date = request.form.get("interview_date", "").strip()
    application_deadline = request.form.get("application_deadline", "").strip()
    notes = request.form.get("notes", "").strip()

    if not company or not role:
        flash("Company and Role are required.", "error")
        return redirect(url_for("admin.job_tracker"))

    if not applied_date:
        applied_date = datetime.today().strftime("%Y-%m-%d")

    app = JobApplication(
        company=company,
        role=role,
        stage=stage,
        applied_date=applied_date,
        interview_date=interview_date if interview_date else None,
        application_deadline=application_deadline if application_deadline else None,
        notes=notes,
    )
    db.session.add(app)
    if _commit_or_flash():
        flash("Job application added successfully.", "success")
    return redirect(url_for("admin.job_tracker"))


@admin_bp.route("/job-tracker/<int:app_id>/edit", methods=["POST"])
@admin_required
def edit_job_application(app_id: int):
    app = db.session.get(JobApplication, app_id)
    if not app:
        abort(404)

    company = request.form.get("company", "").strip()
    role = request.form.get("role", "").strip()
    stage = request.form.get("stage", "Applied").strip()
    applied_date = request.form.get("applied_date", "").strip()
    interview_date = request.form.get("interview_date", "").strip()
    application_deadline = request.form.get("application_deadline", "").strip()
    notes = request.form.get("notes", "").strip()

    if not company or not role:
        flash("Company and Role are required.", "error")
        return redirect(url_for("admin.job_tracker"))

    app.company = company
    app.role = role
    app.stage = stage
    app.applied_date = applied_date
    app.interview_date = interview_date if interview_date else None
    app.application_deadline = application_deadline if application_deadline else None
    app.notes = notes

    if _commit_or_flash():
        flash("Job application updated successfully.", "success")
    return redirect(url_for("admin.job_tracker"))


@admin_bp.route("/job-tracker/<int:app_id>/delete", methods=["POST"])
@admin_required
def delete_job_application(app_id: int):
    app = db.session.get(JobApplication, app_id)
    if not app:
        abort(404)

    db.session.delete(app)
    if _commit_or_flash():
        flash("Job application deleted.", "success")
    return redirect(url_for("admin.job_tracker"))


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

        # Parse bullets
        details = [line.strip() for line in details_raw.split("\n") if line.strip()]

        # Parse tech stack
        tech_stack = [tech.strip() for tech in tech_stack_raw.split(",") if tech.strip()]

        # Apply defaults for layout/colors
        exp = Experience(
            company=company,
            role=role,
            period=period,
            brief=brief,
            details=details,
            tech_stack=tech_stack,
            location=location,
            type=work_type,
            icon="fas fa-briefcase",
            bgIcon="fas fa-building",
            iconColor="text-yellow-600",
            bgColor="bg-yellow-50",
            hoverColor="text-yellow-900",
            current=False,
            is_visible=True
        )

        # Sort order
        max_order = db.session.query(func.max(Experience.sort_order)).scalar()
        exp.sort_order = (max_order or 0) + 10

        # Unique slug
        exp.id = _unique_slug(Experience, company)

        db.session.add(exp)
        db.session.commit()
        flash("Job Experience added successfully!", "success")

    elif section == "skills":
        title = request.form.get("title", "").strip()
        desc = request.form.get("desc", "").strip()
        tags_raw = request.form.get("tags", "").strip()
        progress_val = request.form.get("progress_val", "85").strip()
        theme = request.form.get("theme", "yellow").strip()

        if not title:
            flash("Skill Title is required.", "error")
            return redirect(url_for("admin.dashboard"))

        # Parse tags
        tags = [tag.strip() for tag in tags_raw.split(",") if tag.strip()]

        # Map theme colors
        themes = {
            "yellow": ("text-yellow-600", "bg-yellow-50", "fas fa-code"),
            "blue": ("text-blue-600", "bg-blue-50", "fas fa-laptop-code"),
            "indigo": ("text-indigo-600", "bg-indigo-50", "fas fa-terminal"),
            "green": ("text-green-600", "bg-green-50", "fas fa-cogs"),
            "red": ("text-red-600", "bg-red-50", "fas fa-bolt")
        }
        icon_color, bg_color, default_icon = themes.get(theme, themes["yellow"])

        # Parse progress
        try:
            val = int(progress_val)
        except ValueError:
            val = 85

        progress = {
            "label": "Experience",
            "value": val,
            "unit": "%",
            "max": 100
        }

        sk = Skill(
            title=title,
            desc=desc,
            icon=default_icon,
            iconColor=icon_color,
            bgColor=bg_color,
            tags=tags,
            progress=progress,
            stats=[],
            is_visible=True
        )

        # Sort order
        max_order = db.session.query(func.max(Skill.sort_order)).scalar()
        sk.sort_order = (max_order or 0) + 10

        # Unique slug
        sk.id = _unique_slug(Skill, title)

        db.session.add(sk)
        db.session.commit()
        flash("Skill added successfully!", "success")

    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/job-tracker/<int:app_id>/update-stage-ajax", methods=["POST"])
@admin_required
def update_job_stage_ajax(app_id: int):
    app = db.session.get(JobApplication, app_id)
    if not app:
        abort(404)

    stage = request.form.get("stage", "").strip()
    additional_notes = request.form.get("additional_notes", "").strip()
    date_val = request.form.get("date_val", "").strip()

    if stage:
        app.stage = stage

    # Normalization of date (handling UK format DD/MM/YYYY [HH:MM])
    normalized_date = None
    if date_val:
        if "/" in date_val:
            try:
                if " " in date_val:
                    d_part, t_part = date_val.split(" ", 1)
                    day, month, year = d_part.split("/")
                    # Validate time part
                    if ":" in t_part:
                        normalized_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}T{t_part}"
                    else:
                        normalized_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}T{t_part}:00"
                else:
                    day, month, year = date_val.split("/")
                    normalized_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except Exception:
                normalized_date = date_val
        else:
            normalized_date = date_val.replace(" ", "T")

    if stage == 'Interview':
        app.interview_date = normalized_date
    elif stage == 'Assessment':
        app.interview_date = normalized_date
    elif stage in ('Not Applied Yet', 'Missed Deadline'):
        app.application_deadline = normalized_date

    if additional_notes:
        sep = "\n\n" if app.notes else ""
        note_prefix = "Rejection Feedback:" if stage == 'Rejected' else "Offer Details:"
        app.notes = f"{app.notes}{sep}{note_prefix} {additional_notes}"

    db.session.commit()
    flash(f"Stage updated to '{stage}'.", "success")
    return redirect(url_for("admin.job_tracker"))



