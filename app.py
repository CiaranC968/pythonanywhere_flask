import json
import os
from flask import Flask, render_template, request, abort, jsonify, send_from_directory, make_response
from dotenv import load_dotenv
from flask_mail import Mail, Message

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')

# --- Configuration ---
def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "t", "yes", "y"}

app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-change-me"),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_USE_TLS=_bool_env("MAIL_USE_TLS", "true"),
    MAIL_USE_SSL=_bool_env("MAIL_USE_SSL", "false"),
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER") or os.getenv("MAIL_USERNAME"),
)

mail = Mail(app)

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
    return render_template("partials/education_details.html", education=load_json('education.json'))

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

# --- Contact Form ---
@app.route("/send-email", methods=["POST"])
def send_email():
    if request.form.get("fax_number"): return "", 200
    name, email, message = request.form.get("name", ""), request.form.get("email", ""), request.form.get("message", "")
    if not name or not email or not message: return "Missing fields", 400
    msg = Message(subject=f"Contact: {name}", recipients=[os.getenv("MAIL_RECIPIENT") or app.config["MAIL_USERNAME"]],
                  reply_to=email, body=f"From: {name} ({email})\n\n{message}")
    try:
        mail.send(msg)
        return "<p class='text-green-500 font-bold'>Message sent!</p>", 200
    except Exception as e:
        return f"<p class='text-red-500'>Error: {str(e)}</p>", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)