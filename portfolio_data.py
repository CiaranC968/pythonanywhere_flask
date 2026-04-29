import logging
import os

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
    return (
        model.query.filter_by(is_visible=True)
        .order_by(model.sort_order.asc(), model.id.asc())
        .all()
    )


def get_portfolio():
    return {name: visible_items(model) for name, model in COLLECTIONS.items()}


def get_section_item(section, item_id, visible_only=True):
    model = COLLECTIONS[section]
    query = model.query
    if visible_only:
        query = query.filter_by(is_visible=True)
    return query.filter_by(id=item_id).first()


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
