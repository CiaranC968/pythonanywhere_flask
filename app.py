import json
import os
from functools import lru_cache
from flask import Flask, render_template, abort, send_from_directory, make_response, request
from werkzeug.exceptions import NotFound

app = Flask(__name__, static_folder='static', static_url_path='/static')

# --- Configuration ---
app.config.update(
    JSON_AS_ASCII=False,
    TEMPLATES_AUTO_RELOAD=True if os.environ.get('FLASK_ENV') == 'development' else False,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max request size
)


# --- Data Loading with Caching ---
@lru_cache(maxsize=32)
def load_json(filename):
    """
    Load JSON data with caching for better performance.
    Cache is cleared when app restarts.
    """
    path = os.path.join(app.root_path, 'data', filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        app.logger.error(f"JSON file not found: {filename}")
        return []
    except json.JSONDecodeError as e:
        app.logger.error(f"Error decoding JSON from {filename}: {e}")
        return []
    except Exception as e:
        app.logger.error(f"Unexpected error loading {filename}: {e}")
        return []


def find_item_by_id(data, item_id, id_field='id'):
    """Helper function to find items in data by ID"""
    return next((item for item in data if item.get(id_field) == item_id), None)


@app.errorhandler(404)
def not_found_error(error):
    # HTMX always sends the 'HX-Request' header
    if request.headers.get('HX-Request'):
        return render_template('partials/error_404.html'), 404
    return render_template('partials/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Internal error: {error}")
    return render_template('partials/error_500.html'), 500


# --- Main Route ---
@app.route("/")
def index():
    """Main portfolio page"""
    return render_template("index.html")


# --- Project Routes ---
@app.route("/fragment/projects")
def fragment_projects():
    """Load all project cards"""
    projects = load_json('projects.json')
    return render_template("partials/project_cards.html", projects=projects)


@app.route("/fragment/project-modal/<slug>")
def fragment_project_modal(slug):
    """Load individual project modal"""
    projects = load_json('projects.json')
    project = find_item_by_id(projects, slug, id_field='slug')

    if not project:
        app.logger.warning(f"Project not found: {slug}")
        abort(404)

    return render_template("partials/project_modal.html", p=project)


# --- Experience Routes ---
@app.route("/fragment/experience")
def fragment_experience_list():
    """Load all experience cards"""
    experience = load_json('experience.json')
    return render_template("partials/experience_cards.html", experience=experience)


@app.route("/fragment/experience/<company_id>")
def fragment_experience_detail(company_id):
    """Load individual experience modal"""
    experience = load_json('experience.json')
    job = find_item_by_id(experience, company_id)

    if not job:
        app.logger.warning(f"Experience not found: {company_id}")
        abort(404)

    return render_template("partials/experience_modal.html", exp=job)


# --- Education Routes ---
@app.route("/fragment/education")
def fragment_education():
    """Load all education cards"""
    education = load_json('education.json')
    return render_template("partials/education_cards.html", education=education)


@app.route("/fragment/education/<edu_id>")
def fragment_education_detail(edu_id):
    """Load individual education modal"""
    education = load_json('education.json')
    selected_edu = find_item_by_id(education, edu_id)

    if not selected_edu:
        app.logger.warning(f"Education not found: {edu_id}")
        abort(404)

    return render_template("partials/education_modal.html", edu=selected_edu)


# --- Skills Routes ---
@app.route("/fragment/skills")
def fragment_skills():
    """Load all skill cards"""
    skills = load_json('skills.json')
    return render_template("partials/skill_cards.html", skills=skills)


@app.route("/fragment/skill-modal/<skill_id>")
def fragment_skill_modal(skill_id):
    """Load individual skill modal"""
    skills = load_json('skills.json')
    skill = find_item_by_id(skills, skill_id)

    if not skill:
        app.logger.warning(f"Skill not found: {skill_id}")
        abort(404)

    return render_template("partials/skill_modal.html", skill=skill)


# --- Certificate Routes ---
@app.route("/fragment/certificates")
def fragment_certificates():
    """Load all certificate cards"""
    certificates = load_json('certificates.json')
    return render_template("partials/certificate_cards.html", certificates=certificates)


@app.route("/fragment/certificate-modal/<cert_id>")
def fragment_certificate_modal(cert_id):
    """Load individual certificate modal"""
    certificates = load_json('certificates.json')
    cert = find_item_by_id(certificates, cert_id)

    if not cert:
        app.logger.warning(f"Certificate not found: {cert_id}")
        abort(404)

    return render_template("partials/certificate_modal.html", cert=cert)


# --- Contact Route (NEW) ---
@app.route("/contact", methods=['POST'])
def contact():
    """
    Handle contact form submissions via HTMX.
    In a production app, you would send an email here using Flask-Mail.
    """
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    # Basic Validation
    if not name or not email or not message:
        return f"""
        <div class="mb-6 p-4 bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl text-red-800 dark:text-red-300 flex items-center gap-3">
            <i class="fas fa-exclamation-circle text-xl"></i>
            <div>
                <p class="font-bold">Error</p>
                <p class="text-sm">Please fill out all required fields.</p>
            </div>
        </div>
        """, 200 # Return 200 so HTMX renders the error HTML

    # LOGGING: This simulates sending the email. Check your terminal!
    app.logger.info(f"----- NEW MESSAGE -----")
    app.logger.info(f"From: {name} <{email}>")
    app.logger.info(f"Subject: {subject}")
    app.logger.info(f"Message: {message}")
    app.logger.info(f"-----------------------")

    # Return HTML Fragment for Success Message
    # This replaces the #form-response div in your HTML
    return f"""
    <div class="mb-6 p-4 bg-green-100 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-xl text-green-800 dark:text-green-300 flex items-center gap-3 animate-fade-in-up">
        <i class="fas fa-check-circle text-xl"></i>
        <div>
            <p class="font-bold">Message Sent!</p>
            <p class="text-sm">Thanks {name}, I'll get back to you shortly.</p>
        </div>
    </div>
    <script>
        // Clear the form fields after successful submission
        document.querySelector('form').reset();
    </script>
    """


# --- CV Routes ---
@app.route("/fragment/cv")
def fragment_cv():
    """Load CV modal content"""
    return render_template("partials/cv_modal.html")


@app.route("/get-cv")
def get_cv_file():
    """Download or view CV PDF"""
    directory = os.path.join(app.root_path, 'static', 'docs')
    filename = "Ciaran_Cairns_CV.pdf"

    # Check if file exists
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        app.logger.error(f"CV file not found: {filepath}")
        abort(404)

    try:
        response = make_response(send_from_directory(directory, filename))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        return response
    except Exception as e:
        app.logger.error(f"Error serving CV: {e}")
        abort(500)


# --- Context Processors ---
@app.context_processor
def inject_globals():
    """Inject global variables into all templates"""
    return {
        'site_name': 'Ciaran Cairns',
        'site_title': 'Software Developer',
        'current_year': 2025
    }


# --- CLI Commands for Development ---
@app.cli.command()
def clear_cache():
    """Clear the JSON cache"""
    load_json.cache_clear()
    print("Cache cleared!")


@app.cli.command()
def validate_data():
    """Validate all JSON data files"""
    files = ['projects.json', 'experience.json', 'education.json',
             'skills.json', 'certificates.json']

    for filename in files:
        data = load_json(filename)
        if data:
            print(f"✓ {filename}: {len(data)} items loaded")
        else:
            print(f"✗ {filename}: Failed to load or empty")


if __name__ == "__main__":
    # Development server configuration
    app.run(
        port=5000,
        debug=True,
    )