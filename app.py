import os
import secrets
from datetime import datetime
from types import SimpleNamespace
from urllib.parse import quote_plus

from flask import Flask, render_template, request
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Import Blueprints
from blueprints.admin import admin_bp
from blueprints.main import main_bp
from blueprints.fragments import fragments_bp
from blueprints.contact import contact_bp
from blueprints.cv import cv_bp

from extensions import db
from portfolio_data import get_portfolio, get_profile, seed_database_from_json


def load_dotenv(path=None):
    """Tiny .env loader for local dev; PythonAnywhere uses WSGI env values."""
    path = path or os.environ.get("ENV_FILE", ".env")
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def ensure_schema():
    """Small first-party schema patcher for simple PythonAnywhere deployments."""
    inspector = inspect(db.engine)
    if "profile" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("profile")}
    additions = {
        "cv_subtitle": "VARCHAR(180) NOT NULL DEFAULT ''",
        "phone": "VARCHAR(80) NOT NULL DEFAULT ''",
        "address": "VARCHAR(255) NOT NULL DEFAULT ''",
    }

    for column, definition in additions.items():
        if column not in existing:
            db.session.execute(text(f"ALTER TABLE profile ADD COLUMN {column} {definition}"))
    db.session.commit()


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
            f"@{host_part}/{quote_plus(mysql_database)}?charset=utf8mb4"
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

    return application


app = create_app()
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=True)
