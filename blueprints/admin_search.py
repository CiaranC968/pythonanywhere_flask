import json

from flask import url_for

from models import (
    Certificate,
    Education,
    Experience,
    InterviewAnswer,
    JobApplication,
    Profile,
    Project,
    ResumeTemplate,
    Skill,
)


CONTENT_SEARCH_CONFIG = (
    ("profile", "Profile", "fa-user", Profile, ("full_name", "title", "about", "location")),
    ("experience", "Experience", "fa-briefcase", Experience, ("company", "role", "period", "brief", "details", "tech_stack")),
    ("education", "Education", "fa-graduation-cap", Education, ("degree", "university", "year", "description", "stages")),
    ("skills", "Skills", "fa-code", Skill, ("title", "desc", "tags")),
    ("projects", "Projects", "fa-folder-open", Project, ("title", "desc", "status", "tags", "features")),
    ("certificates", "Certificates", "fa-award", Certificate, ("title", "issuer", "date", "desc", "skills")),
)


def _text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _matches(query_terms, values):
    searchable = " ".join(_text(value) for value in values).casefold()
    return all(term in searchable for term in query_terms)


def _content_result(section, label, icon, item):
    if section == "profile":
        title = item.full_name
        subtitle = item.title
    elif section == "experience":
        title = item.role
        subtitle = item.company
    elif section == "education":
        title = item.degree
        subtitle = item.university
    elif section == "certificates":
        title = item.title
        subtitle = item.issuer
    else:
        title = item.title
        subtitle = getattr(item, "status", "") or getattr(item, "desc", "")

    return {
        "category": label,
        "icon": icon,
        "title": title,
        "subtitle": subtitle,
        "url": url_for("admin.edit_item", section=section, item_id=item.id),
    }


def search_admin_content(query, limit=24):
    query_terms = [term for term in query.casefold().split() if term]
    if not query_terms:
        return []

    results = []
    for section, label, icon, model, fields in CONTENT_SEARCH_CONFIG:
        for item in model.query.all():
            if not _matches(query_terms, (getattr(item, field, "") for field in fields)):
                continue
            results.append(_content_result(section, label, icon, item))
            if len(results) >= limit:
                return results

    company_names = set()
    for application in JobApplication.query.order_by(JobApplication.id.desc()).all():
        values = (
            application.company,
            application.role,
            application.stage,
            application.notes,
            application.badges,
            application.location,
            application.source,
            application.interview_research,
            application.interview_questions,
        )
        if _matches(query_terms, values):
            results.append(
                {
                    "category": "Applications",
                    "icon": "fa-briefcase",
                    "title": application.role,
                    "subtitle": f"{application.company} · {application.stage}",
                    "url": f'{url_for("admin.job_tracker")}#application-{application.id}',
                }
            )

        company_key = " ".join(application.company.casefold().split())
        if company_key not in company_names and _matches(query_terms, (application.company,)):
            company_names.add(company_key)
            results.append(
                {
                    "category": "Companies",
                    "icon": "fa-building",
                    "title": application.company,
                    "subtitle": "Open company application history",
                    "url": url_for("admin.job_company", company_name=application.company),
                }
            )
        if len(results) >= limit:
            return results[:limit]

    for template in ResumeTemplate.query.filter_by(is_visible=True).all():
        if _matches(query_terms, (template.label, template.text, template.target)):
            results.append(
                {
                    "category": "Templates",
                    "icon": "fa-file-lines",
                    "title": template.label,
                    "subtitle": "Resume wording template",
                    "url": url_for("admin.resume_builder"),
                }
            )
        if len(results) >= limit:
            return results[:limit]

    for answer in InterviewAnswer.query.order_by(InterviewAnswer.updated_at.desc()).all():
        if _matches(
            query_terms,
            (answer.category, answer.question, answer.situation, answer.task, answer.action, answer.result, answer.tags),
        ):
            results.append(
                {
                    "category": "Answer bank",
                    "icon": "fa-comments",
                    "title": answer.question,
                    "subtitle": answer.category,
                    "url": f'{url_for("admin.job_tracker")}?section=answer-bank',
                }
            )
        if len(results) >= limit:
            break

    return results[:limit]
