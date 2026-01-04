from flask import Blueprint, render_template, abort, current_app
from utils import find_item_by_id

fragments_bp = Blueprint("fragments", __name__, url_prefix="/fragment")


@fragments_bp.route("/projects")
def projects():
    return render_template(
        "partials/project_cards.html",
        projects=current_app.config["DATA"]["projects"]
    )


@fragments_bp.route("/project-modal/<slug>")
def project_modal(slug):
    project = find_item_by_id(current_app.config["DATA"]["projects"], slug, "slug")
    if not project:
        abort(404)
    return render_template("partials/project_modal.html", p=project)


@fragments_bp.route("/experience")
def experience():
    return render_template(
        "partials/experience_cards.html",
        experience=current_app.config["DATA"]["experience"]
    )


@fragments_bp.route("/experience/<company_id>")
def experience_detail(company_id):
    job = find_item_by_id(current_app.config["DATA"]["experience"], company_id)
    if not job:
        abort(404)
    return render_template("partials/experience_modal.html", exp=job)


@fragments_bp.route("/education")
def education():
    return render_template(
        "partials/education_cards.html",
        education=current_app.config["DATA"]["education"]
    )


@fragments_bp.route("/education/<edu_id>")
def education_detail(edu_id):
    edu = find_item_by_id(current_app.config["DATA"]["education"], edu_id)
    if not edu:
        abort(404)
    return render_template("partials/education_modal.html", edu=edu)


@fragments_bp.route("/skills")
def skills():
    return render_template(
        "partials/skill_cards.html",
        skills=current_app.config["DATA"]["skills"]
    )


@fragments_bp.route("/skill-modal/<skill_id>")
def skill_modal(skill_id):
    skill = find_item_by_id(current_app.config["DATA"]["skills"], skill_id)
    if not skill:
        abort(404)
    return render_template("partials/skill_modal.html", skill=skill)


@fragments_bp.route("/certificates")
def certificates():
    return render_template(
        "partials/certificate_cards.html",
        certificates=current_app.config["DATA"]["certificates"]
    )


@fragments_bp.route("/certificate-modal/<cert_id>")
def certificate_modal(cert_id):
    cert = find_item_by_id(current_app.config["DATA"]["certificates"], cert_id)
    if not cert:
        abort(404)
    return render_template("partials/certificate_modal.html", cert=cert)


@fragments_bp.route("/cv")
def cv_modal():
    return render_template("partials/cv_modal.html")