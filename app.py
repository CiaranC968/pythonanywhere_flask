import json
import os
from flask import Flask, render_template, abort, send_from_directory, make_response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')

# --- Configuration ---
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-secret-change-me")

# --- Helpers ---
def load_json(filename):
    path = os.path.join(app.root_path, 'data', filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filename}: {e}")
        return []

# --- Main Route ---
@app.route("/")
def index():
    return render_template("index.html")

# --- Fragment Routes ---
@app.route("/fragment/projects")
def fragment_projects():
    return render_template("partials/project_cards.html", projects=load_json('projects.json'))

@app.route("/fragment/project-modal/<slug>")
def fragment_project_modal(slug):
    p = next((x for x in load_json('projects.json') if x["slug"] == slug), None)
    if not p: abort(404)
    return render_template("partials/project_modal.html", p=p)

@app.route("/fragment/experience")
def fragment_experience_list():
    return render_template("partials/experience_cards.html", experience=load_json('experience.json'))

@app.route("/fragment/experience/<company_id>")
def fragment_experience_detail(company_id):
    job = next((item for item in load_json('experience.json') if item["id"] == company_id), None)
    if not job: abort(404)
    return render_template("partials/experience_modal.html", exp=job)

@app.route("/fragment/education")
def fragment_education():
    """Renders the grid of cards on the main page"""
    return render_template(
        "partials/education_cards.html",
        education=load_json('education.json')
    )

@app.route("/fragment/education/<edu_id>")
def fragment_education_detail(edu_id):
    """Renders the content inside the pop-up modal"""
    education_data = load_json('education.json')
    selected_edu = next((item for item in education_data if item['id'] == edu_id), None)

    if not selected_edu:
        abort(404)

    return render_template(
        "partials/education_modal.html",
        edu=selected_edu
    )

@app.route("/fragment/skills")
def fragment_skills():
    return render_template("partials/skill_cards.html", skills=load_json('skills.json'))

@app.route("/fragment/skill-modal/<skill_id>")
def fragment_skill_modal(skill_id):
    skill = next((s for s in load_json('skills.json') if s["id"] == skill_id), None)
    if not skill: abort(404)
    return render_template("partials/skill_modal.html", skill=skill)

@app.route("/fragment/certificates")
def fragment_certificates():
    return render_template("partials/certificate_cards.html", certificates=load_json('certificates.json'))

@app.route("/fragment/certificate-modal/<cert_id>")
def fragment_certificate_modal(cert_id):
    cert = next((c for c in load_json('certificates.json') if c["id"] == cert_id), None)
    if not cert: abort(404)
    return render_template("partials/certificate_modal.html", cert=cert)

@app.route("/fragment/cv")
def fragment_cv():
    return render_template("partials/cv_modal.html")

@app.route("/get-cv")
def get_cv_file():
    directory = os.path.join(app.root_path, 'static', 'docs')
    filename = "Ciaran_Cairns_CV.pdf"
    response = make_response(send_from_directory(directory, filename))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=%s' % filename
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
