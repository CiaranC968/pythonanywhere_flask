import logging
import os
import re
from datetime import date
from types import SimpleNamespace

from sqlalchemy.exc import SQLAlchemyError

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
    except SQLAlchemyError:
        _rollback_session()
        section = MODEL_SECTIONS.get(model, model.__name__)
        logger.exception("Database query failed for %s; using JSON fallback.", section)
        return _json_items(section)


def get_portfolio():
    portfolio = {name: visible_items(model) for name, model in COLLECTIONS.items()}
    portfolio["skills"] = skills_with_dynamic_metrics(
        portfolio["skills"],
        portfolio["projects"],
        portfolio["certificates"],
        portfolio["experience"],
    )
    return portfolio


def skills_with_dynamic_metrics(skills, projects, certificates, experience):
    metrics = [
        _skill_metrics(skill, projects, certificates, experience)
        for skill in skills
    ]
    max_years = max([metric["years"] for metric in metrics] + [1])
    return [
        _skill_with_metrics(skill, metric, max_years)
        for skill, metric in zip(skills, metrics)
    ]


def get_section_item(section, item_id, visible_only=True):
    model = COLLECTIONS[section]
    try:
        query = model.query
        if visible_only:
            query = query.filter_by(is_visible=True)
        item = query.filter_by(id=item_id).first()
        if item:
            return item
    except SQLAlchemyError:
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
    except SQLAlchemyError:
        logger.exception("Could not roll back the database session. Removing session and disposing engine.")
        db.session.remove()
        db.engine.dispose()


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


def _skill_metrics(skill, projects, certificates, experience):
    terms = _term_bag([getattr(skill, "title", ""), *(getattr(skill, "tags", None) or [])])
    matching_projects = [
        project for project in projects
        if _bags_overlap(terms, _term_bag(getattr(project, "tags", None) or []))
    ]
    matching_certificates = [
        cert for cert in certificates
        if _bags_overlap(
            terms,
            _term_bag([
                getattr(cert, "title", ""),
                getattr(cert, "desc", ""),
                *(getattr(cert, "skills", None) or []),
            ]),
        )
    ]
    matching_experience = [
        item for item in experience
        if _bags_overlap(terms, _experience_terms(item))
    ]

    years = []
    for project in matching_projects:
        years.extend(_project_years(project))
    for cert in matching_certificates:
        years.extend(_years_from_text(getattr(cert, "date", "")))
    for item in matching_experience:
        years.extend(_experience_years(item))

    first_year = min(years) if years else None
    return {
        "project_count": len(matching_projects),
        "certificate_count": len(matching_certificates),
        "years": _inclusive_years(first_year),
    }


def _skill_with_metrics(skill, metric, max_years):
    progress = dict(getattr(skill, "progress", None) or {})
    progress.update(
        {
            "label": progress.get("label") or "Experience",
            "value": metric["years"],
            "unit": progress.get("unit") or "years",
            "max": max(max_years, metric["years"], 1),
        }
    )

    stats = [
        stat for stat in (getattr(skill, "stats", None) or [])
        if not _is_dynamic_skill_stat(stat)
    ]
    if metric["project_count"]:
        stats.append({"icon": "fas fa-folder", "value": metric["project_count"], "label": "projects"})
    if metric["certificate_count"]:
        stats.append({"icon": "fas fa-award", "value": metric["certificate_count"], "label": "certs"})

    return _clone_item(skill, progress=progress, stats=stats)


def _is_dynamic_skill_stat(stat):
    icon = _normalise_term(stat.get("icon", ""))
    label = _normalise_term(stat.get("label", ""))
    return "folder" in icon or "award" in icon or "certificate" in icon or label in {"project", "projects", "cert", "certs", "certificate", "certificates"}


def _clone_item(item, **overrides):
    if hasattr(item, "__table__"):
        data = {column.name: getattr(item, column.name) for column in item.__table__.columns}
    else:
        data = {
            key: value
            for key, value in vars(item).items()
            if not key.startswith("_")
        }
    data.update(overrides)
    return SimpleNamespace(**data)


def _experience_terms(item):
    values = [
        getattr(item, "role", ""),
        getattr(item, "brief", ""),
        *(getattr(item, "tech_stack", None) or []),
        *(getattr(item, "skills", None) or []),
    ]
    for timeline_item in getattr(item, "timeline", None) or []:
        values.extend([
            timeline_item.get("role", ""),
            timeline_item.get("desc", ""),
            *(timeline_item.get("tech_stack", []) or []),
            *(timeline_item.get("skills", []) or []),
        ])
    return _term_bag(values)


def _experience_years(item):
    years = _years_from_text(getattr(item, "period", ""))
    for timeline_item in getattr(item, "timeline", None) or []:
        years.extend(_years_from_text(timeline_item.get("period", "")))
    return years


def _project_years(project):
    years = []
    for stat in getattr(project, "stats", None) or []:
        years.extend(_years_from_text(stat.get("value", "")))
    if not years and getattr(project, "status", "") in {"Live", "In Progress"}:
        years.append(date.today().year)
    return years


def _inclusive_years(first_year):
    if not first_year:
        return 0
    return max(1, date.today().year - first_year + 1)


def _years_from_text(value):
    return [
        int(match.group(0))
        for match in re.finditer(r"\b(?:19|20)\d{2}\b", str(value))
    ]


def _term_bag(values):
    phrases = set()
    tokens = set()
    for value in values:
        text = _normalise_term(value)
        if not text:
            continue
        phrases.add(text)
        tokens.update(part for part in text.split() if len(part) > 1)
    return {"phrases": phrases, "tokens": tokens}


def _normalise_term(value):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(value).lower())).strip()


def _bags_overlap(left, right):
    return bool(
        left["phrases"] & right["phrases"]
        or left["tokens"] & right["tokens"]
    )
