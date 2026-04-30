from flask import Blueprint, render_template, abort

from portfolio_data import get_section_item, skills_with_dynamic_metrics, visible_items
from models import Certificate, Education, Experience, Project, Skill

fragments_bp = Blueprint("fragments", __name__, url_prefix="/fragment")


@fragments_bp.route("/projects")
def projects():
    return render_template(
        "partials/cards/unified_cards.html",
        items=visible_items(Project),
        type="project",
        limit=6,
        toggle_label="projects",
    )


@fragments_bp.route("/project-modal/<project_id>")
def project_modal(project_id):
    project = get_section_item("projects", project_id)
    if not project:
        abort(404)
    return render_template("partials/modals/project_modal.html", p=project)


@fragments_bp.route("/experience")
def experience():
    return render_template(
        "partials/cards/experience_cards.html",
        experience=visible_items(Experience)
    )


@fragments_bp.route("/experience/<company_id>")
def experience_detail(company_id):
    job = get_section_item("experience", company_id)
    if not job:
        abort(404)
    return render_template("partials/modals/experience_modal.html", exp=job)


@fragments_bp.route("/education")
def education():
    return render_template(
        "partials/cards/education_cards.html",
        education=visible_items(Education)
    )


@fragments_bp.route("/education/<edu_id>")
def education_detail(edu_id):
    edu = get_section_item("education", edu_id)
    if not edu:
        abort(404)
    return render_template("partials/modals/education_modal.html", edu=edu)


@fragments_bp.route("/skills")
def skills():
    skill_items = skills_with_dynamic_metrics(
        visible_items(Skill),
        visible_items(Project),
        visible_items(Certificate),
        visible_items(Experience),
    )
    return render_template(
        "partials/cards/unified_cards.html",
        items=skill_items,
        type="skill"
    )

@fragments_bp.route("/skill-modal/<skill_id>")
def skill_modal(skill_id):
    skill = next(
        (
            item for item in skills_with_dynamic_metrics(
                visible_items(Skill),
                visible_items(Project),
                visible_items(Certificate),
                visible_items(Experience),
            )
            if item.id == skill_id
        ),
        None,
    )
    if not skill:
        abort(404)
    return render_template("partials/modals/skill_modal.html", skill=skill)


@fragments_bp.route("/certificates")
def certificates():
    return render_template(
        "partials/cards/certificate_cards.html",
        certificates=visible_items(Certificate)
    )


@fragments_bp.route("/certificate-modal/<cert_id>")
def certificate_modal(cert_id):
    cert = get_section_item("certificates", cert_id)
    if not cert:
        abort(404)
    return render_template("partials/modals/certificate_modal.html", cert=cert)


@fragments_bp.route("/cv")
def cv_modal():
    return render_template("partials/modals/cv_modal.html")
