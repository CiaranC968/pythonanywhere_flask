import logging
import os
from types import SimpleNamespace

from extensions import db
from models import Certificate, Education, Experience, Profile, Project, Skill
from utils import load_json_file

logger = logging.getLogger(__name__)


COLLECTIONS = {
    "projects": Project,
    "experience": Experience,
    "education": Education,
    "skills": Skill,
    "certificates": Certificate,
}
MODEL_SECTIONS = {model: section for section, model in COLLECTIONS.items()}
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

FALLBACK_DEFAULTS = {
    "projects": {
        "desc": "",
        "status": "Completed",
        "icon": "fas fa-folder",
        "iconColor": "text-gray-600",
        "bgColor": "bg-gray-100",
        "tags": [],
        "links": [],
        "stats": [],
        "features": [],
        "challenges": "",
        "image": "",
    },
    "skills": {
        "desc": "",
        "icon": "fas fa-code",
        "iconColor": "text-gray-600",
        "bgColor": "bg-gray-100",
        "tags": [],
        "progress": None,
        "stats": [],
    },
    "experience": {
        "role": "",
        "period": "",
        "brief": "",
        "details": [],
        "tech_stack": [],
        "timeline": [],
        "skills": [],
        "logo": "",
        "location": "",
        "type": "",
        "icon": "fas fa-building",
        "bgIcon": "fas fa-briefcase",
        "iconColor": "text-gray-600",
        "bgColor": "bg-gray-100",
        "hoverColor": "text-gray-900",
        "current": False,
    },
    "education": {
        "year": "",
        "logo": "",
        "description": "",
        "stages": {},
        "progress": None,
        "current": False,
        "status": "",
        "total_credits": None,
        "gpa": "",
        "modules_completed": None,
    },
    "certificates": {
        "date": "",
        "desc": "",
        "image_path": "",
        "logo": "",
        "link": "#",
        "credential_id": "",
        "skills": [],
        "verified": False,
    },
}


def get_profile():
    profile = db.session.get(Profile, 1)
    if profile:
        return profile

    profile = Profile(
        id=1,
        full_name="Ciaran Cairns",
        title="Software Developer",
        tagline="Available for Work",
        cv_subtitle="Stage 2 BSc Computing and IT (Software)",
        about="I'm a final-year Computing & IT student at the Open University specialising in building robust, user-centric software solutions.",
        email="ciarancairns@googlemail.com",
        phone="",
        address="",
        linkedin_url="https://www.linkedin.com/in/ciarancairns",
        github_url="https://github.com/CiaranC968",
        website_url="https://www.ciaranc.dev",
        location="Northern Ireland",
        availability_text="Available for new projects",
        contact_intro="I'm currently looking for full-time roles or internships.",
        profile_image="about.png",
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def visible_items(model):
    try:
        return (
            model.query.filter_by(is_visible=True)
            .order_by(model.sort_order.asc(), model.id.asc())
            .all()
        )
    except Exception:
        _rollback_session()
        section = MODEL_SECTIONS.get(model, model.__name__)
        logger.exception("Database query failed for %s; using JSON fallback.", section)
        return _json_items(section)


def get_portfolio():
    return {name: visible_items(model) for name, model in COLLECTIONS.items()}


def get_section_item(section, item_id, visible_only=True):
    model = COLLECTIONS[section]
    try:
        query = model.query
        if visible_only:
            query = query.filter_by(is_visible=True)
        item = query.filter_by(id=item_id).first()
        if item:
            return item
    except Exception:
        _rollback_session()
        logger.exception("Database lookup failed for %s/%s; using JSON fallback.", section, item_id)

    return _json_item(section, item_id, visible_only=visible_only)


def seed_database_from_json(app):
    """Create first-run content from the existing JSON files."""
    if Project.query.first() or Skill.query.first() or Experience.query.first():
        get_profile()
        return

    data_dir = os.path.join(app.root_path, "data")
    for section, model in COLLECTIONS.items():
        records = load_json_file(data_dir, f"{section}.json")
        for index, record in enumerate(records):
            item = model(**_filter_model_fields(model, record))
            item.sort_order = index
            item.is_visible = True
            db.session.add(item)

    get_profile()
    db.session.commit()
    logger.info("Seeded portfolio database from JSON files.")


def _filter_model_fields(model, record):
    columns = {column.name for column in model.__table__.columns}
    return {key: value for key, value in record.items() if key in columns}


def _rollback_session():
    try:
        db.session.rollback()
    except Exception:
        logger.exception("Could not roll back the database session.")


def _json_items(section):
    records = load_json_file(DATA_DIR, f"{section}.json")
    items = []
    for index, record in enumerate(records):
        if record.get("is_visible", True):
            items.append(_namespace_item(section, record, index))
    return items


def _json_item(section, item_id, visible_only=True):
    for index, record in enumerate(load_json_file(DATA_DIR, f"{section}.json")):
        if record.get("id") != item_id:
            continue
        if visible_only and not record.get("is_visible", True):
            return None
        return _namespace_item(section, record, index)
    return None


def _namespace_item(section, record, index):
    data = {
        **FALLBACK_DEFAULTS.get(section, {}),
        **record,
        "sort_order": record.get("sort_order", index),
        "is_visible": record.get("is_visible", True),
    }
    if section == "experience":
        data["duration"] = data.get("period", "")
    return SimpleNamespace(**data)
