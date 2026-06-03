import os
import secrets
from datetime import datetime
from types import SimpleNamespace
from urllib.parse import quote, quote_plus

from flask import Flask, render_template, request
from sqlalchemy import inspect, text

# Import Blueprints
from blueprints.admin import admin_bp
from blueprints.main import main_bp
from blueprints.fragments import fragments_bp
from blueprints.contact import contact_bp
from blueprints.cv import cv_bp

from extensions import db
from portfolio_data import get_portfolio, get_profile, seed_database_from_json


def load_dotenv(path=None):
    """Tiny .env loader for local dev and simple PythonAnywhere deployments."""
    path = path or os.environ.get("ENV_FILE")
    if not path:
        path = ".env" if os.path.exists(".env") else "/home/ciaranc88/mysite/.env"
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip("\"'")


def ensure_schema():
    """Small first-party schema patcher for simple PythonAnywhere deployments."""
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    dialect = db.engine.dialect.name
    quote = db.engine.dialect.identifier_preparer.quote

    boolean = "TINYINT(1)" if dialect.startswith("mysql") else "BOOLEAN"
    json_type = "JSON" if dialect.startswith("mysql") else "JSON"
    schema_additions = {
        "profile": {
            "full_name": "VARCHAR(120) NOT NULL DEFAULT 'Your Name'",
            "title": "VARCHAR(160) NOT NULL DEFAULT 'Software Developer'",
            "tagline": "VARCHAR(255) NOT NULL DEFAULT 'Available for Work'",
            "cv_subtitle": "VARCHAR(180) NOT NULL DEFAULT ''",
            "about": "TEXT NULL",
            "email": "VARCHAR(255) NOT NULL DEFAULT ''",
            "phone": "VARCHAR(80) NOT NULL DEFAULT ''",
            "address": "VARCHAR(255) NOT NULL DEFAULT ''",
            "linkedin_url": "VARCHAR(500) NOT NULL DEFAULT ''",
            "github_url": "VARCHAR(500) NOT NULL DEFAULT ''",
            "website_url": "VARCHAR(500) NOT NULL DEFAULT ''",
            "location": "VARCHAR(160) NOT NULL DEFAULT ''",
            "availability_text": "VARCHAR(160) NOT NULL DEFAULT 'Available for new projects'",
            "contact_intro": "TEXT NULL",
            "profile_image": "VARCHAR(255) NOT NULL DEFAULT 'about.png'",
            "hero_icon": "VARCHAR(120) NOT NULL DEFAULT 'fas fa-terminal'",
        },
        "project": {
            "title": "VARCHAR(180) NOT NULL DEFAULT ''",
            "desc": "TEXT NULL",
            "status": "VARCHAR(80) NOT NULL DEFAULT 'Completed'",
            "icon": "VARCHAR(120) NOT NULL DEFAULT 'fas fa-folder'",
            "iconColor": "VARCHAR(120) NOT NULL DEFAULT 'text-gray-600'",
            "bgColor": "VARCHAR(120) NOT NULL DEFAULT 'bg-gray-100'",
            "tags": f"{json_type} NULL",
            "links": f"{json_type} NULL",
            "stats": f"{json_type} NULL",
            "features": f"{json_type} NULL",
            "challenges": "TEXT NULL",
            "image": "VARCHAR(255) NOT NULL DEFAULT ''",
            "sort_order": "INTEGER NOT NULL DEFAULT 0",
            "is_visible": f"{boolean} NOT NULL DEFAULT 1",
        },
        "skill": {
            "title": "VARCHAR(180) NOT NULL DEFAULT ''",
            "desc": "TEXT NULL",
            "icon": "VARCHAR(120) NOT NULL DEFAULT 'fas fa-code'",
            "iconColor": "VARCHAR(120) NOT NULL DEFAULT 'text-gray-600'",
            "bgColor": "VARCHAR(120) NOT NULL DEFAULT 'bg-gray-100'",
            "tags": f"{json_type} NULL",
            "progress": f"{json_type} NULL",
            "stats": f"{json_type} NULL",
            "sort_order": "INTEGER NOT NULL DEFAULT 0",
            "is_visible": f"{boolean} NOT NULL DEFAULT 1",
        },
        "experience": {
            "company": "VARCHAR(180) NOT NULL DEFAULT ''",
            "role": "VARCHAR(180) NOT NULL DEFAULT ''",
            "period": "VARCHAR(120) NOT NULL DEFAULT ''",
            "brief": "TEXT NULL",
            "details": f"{json_type} NULL",
            "tech_stack": f"{json_type} NULL",
            "timeline": f"{json_type} NULL",
            "skills": f"{json_type} NULL",
            "logo": "VARCHAR(255) NOT NULL DEFAULT ''",
            "location": "VARCHAR(180) NOT NULL DEFAULT ''",
            "type": "VARCHAR(120) NOT NULL DEFAULT ''",
            "icon": "VARCHAR(120) NOT NULL DEFAULT 'fas fa-building'",
            "bgIcon": "VARCHAR(120) NOT NULL DEFAULT 'fas fa-briefcase'",
            "iconColor": "VARCHAR(120) NOT NULL DEFAULT 'text-gray-600'",
            "bgColor": "VARCHAR(120) NOT NULL DEFAULT 'bg-gray-100'",
            "hoverColor": "VARCHAR(120) NOT NULL DEFAULT 'text-gray-900'",
            "current": f"{boolean} NOT NULL DEFAULT 0",
            "sort_order": "INTEGER NOT NULL DEFAULT 0",
            "is_visible": f"{boolean} NOT NULL DEFAULT 1",
        },
        "education": {
            "degree": "VARCHAR(220) NOT NULL DEFAULT ''",
            "university": "VARCHAR(220) NOT NULL DEFAULT ''",
            "year": "VARCHAR(120) NOT NULL DEFAULT ''",
            "logo": "VARCHAR(255) NOT NULL DEFAULT ''",
            "description": "TEXT NULL",
            "stages": f"{json_type} NULL",
            "progress": "INTEGER NULL",
            "current": f"{boolean} NOT NULL DEFAULT 0",
            "status": "VARCHAR(120) NOT NULL DEFAULT ''",
            "total_credits": "INTEGER NULL",
            "gpa": "VARCHAR(40) NOT NULL DEFAULT ''",
            "modules_completed": "INTEGER NULL",
            "sort_order": "INTEGER NOT NULL DEFAULT 0",
            "is_visible": f"{boolean} NOT NULL DEFAULT 1",
        },
        "certificate": {
            "title": "VARCHAR(220) NOT NULL DEFAULT ''",
            "issuer": "VARCHAR(220) NOT NULL DEFAULT ''",
            "date": "VARCHAR(120) NOT NULL DEFAULT ''",
            "desc": "TEXT NULL",
            "image_path": "VARCHAR(500) NOT NULL DEFAULT ''",
            "logo": "VARCHAR(255) NOT NULL DEFAULT ''",
            "link": "VARCHAR(500) NOT NULL DEFAULT '#'",
            "credential_id": "VARCHAR(180) NOT NULL DEFAULT ''",
            "skills": f"{json_type} NULL",
            "verified": f"{boolean} NOT NULL DEFAULT 0",
            "sort_order": "INTEGER NOT NULL DEFAULT 0",
            "is_visible": f"{boolean} NOT NULL DEFAULT 1",
        },
        "job_application": {
            "company": "VARCHAR(180) NOT NULL DEFAULT ''",
            "role": "VARCHAR(180) NOT NULL DEFAULT ''",
            "stage": "VARCHAR(80) NOT NULL DEFAULT 'Applied'",
            "applied_date": "VARCHAR(80) NOT NULL DEFAULT ''",
            "interview_date": "VARCHAR(80) NULL",
            "application_deadline": "VARCHAR(80) NULL",
            "notes": "TEXT NULL",
            "job_url": "VARCHAR(500) NULL",
            "company_url": "VARCHAR(500) NULL",
            "company_address": "VARCHAR(500) NULL",
            "linkedin_url": "VARCHAR(500) NULL",
            "salary": "VARCHAR(120) NULL",
            "location": "VARCHAR(180) NULL",
        },
    }

    for table, additions in schema_additions.items():
        if table not in existing_tables:
            continue

        existing = {column["name"] for column in inspector.get_columns(table)}
        for column, definition in additions.items():
            if column not in existing:
                db.session.execute(
                    text(f"ALTER TABLE {quote(table)} ADD COLUMN {quote(column)} {definition}")
                )

    _backfill_schema_defaults(quote)
    db.session.commit()


