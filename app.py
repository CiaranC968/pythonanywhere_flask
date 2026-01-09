import os
from datetime import datetime
from flask import Flask, render_template, request, current_app

# Import Blueprints
from blueprints.main import main_bp
from blueprints.fragments import fragments_bp
from blueprints.contact import contact_bp
from blueprints.cv import cv_bp

# Import Utility
from utils import load_json_file


def create_app():
    application = Flask(__name__, static_folder="static", static_url_path="/static")

    # --- Configuration ---
    application.config.update(
        JSON_AS_ASCII=False,
        TEMPLATES_AUTO_RELOAD=True,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    )

    # --- Load Data Strategy ---
    data_dir = os.path.join(application.root_path, 'data')

    # Load all data into app.config so it persists in memory
    application.config["DATA"] = {
        "projects": load_json_file(data_dir, "projects.json"),
        "experience": load_json_file(data_dir, "experience.json"),
        "education": load_json_file(data_dir, "education.json"),
        "skills": load_json_file(data_dir, "skills.json"),
        "certificates": load_json_file(data_dir, "certificates.json"),
    }

    # --- Register Blueprints ---
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
        return {
            "site_name": "Ciaran Cairns",
            "site_title": "Software Developer",
            "current_year": datetime.now().year,
            "portfolio": application.config["DATA"]
        }

    return application


app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)