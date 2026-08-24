from datetime import datetime

from flask import Blueprint, render_template
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Certificate, Education, Experience, Project, Skill


main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route('/health')
def health():
    try:
        db.session.execute(text("SELECT 1"))
        content_counts = {
            'projects': Project.query.filter_by(is_visible=True).count(),
            'experience': Experience.query.filter_by(is_visible=True).count(),
            'education': Education.query.filter_by(is_visible=True).count(),
            'skills': Skill.query.filter_by(is_visible=True).count(),
            'certificates': Certificate.query.filter_by(is_visible=True).count(),
        }
    except SQLAlchemyError:
        return {
            'status': 'degraded',
            'timestamp': datetime.now().isoformat(),
            'error': 'Database health check failed.',
            'checks': {'database': False},
            'content_counts': {},
        }, 503

    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {'database': True},
        'content_counts': content_counts,
    }
