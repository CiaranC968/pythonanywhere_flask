from datetime import datetime

from flask import Blueprint, render_template

from models import Certificate, Education, Experience, Project, Skill


main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route('/health')
def health():
    try:
        checks = {
            'projects': Project.query.filter_by(is_visible=True).count() > 0,
            'experience': Experience.query.filter_by(is_visible=True).count() > 0,
            'education': Education.query.filter_by(is_visible=True).count() > 0,
            'skills': Skill.query.filter_by(is_visible=True).count() > 0,
            'certificates': Certificate.query.filter_by(is_visible=True).count() > 0,
        }
    except Exception as exc:
        return {
            'status': 'degraded',
            'timestamp': datetime.now().isoformat(),
            'error': str(exc),
            'checks': {}
        }, 503

    all_healthy = all(checks.values())

    return {
        'status': 'healthy' if all_healthy else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'checks': checks
    }, 200 if all_healthy else 503
