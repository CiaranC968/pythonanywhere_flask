import os
from datetime import datetime
from flask import Flask, render_template, request

from blueprints.main import main_bp
from blueprints.fragments import fragments_bp
from blueprints.contact import contact_bp
from blueprints.cv import cv_bp
from utils import load_json_file


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    # --- Configuration ---
    app.config.update(
        JSON_AS_ASCII=False,
        TEMPLATES_AUTO_RELOAD=os.environ.get("FLASK_ENV") == "development",
        MAX_CONTENT_LENGTH=16 * 1024 * 1024
    )

    # --- Load Data Once at Startup ---
    app.config["DATA"] = {
        "projects": load_json_file(app.root_path, "projects.json"),
        "experience": load_json_file(app.root_path, "experience.json"),
        "education": load_json_file(app.root_path, "education.json"),
        "skills": load_json_file(app.root_path, "skills.json"),
        "certificates": load_json_file(app.root_path, "certificates.json"),
    }

    # --- Blueprints ---
    app.register_blueprint(main_bp)
    app.register_blueprint(fragments_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(cv_bp)

    # --- Error Handlers ---
    @app.errorhandler(404)
    def not_found(error):
        if request.headers.get("HX-Request"):
            return render_template("partials/error_404.html"), 404
        return render_template("partials/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(error)
        return render_template("partials/error_500.html"), 500

    # --- Context Processor ---
    @app.context_processor
    def inject_globals():
        return {
            "site_name": "Ciaran Cairns",
            "site_title": "Software Developer",
            "current_year": datetime.now().year,
        }

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5000, debug=True)