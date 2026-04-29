# Portfolio Website - ciaranc.dev

My personal portfolio website showcases my projects, skills, and experience as a software developer. Built with Flask and deployed on PythonAnywhere.

🌐 **Live Site**: [ciaranc.dev](https://www.ciaranc.dev)

## About Me

Final-year Computing & IT student at The Open University, specialising in Python and web development. Recently completed a software developer internship at TrailStone, where I gained hands-on experience building production applications.

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with Tailwind utility classes
- **Interactivity**: HTMX for dynamic content loading
- **Deployment**: PythonAnywhere
- **Version Control**: Git/GitHub

## Features

### Database-backed content
- MySQL-compatible SQLAlchemy models for profile, jobs, education, skills, projects, and certificates
- Unlinked, password-protected `/admin` editor for adding, editing, hiding, sorting, and deleting portfolio content
- First-run seeding from the existing JSON files so the current site content is preserved
- Generated `/get-cv` PDF built from the database content

### Architecture
- **Application Factory Pattern** - Scalable Flask application structure
- **Blueprint-based Routing** - Modular route organisation
- **Service Layer Architecture** - Separation of business logic
- **HTMX Partials** - Dynamic content loading without full page reloads

### Design
- **Warm Colour Scheme** - Professional yellow accent colours
- **Glassmorphism Effects** - Modern, frosted glass UI elements
- **Responsive Design** - Mobile-first approach, works on all devices
- **Theme Toggle** - Light/dark mode support
- **Accessibility Compliant** - ARIA attributes and semantic HTML

### Performance
- **CSS-only Solutions** - Minimal JavaScript dependencies
- **Modern CSS** - Uses `:has()` pseudo-class and other modern techniques
- **Optimised Loading** - Fast page loads and smooth interactions

## Development Approach

This portfolio was built with a focus on:
- **Clean, maintainable code** - Following best practices and design patterns
- **Accessibility** - Ensuring all users can access and navigate the site
- **Performance** - Optimising for fast load times and smooth interactions
- **User experience** - Intuitive navigation and clear presentation of information

## Local Development

```bash
# Clone the repository
git clone https://github.com/CiaranC968/pythonanywhere_flask.git
cd pythonanywhere_flask

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional local admin/database settings can go in an untracked .env file.
# Do not commit real secrets.
SECRET_KEY="<generate-a-secret>"
ADMIN_PASSWORD="<choose-a-local-admin-password>"
DATABASE_URL="sqlite:///portfolio.db"

# Run the application
python app.py
```

Visit `http://127.0.0.1:8080` in your browser.

Open `http://127.0.0.1:8080/admin` directly to edit the portfolio content. It is intentionally not linked from the public website. Admin login is disabled until `ADMIN_PASSWORD` or `ADMIN_PASSWORD_HASH` is set.

## PythonAnywhere MySQL Setup

Set these environment variables in your PythonAnywhere web app. Do not commit real values to Git:

```bash
SECRET_KEY="<generate-a-secret>"
ADMIN_PASSWORD="<choose-an-admin-password>"
DATABASE_URL="mysql+pymysql://<mysql-user>:<mysql-password>@<mysql-host>/<mysql-database>"
```

If your MySQL password contains symbols such as `@`, `#`, `/`, or `:`, use separate variables instead of a single URL:

```bash
SECRET_KEY="<generate-a-secret>"
ADMIN_PASSWORD="<choose-an-admin-password>"
MYSQL_USER="<mysql-user>"
MYSQL_PASSWORD="<mysql-password>"
MYSQL_HOST="<mysql-host>"
MYSQL_DATABASE="<mysql-database>"
```

On PythonAnywhere, make sure these are set for the web app process itself. If you only export them in a Bash console, the website may not see them after reload.

Prefer PythonAnywhere's environment-variable support if available. If you use a file, store it outside Git, for example `/home/ciaranc88/.env`, and point the WSGI file at it:

```python
import os
import sys

project_home = "/home/ciaranc88/pythonanywhere_flask"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ["ENV_FILE"] = "/home/ciaranc88/.env"

from app import application
```

After installing `requirements.txt` and reloading the web app, the tables are created automatically. If the database is empty, the current JSON content is imported once. Future edits should be made through `/admin`.

After logging in, open `/admin/diagnostics` to confirm the app can run `SELECT 1`, see the masked database URI, and list the tables.

The admin editor manages:
- Profile: name, title, CV subtitle, email, phone, address, links, about text, and hero text
- Experience: companies, jobs, timelines/promotions, bullet points, tech stack, logos, icons, visibility, and order
- Education: degrees, universities, years, modules/stages, progress, and results
- Skills, projects, and certificates, including JSON-powered links, tags, stats, and credential data

## Deployment

Deployed on PythonAnywhere with a continuous deployment workflow:
1. Make changes locally and test
2. Pushed to a GitHub repository
3. Pull changes on PythonAnywhere
4. Reload the web app

## Skills Demonstrated

- **Python & Flask** - Backend development with modern patterns
- **Web Development** - HTML, CSS, JavaScript
- **Responsive Design** - Mobile-first, cross-browser compatible
- **Accessibility** - WCAG compliance and semantic HTML
- **Version Control** - Git workflow and collaboration
- **Deployment** - Production hosting and DevOps
- **Problem-Solving** - Technical challenges and optimisation

## Contact

- **Portfolio**: [ciaranc.dev](https://www.ciaranc.dev)
- **GitHub**: [@CiaranC968](https://github.com/CiaranC968)
- **LinkedIn**: [Connect with me](https://linkedin.com/in/your-profile)

## Experience

**Software Developer Intern** - TrailStone  
Developed web applications and gained experience in professional software development practices.

## Education

**BSc (Hons) Computing & IT**  
The Open University - Final Year

---

Built with Flask, htmx and javascript
