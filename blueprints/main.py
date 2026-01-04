from flask import Blueprint, render_template
from datetime import datetime
from flask import current_app


main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route('/health')
def health():
    data = current_app.config.get("DATA", {})

    checks = {
        'projects': bool(data.get('projects')),
        'experience': bool(data.get('experience')),
        'education': bool(data.get('education')),
        'skills': bool(data.get('skills')),
        'certificates': bool(data.get('certificates')),
    }

    all_healthy = all(checks.values())

    return {
        'status': 'healthy' if all_healthy else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'checks': checks
    }, 200 if all_healthy else 503