def _backfill_schema_defaults(quote):
    defaults = {
        "profile": {
            "about": "",
            "contact_intro": "",
        },
        "project": {
            "desc": "",
            "tags": "[]",
            "links": "[]",
            "stats": "[]",
            "features": "[]",
            "challenges": "",
        },
        "skill": {
            "desc": "",
            "tags": "[]",
            "stats": "[]",
        },
        "experience": {
            "brief": "",
            "details": "[]",
            "tech_stack": "[]",
            "timeline": "[]",
            "skills": "[]",
        },
        "education": {
            "description": "",
            "stages": "{}",
        },
        "certificate": {
            "desc": "",
            "skills": "[]",
        },
    }

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    for table, columns in defaults.items():
        if table not in existing_tables:
            continue

        existing_columns = {column["name"] for column in inspector.get_columns(table)}
        for column, value in columns.items():
            if column not in existing_columns:
                continue
            db.session.execute(
                text(
                    f"UPDATE {quote(table)} "
                    f"SET {quote(column)} = :value "
                    f"WHERE {quote(column)} IS NULL"
                ),
                {"value": value},
            )


def build_database_url():
    database_url = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
    if database_url:
        return _normalise_database_url(database_url)

    mysql_user = os.environ.get("MYSQL_USER") or os.environ.get("PA_MYSQL_USER")
    mysql_password = os.environ.get("MYSQL_PASSWORD") or os.environ.get("PA_MYSQL_PASSWORD")
    mysql_host = os.environ.get("MYSQL_HOST") or os.environ.get("PA_MYSQL_HOST")
    mysql_database = os.environ.get("MYSQL_DATABASE") or os.environ.get("PA_MYSQL_DATABASE")

    if all([mysql_user, mysql_password, mysql_host, mysql_database]):
        if ":" in mysql_host:
            host, port = mysql_host.rsplit(":", 1)
            host_part = f"{host}:{port}"
        else:
            host_part = mysql_host

        return (
            "mysql+pymysql://"
            f"{quote_plus(mysql_user)}:{quote_plus(mysql_password)}"
            f"@{host_part}/{quote(mysql_database, safe='$')}?charset=utf8mb4"
        )

    return "sqlite:///portfolio.db"


