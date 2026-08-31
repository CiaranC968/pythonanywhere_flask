JOB_ATTACHMENT_EXTENSIONS = {".doc", ".docx", ".jpeg", ".jpg", ".pdf", ".png", ".txt"}

JOB_OPTIONAL_FIELDS = {
    "stage_updated_at",
    "interview_date",
    "assessment_date",
    "application_deadline",
    "job_url",
    "company_url",
    "company_address",
    "linkedin_url",
    "salary",
    "location",
    "follow_up_date",
}

JOB_TEXT_FIELDS = (
    "company",
    "role",
    "applied_date",
    "stage_updated_at",
    "interview_date",
    "assessment_date",
    "application_deadline",
    "badges",
    "notes",
    "job_url",
    "company_url",
    "company_address",
    "linkedin_url",
    "salary",
    "location",
    "work_arrangement",
    "source",
    "follow_up_date",
    "reminder_note",
    "rejection_reason",
    "rejection_notes",
    "interview_research",
    "interview_questions",
    "interview_answers",
    "interview_talking_points",
)

JOB_FIELD_LIMITS = {
    "company": 180,
    "role": 180,
    "applied_date": 80,
    "stage_updated_at": 80,
    "interview_date": 80,
    "assessment_date": 80,
    "application_deadline": 80,
    "badges": 500,
    "job_url": 500,
    "company_url": 500,
    "company_address": 500,
    "linkedin_url": 500,
    "salary": 120,
    "location": 180,
    "work_arrangement": 40,
    "source": 120,
    "follow_up_date": 80,
    "rejection_reason": 120,
}

JOB_DATE_FIELDS = {
    "applied_date",
    "stage_updated_at",
    "interview_date",
    "assessment_date",
    "application_deadline",
    "follow_up_date",
}

JOB_REJECTION_REASONS = (
    "Role filled or hiring paused",
    "Experience mismatch",
    "Skills mismatch",
    "Assessment result",
    "Interview result",
    "Location or working arrangement",
    "Salary or availability",
    "Eligibility or right to work",
    "Withdrew application",
    "No reason given",
    "Other",
)

JOB_WORK_ARRANGEMENTS = (
    ("", "Not recorded"),
    ("Remote", "Remote"),
    ("Hybrid", "Hybrid"),
    ("Office", "Office-based"),
    ("Flexible", "Flexible"),
)
JOB_WORK_ARRANGEMENT_VALUES = {value for value, _label in JOB_WORK_ARRANGEMENTS}
JOB_COOLING_OFF_DAYS = 30

RESUME_PRESET_TARGET = "resume_preset"
RESUME_PRESET_FIELDS = (
    "label",
    "header_subtitle",
    "target_role",
    "resume_keywords",
    "resume_summary",
    "company_details",
    "resume_conclusion",
)

DASHBOARD_SECTION_ICONS = {
    "profile": "fa-user",
    "experience": "fa-briefcase",
    "education": "fa-graduation-cap",
    "skills": "fa-code",
    "projects": "fa-folder-open",
    "certificates": "fa-award",
}
