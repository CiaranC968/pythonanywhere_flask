from extensions import db


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True, default=1)
    full_name = db.Column(db.String(120), nullable=False, default="Your Name")
    title = db.Column(db.String(160), nullable=False, default="Software Developer")
    tagline = db.Column(db.String(255), nullable=False, default="Available for Work")
    cv_subtitle = db.Column(db.String(180), nullable=False, default="")
    about = db.Column(db.Text, nullable=False, default="")
    email = db.Column(db.String(255), nullable=False, default="")
    phone = db.Column(db.String(80), nullable=False, default="")
    address = db.Column(db.String(255), nullable=False, default="")
    linkedin_url = db.Column(db.String(500), nullable=False, default="")
    github_url = db.Column(db.String(500), nullable=False, default="")
    website_url = db.Column(db.String(500), nullable=False, default="")
    location = db.Column(db.String(160), nullable=False, default="")
    availability_text = db.Column(db.String(160), nullable=False, default="Available for new projects")
    contact_intro = db.Column(db.Text, nullable=False, default="")
    profile_image = db.Column(db.String(255), nullable=False, default="about.png")
    hero_icon = db.Column(db.String(120), nullable=False, default="fas fa-terminal")


class SortableMixin:
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)


class Project(db.Model, SortableMixin):
    id = db.Column(db.String(80), primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    desc = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(80), nullable=False, default="Completed")
    icon = db.Column(db.String(120), nullable=False, default="fas fa-folder")
    iconColor = db.Column(db.String(120), nullable=False, default="text-gray-600")
    bgColor = db.Column(db.String(120), nullable=False, default="bg-gray-100")
    tags = db.Column(db.JSON, nullable=False, default=list)
    links = db.Column(db.JSON, nullable=False, default=list)
    stats = db.Column(db.JSON, nullable=False, default=list)
    features = db.Column(db.JSON, nullable=False, default=list)
    challenges = db.Column(db.Text, nullable=False, default="")
    image = db.Column(db.String(255), nullable=False, default="")


class Skill(db.Model, SortableMixin):
    id = db.Column(db.String(80), primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    desc = db.Column(db.Text, nullable=False, default="")
    icon = db.Column(db.String(120), nullable=False, default="fas fa-code")
    iconColor = db.Column(db.String(120), nullable=False, default="text-gray-600")
    bgColor = db.Column(db.String(120), nullable=False, default="bg-gray-100")
    tags = db.Column(db.JSON, nullable=False, default=list)
    progress = db.Column(db.JSON, nullable=True)
    stats = db.Column(db.JSON, nullable=False, default=list)


class Experience(db.Model, SortableMixin):
    id = db.Column(db.String(80), primary_key=True)
    company = db.Column(db.String(180), nullable=False)
    role = db.Column(db.String(180), nullable=False)
    period = db.Column(db.String(120), nullable=False, default="")
    brief = db.Column(db.Text, nullable=False, default="")
    details = db.Column(db.JSON, nullable=False, default=list)
    tech_stack = db.Column(db.JSON, nullable=False, default=list)
    timeline = db.Column(db.JSON, nullable=False, default=list)
    skills = db.Column(db.JSON, nullable=False, default=list)
    logo = db.Column(db.String(255), nullable=False, default="")
    location = db.Column(db.String(180), nullable=False, default="")
    type = db.Column(db.String(120), nullable=False, default="")
    icon = db.Column(db.String(120), nullable=False, default="fas fa-building")
    bgIcon = db.Column(db.String(120), nullable=False, default="fas fa-briefcase")
    iconColor = db.Column(db.String(120), nullable=False, default="text-gray-600")
    bgColor = db.Column(db.String(120), nullable=False, default="bg-gray-100")
    hoverColor = db.Column(db.String(120), nullable=False, default="text-gray-900")
    current = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def duration(self):
        return self.period


class Education(db.Model, SortableMixin):
    id = db.Column(db.String(80), primary_key=True)
    degree = db.Column(db.String(220), nullable=False)
    university = db.Column(db.String(220), nullable=False)
    year = db.Column(db.String(120), nullable=False, default="")
    logo = db.Column(db.String(255), nullable=False, default="")
    description = db.Column(db.Text, nullable=False, default="")
    stages = db.Column(db.JSON, nullable=False, default=dict)
    progress = db.Column(db.Integer, nullable=True)
    current = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(120), nullable=False, default="")
    total_credits = db.Column(db.Integer, nullable=True)
    gpa = db.Column(db.String(40), nullable=False, default="")
    modules_completed = db.Column(db.Integer, nullable=True)


class Certificate(db.Model, SortableMixin):
    id = db.Column(db.String(80), primary_key=True)
    title = db.Column(db.String(220), nullable=False)
    issuer = db.Column(db.String(220), nullable=False)
    date = db.Column(db.String(120), nullable=False, default="")
    desc = db.Column(db.Text, nullable=False, default="")
    image_path = db.Column(db.String(500), nullable=False, default="")
    logo = db.Column(db.String(255), nullable=False, default="")
    link = db.Column(db.String(500), nullable=False, default="#")
    credential_id = db.Column(db.String(180), nullable=False, default="")
    skills = db.Column(db.JSON, nullable=False, default=list)
    verified = db.Column(db.Boolean, nullable=False, default=False)


class ResumeTemplate(db.Model, SortableMixin):
    id = db.Column(db.Integer, primary_key=True)
    target = db.Column(db.String(80), nullable=False, default="company_details")
    label = db.Column(db.String(120), nullable=False, default="")
    text = db.Column(db.Text, nullable=False, default="")


class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(180), nullable=False)
    role = db.Column(db.String(180), nullable=False)
    stage = db.Column(db.String(80), nullable=False, default="Applied")  # Not Applied Yet, Applied, Interview, Rejected, Got Job, Missed Deadline
    applied_date = db.Column(db.String(80), nullable=False, default="")
    interview_date = db.Column(db.String(80), nullable=True)  # Format: YYYY-MM-DD or datetime
    application_deadline = db.Column(db.String(80), nullable=True)  # Format: YYYY-MM-DD or datetime
    notes = db.Column(db.Text, nullable=False, default="")