def _normalise_database_url(database_url):
    if database_url.startswith("mysql://"):
        return database_url.replace("mysql://", "mysql+pymysql://", 1)
    if database_url.startswith("mysql+pymysql://") and "charset=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        return f"{database_url}{separator}charset=utf8mb4"
    return database_url


def fallback_profile():
    return SimpleNamespace(
        full_name="Portfolio",
        title="Portfolio",
        tagline="Available for Work",
        cv_subtitle="",
        about="Database connection is not available yet.",
        email="",
        phone="",
        address="",
        linkedin_url="",
        github_url="",
        website_url="",
        location="",
        availability_text="",
        contact_intro="",
        profile_image="about.png",
        hero_icon="fas fa-terminal",
    )


def create_app():
    load_dotenv()
    application = Flask(__name__, static_folder="static", static_url_path="/static")
    database_url = build_database_url()
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        secret_key = secrets.token_urlsafe(32)
        application.logger.warning("SECRET_KEY is not set; using a temporary development key.")

    # --- Configuration ---
    application.config.update(
        SECRET_KEY=secret_key,
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_pre_ping": True,
            "pool_recycle": int(os.environ.get("SQLALCHEMY_POOL_RECYCLE", "280")),
        },
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", ""),
        ADMIN_PASSWORD_HASH=os.environ.get("ADMIN_PASSWORD_HASH", ""),
        JSON_AS_ASCII=False,
        TEMPLATES_AUTO_RELOAD=True,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    )

    db.init_app(application)
    with application.app_context():
        try:
            db.create_all()
            ensure_schema()
            seed_database_from_json(application)
        except Exception as exc:
            application.logger.exception("Database startup failed: %s", exc)

    # --- Register Blueprints ---
    application.register_blueprint(admin_bp)
    application.register_blueprint(main_bp)
    application.register_blueprint(fragments_bp)  # HTMX fragments
    application.register_blueprint(contact_bp)
    application.register_blueprint(cv_bp)

    # --- Error Handlers (HTMX Aware) ---
    @application.errorhandler(404)
    def not_found(error):
        # If HTMX triggers a 404, send a partial, otherwise send full page
        if request.headers.get("HX-Request"):
            return render_template("partials/error_pages/error_404.html"), 404
        return render_template("partials/error_pages/404.html"), 404

    @application.errorhandler(500)
    def internal_error(error):
        application.logger.exception(error)
        if request.headers.get("HX-Request"):
            return render_template("partials/error_pages/error_500.html"), 500
        return render_template("partials/error_pages/500.html"), 500

    # --- Context Processors ---
    @application.context_processor
    def inject_globals():
        try:
            profile = get_profile()
            portfolio = get_portfolio()
        except Exception:
            application.logger.exception("Could not load database-backed page context.")
            profile = fallback_profile()
            portfolio = {
                "projects": [],
                "experience": [],
                "education": [],
                "skills": [],
                "certificates": [],
            }

        return {
            "profile": profile,
            "site_name": profile.full_name,
            "site_title": profile.title,
            "current_year": datetime.now().year,
            "portfolio": portfolio,
        }

    # --- Favicon Routes ---
    @application.route('/favicon.ico')
    def favicon():
        from flask import send_from_directory
        return send_from_directory(os.path.join(application.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @application.route('/favicon/favicon.svg')
    def favicon_svg():
        from flask import send_from_directory
        return send_from_directory(os.path.join(application.root_path, 'static', 'favicon'),
                                   'favicon.svg', mimetype='image/svg+xml')

    return application


app = create_app()
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=True)
