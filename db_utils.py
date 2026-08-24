from sqlalchemy import inspect, text
from extensions import db

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
            "stage_updated_at": "VARCHAR(80) NULL",
            "applied_date": "VARCHAR(80) NOT NULL DEFAULT ''",
            "interview_date": "VARCHAR(80) NULL",
            "assessment_date": "VARCHAR(80) NULL",
            "application_deadline": "VARCHAR(80) NULL",
            "reached_interview": f"{boolean} NOT NULL DEFAULT 0",
            "reached_assessment": f"{boolean} NOT NULL DEFAULT 0",
            "badges": "VARCHAR(500) NOT NULL DEFAULT ''",
            "notes": "TEXT NULL",
            "job_url": "VARCHAR(500) NULL",
            "company_url": "VARCHAR(500) NULL",
            "company_address": "VARCHAR(500) NULL",
            "linkedin_url": "VARCHAR(500) NULL",
            "salary": "VARCHAR(120) NULL",
            "location": "VARCHAR(180) NULL",
            "source": "VARCHAR(120) NOT NULL DEFAULT ''",
            "follow_up_date": "VARCHAR(80) NULL",
            "reminder_note": "TEXT NULL",
            "reminder_done": f"{boolean} NOT NULL DEFAULT 0",
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
        "job_application": {
            "source": "",
            "reminder_note": "",
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
