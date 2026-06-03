from io import BytesIO
from functools import lru_cache
from datetime import datetime
import os
import re
import unicodedata

from flask import Blueprint, abort, make_response

from portfolio_data import get_portfolio, get_profile

cv_bp = Blueprint("cv", __name__)
DEFAULT_PDF_SECTIONS = ("experience", "skills", "education", "certificates")


@cv_bp.route("/get-cv")
def get_cv():
    from flask import request
    
    theme_color = request.args.get("theme", "burgundy").strip()
    sections_param = request.args.get("sections")
    header_subtitle = request.args.get("subtitle", "").strip()

    if sections_param:
        include_sections = [s.strip() for s in sections_param.split(",") if s.strip()]
    else:
        include_sections = list(DEFAULT_PDF_SECTIONS)

    resume_options = {
        "theme_color": theme_color,
        "header_subtitle": header_subtitle,
    }

    try:
        pdf_bytes = build_cv_pdf(
            profile=get_profile(),
            portfolio=get_portfolio(),
            include_sections=include_sections,
            resume_options=resume_options,
        )
    except ImportError:
        abort(500, description="Install reportlab from requirements.txt to generate PDFs.")

    profile = get_profile()
    filename = f"{_safe_filename(profile.full_name)}_CV.pdf"
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    response.headers["Cache-Control"] = "no-store"
    return response


def build_cv_pdf(profile=None, portfolio=None, include_sections=None, resume_options=None):
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas

    profile = profile or get_profile()
    portfolio = portfolio or get_portfolio()
    include_sections = set(DEFAULT_PDF_SECTIONS if include_sections is None else include_sections)
    resume_options = resume_options or {}
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    color_theme = resume_options.get("theme_color", "burgundy").strip().lower()
    
    palettes = {
        "burgundy": {
            "accent": "#7a1f3d",
            "heading": "#6b2418",
            "soft": "#eee8d8"
        },
        "yellow": {
            "accent": "#b45309",
            "heading": "#1a1815",
            "soft": "#fef9c3"
        },
        "blue": {
            "accent": "#1d4ed8",
            "heading": "#0f172a",
            "soft": "#dbeafe"
        },
        "green": {
            "accent": "#047857",
            "heading": "#111827",
            "soft": "#d1fae5"
        },
        "slate": {
            "accent": "#475569",
            "heading": "#0f172a",
            "soft": "#f1f5f9"
        }
    }
    
    selected_palette = palettes.get(color_theme, palettes["burgundy"])

    theme = {
        "ink": colors.HexColor("#28282b"),
        "muted": colors.HexColor("#646464"),
        "line": colors.HexColor("#d9d4cc"),
        "accent": colors.HexColor(selected_palette["accent"]),
        "heading": colors.HexColor(selected_palette["heading"]),
        "soft": colors.HexColor(selected_palette["soft"]),
        "pill": colors.HexColor("#f4f1ec"),
        "white": colors.white,
        "globe_blue": colors.HexColor("#2ba4d6"),
        "globe_green": colors.HexColor("#5aa36a"),
        "globe_gold": colors.HexColor("#b99b45"),
    }
    ctx = {
        "pdf": pdf,
        "image_reader": ImageReader,
        "string_width": stringWidth,
        "theme": theme,
        "margin": 27,
        "left_x": 27,
        "left_w": 316,
        "right_x": 378,
        "right_w": 195,
        "bottom": 32,
        "header_subtitle": _text(resume_options.get("header_subtitle", "")),
    }

    pdf.setFillColor(theme["white"])
    pdf.rect(0, 0, width, height, fill=1, stroke=0)

    _draw_header(ctx, profile, width, height)
    section_top = height - 136
    if _has_resume_target(resume_options):
        section_top = _draw_resume_target(ctx, resume_options, section_top, width)

    left_y = section_top
    if "experience" in include_sections and portfolio.get("experience"):
        left_y = _draw_experience(ctx, portfolio.get("experience", []), left_y)
    if "projects" in include_sections and portfolio.get("projects"):
        left_y = _draw_projects(ctx, portfolio.get("projects", []), left_y - 8)
    if "certificates" in include_sections and portfolio.get("certificates"):
        _draw_certificates(ctx, portfolio.get("certificates", []), left_y - 8)

    right_y = section_top
    if "skills" in include_sections and portfolio.get("skills"):
        right_y = _draw_skills(ctx, portfolio.get("skills", []), right_y)
    if "education" in include_sections and portfolio.get("education"):
        _draw_education(ctx, portfolio.get("education", []), right_y - 12)

    pdf.setTitle(resume_options.get("document_title") or f"{profile.full_name} CV")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def build_resume_letter_pdf(profile=None, resume_options=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas

    profile = profile or get_profile()
    resume_options = resume_options or {}
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    theme = {
        "background": colors.white,
        "ink": colors.HexColor("#242424"),
        "muted": colors.HexColor("#424242"),
        "quiet": colors.HexColor("#6f6f6f"),
        "line": colors.HexColor("#d6d0c8"),
        "accent": colors.HexColor("#8a233c"),
    }
    ctx = {
        "pdf": pdf,
        "image_reader": ImageReader,
        "string_width": stringWidth,
        "theme": theme,
        "left_x": 38,
        "right_x": width - 38,
        "bottom": 38,
    }

    pdf.setFillColor(theme["background"])
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    _draw_letter_header(ctx, profile, height)
    y = height - 166
    y = _draw_letter_section(ctx, "Introduction", y, _letter_intro(resume_options))
    y = _draw_letter_section(ctx, "What I Bring to the Team", y - 12, _letter_bullets(resume_options), bullets=True)
    _draw_letter_section(ctx, "Conclusion", y - 12, _letter_conclusion(resume_options, profile))
    _draw_letter_footer(ctx, profile, width)

    company = _text(resume_options.get("company_name", ""))
    pdf.setTitle(" - ".join(part for part in [profile.full_name, company, "Cover Letter"] if part))
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _draw_letter_header(ctx, profile, height):
    pdf = ctx["pdf"]
    theme = ctx["theme"]
    name_parts = _text(profile.full_name).split()
    first_name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else _text(profile.full_name)
    last_name = name_parts[-1] if len(name_parts) > 1 else ""
    name_y = height - 70
    pdf.setFillColor(theme["muted"])
    pdf.setFont("Helvetica", 25)
    first_width = ctx["string_width"](first_name + " ", "Helvetica", 25)
    name_x = ctx["left_x"]
    pdf.drawString(name_x, name_y, first_name)
    pdf.setFillColor(theme["ink"])
    pdf.setFont("Helvetica-Bold", 25)
    pdf.drawString(name_x + first_width, name_y, last_name)

    contact = " | ".join(part for part in [_text(profile.phone), _text(profile.email)] if part)
    if contact:
        pdf.setFillColor(theme["quiet"])
        pdf.setFont("Helvetica-Bold", 5.7)
        pdf.drawString(name_x, name_y - 12, contact)


def _draw_letter_section(ctx, title, y, content, bullets=False):
    pdf = ctx["pdf"]
    theme = ctx["theme"]
    x = ctx["left_x"]
    width = ctx["right_x"] - ctx["left_x"]

    pdf.setFillColor(theme["accent"])
    pdf.setFont("Helvetica-Bold", 13)
    title_width = ctx["string_width"](title, "Helvetica-Bold", 13)
    pdf.drawString(x, y, title)
    pdf.setStrokeColor(theme["line"])
    pdf.setLineWidth(0.7)
    pdf.line(x + title_width + 4, y + 4, ctx["right_x"], y + 4)
    y -= 23

    if bullets:
        pdf.setFillColor(theme["muted"])
        pdf.setFont("Helvetica", 7.6)
        for bullet in content:
            lines = _wrap(_text(bullet), width - 30, "Helvetica", 7.6, ctx["string_width"], max_lines=3)
            for line_index, line in enumerate(lines):
                if line_index == 0:
                    pdf.circle(x + 22, y + 2.2, 1.0, fill=1, stroke=0)
                pdf.drawString(x + 30, y, line)
                y -= 10.8
            y -= 1.2
        return y

    pdf.setFillColor(theme["muted"])
    pdf.setFont("Helvetica", 7.9)
    for paragraph in _letter_paragraphs(content):
        for line in _wrap(paragraph, width, "Helvetica", 7.9, ctx["string_width"], max_lines=8):
            pdf.drawString(x, y, line)
            y -= 10.2
        y -= 6
    return y


def _draw_letter_footer(ctx, profile, width):
    pdf = ctx["pdf"]
    theme = ctx["theme"]
    now = datetime.now()
    date_text = f"{now.strftime('%B')} {now.day}, {now.year}"
    pdf.setFillColor(theme["muted"])
    pdf.setFont("Helvetica-Bold", 6)
    pdf.drawString(ctx["left_x"], 38, date_text)
    pdf.drawCentredString(width / 2, 38, f"{_caps(profile.full_name)} - COVER LETTER")


def _letter_intro(options):
    summary = _text(options.get("summary", ""))
    if summary:
        if summary.lower().startswith("dear "):
            return summary
        return f"Dear Hiring Manager,\n\n{summary}"

    role = _text(options.get("target_role", "")) or "the advertised role"
    company = _text(options.get("company_name", "")) or "your team"
    return (
        "Dear Hiring Manager,\n\n"
        f"I am writing to apply for {role} at {company}. "
        "I am keen to bring my software development experience, academic grounding, "
        "and practical problem-solving approach to a team building reliable digital products."
    )


def _letter_bullets(options):
    details = _custom_lines(options.get("details", ""))
    if details:
        return details[:6]

    keywords = _custom_keywords(options.get("keywords", ""))
    if keywords:
        return [f"Focused experience across {', '.join(keywords[:6])}."]

    return [
        "Currently studying BSc (Hons) Computing and IT with the Open University.",
        "Practical experience building Python, Flask, SQL, and React-based software.",
        "Comfortable working with Agile workflows, documentation, testing, and team communication.",
        "Strong customer-facing background with a calm, reliable approach to problem solving.",
    ]


def _letter_conclusion(options, profile):
    conclusion = _text(options.get("conclusion", ""))
    if conclusion:
        return conclusion

    company = _text(options.get("company_name", "")) or "your organisation"
    return (
        "I am enthusiastic about the opportunity to support your engineering teams, "
        "learn from experienced developers, and contribute to high-quality software. "
        f"Thank you for considering my application - I would welcome the chance to discuss how I can support {company}.\n\n"
        "Yours sincerely,\n\n"
        f"{_text(profile.full_name)}"
    )


def _letter_paragraphs(value):
    return [paragraph.strip() for paragraph in str(value or "").splitlines() if paragraph.strip()]


def _profile_image(profile):
    image_path = _profile_image_path(profile)
    if not image_path:
        return None
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None

    size = 256
    try:
        with Image.open(image_path).convert("RGBA") as image:
            side = min(image.size)
            left = (image.width - side) // 2
            top = (image.height - side) // 2
            image = image.crop((left, top, left + side, top + side)).resize((size, size))
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
            image.putalpha(mask)
            output = BytesIO()
            image.save(output, format="PNG")
            return output.getvalue()
    except OSError:
        return None


def _profile_image_path(profile):
    value = _text(getattr(profile, "profile_image", ""))
    root = os.path.dirname(os.path.dirname(__file__))
    candidates = []
    if value:
        if value.startswith("/static/"):
            candidates.append(os.path.join(root, value.lstrip("/")))
        elif os.path.isabs(value):
            candidates.append(value)
        else:
            candidates.extend(
                [
                    os.path.join(root, "static", "images", value),
                    os.path.join(root, "static", value),
                ]
            )
    candidates.append(os.path.join(root, "static", "images", "about.png"))
    return next((path for path in candidates if os.path.exists(path)), "")


def _draw_header(ctx, profile, width, height):
    pdf = ctx["pdf"]
    theme = ctx["theme"]
    x = ctx["left_x"]
    y = height - 53

    pdf.setFillColor(theme["ink"])
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawString(x, y, _caps(profile.full_name))

    y -= 18
    pdf.setFillColor(theme["accent"])
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, _text(ctx.get("header_subtitle") or profile.cv_subtitle or profile.title))

    y -= 14
    contact_items = [
        ("@", profile.email),
        ("tel", profile.phone),
        ("mail", profile.address),
        ("pin", profile.location),
        ("in", _short_url(profile.linkedin_url)),
        ("git", _short_url(profile.github_url)),
        ("web", profile.website_url),
    ]
    col_x = [x, x + 117, x + 240]
    for index, (label, value) in enumerate((item for item in contact_items if item[1])):
        row = index // 3
        col = index % 3
        _draw_contact(ctx, col_x[col], y - row * 9, label, value)

    _draw_globe_badge(ctx, width - 74, height - 78)


def _has_resume_target(options):
    fields = ("company_name", "target_role", "summary", "details", "keywords")
    return any(_text(options.get(field, "")) for field in fields)


def _draw_resume_target(ctx, options, y, page_width):
    full_width = page_width - (ctx["left_x"] * 2)
    y = _section_title(ctx, "TARGETED RESUME", ctx["left_x"], y, full_width)
    pdf = ctx["pdf"]
    theme = ctx["theme"]

    company = _text(options.get("company_name", ""))
    role = _text(options.get("target_role", ""))
    headline = " | ".join(part for part in [role, company] if part)
    if headline:
        pdf.setFillColor(theme["ink"])
        pdf.setFont("Helvetica-Bold", 10.2)
        pdf.drawString(ctx["left_x"], y, _truncate(headline, 86))
        y -= 10.5

    summary = _text(options.get("summary", ""))
    if summary:
        pdf.setFillColor(theme["muted"])
        pdf.setFont("Helvetica", 7.8)
        for line in _wrap(summary, full_width, "Helvetica", 7.8, ctx["string_width"], max_lines=3):
            pdf.drawString(ctx["left_x"], y, line)
            y -= 8.7

    details = _custom_lines(options.get("details", ""))[:4]
    for detail in details:
        for line_index, line in enumerate(_wrap(detail, full_width - 12, "Helvetica", 7.6, ctx["string_width"], max_lines=2)):
            pdf.setFillColor(theme["muted"])
            pdf.setFont("Helvetica", 7.6)
            if line_index == 0:
                pdf.circle(ctx["left_x"] + 2, y + 2.1, 1.15, fill=1, stroke=0)
            pdf.drawString(ctx["left_x"] + 9, y, line)
            y -= 8.3

    keywords = _custom_keywords(options.get("keywords", ""))[:12]
    if keywords:
        y = _draw_pills(ctx, keywords, ctx["left_x"], y - 1, full_width, font_size=7, max_y=22)

    return y - 8


def _draw_contact(ctx, x, y, label, value):
    pdf = ctx["pdf"]
    theme = ctx["theme"]
    _draw_contact_icon(ctx, label, x + 3, y + 2.6)
    pdf.setFont("Helvetica-Bold", 7.3)
    pdf.setFillColor(theme["ink"])
    pdf.drawString(x + 12, y, _truncate(_text(value), 31))


def _draw_contact_icon(ctx, label, x, y):
    pdf = ctx["pdf"]
    theme = ctx["theme"]
    icon_size = 7.6

    if label != "@":
        icon = _contact_icon_image(label, _hex_colour(theme["accent"]))
        if icon:
            pdf.drawImage(
                ctx["image_reader"](BytesIO(icon)),
                x - icon_size / 2,
                y - icon_size / 2,
                width=icon_size,
                height=icon_size,
                mask="auto",
            )
            return

    pdf.saveState()
    pdf.setStrokeColor(theme["accent"])
    pdf.setFillColor(theme["accent"])
    pdf.setLineWidth(0.7)

    if label == "@":
        pdf.circle(x, y, 3.0, fill=0, stroke=1)
        pdf.circle(x + 0.7, y, 1.1, fill=0, stroke=1)
        pdf.line(x + 2.0, y - 0.6, x + 4.2, y + 0.8)
    elif label == "tel":
        pdf.roundRect(x - 2.3, y - 3.0, 4.8, 6.0, 1.2, fill=0, stroke=1)
        pdf.circle(x, y - 2.0, 0.45, fill=1, stroke=0)
    elif label == "mail":
        pdf.rect(x - 3.4, y - 2.4, 6.8, 4.8, fill=0, stroke=1)
        pdf.line(x - 3.4, y + 2.4, x, y - 0.4)
        pdf.line(x + 3.4, y + 2.4, x, y - 0.4)
    elif label == "pin":
        pdf.circle(x, y + 0.8, 2.3, fill=0, stroke=1)
        pdf.line(x - 1.6, y - 0.8, x, y - 3.7)
        pdf.line(x + 1.6, y - 0.8, x, y - 3.7)
    elif label == "web":
        pdf.circle(x, y, 3.1, fill=0, stroke=1)
        pdf.ellipse(x - 1.5, y - 3.1, x + 1.5, y + 3.1, fill=0, stroke=1)
        pdf.line(x - 3.1, y, x + 3.1, y)
    elif label == "git":
        pdf.circle(x, y, 2.9, fill=0, stroke=1)
        pdf.circle(x - 1.1, y + 0.6, 0.35, fill=1, stroke=0)
        pdf.circle(x + 1.1, y + 0.6, 0.35, fill=1, stroke=0)
        pdf.line(x - 1.4, y - 1.2, x + 1.4, y - 1.2)
    elif label == "in":
        pdf.rect(x - 3.0, y - 3.0, 6.0, 6.0, fill=0, stroke=1)
        pdf.line(x - 1.4, y - 1.8, x - 1.4, y + 0.8)
        pdf.circle(x - 1.4, y + 1.8, 0.35, fill=1, stroke=0)
        pdf.line(x + 0.2, y - 1.8, x + 0.2, y + 0.9)
        pdf.line(x + 0.2, y + 0.9, x + 1.6, y - 1.8)
    else:
        pdf.circle(x, y, 2.2, fill=1, stroke=0)

    pdf.restoreState()


@lru_cache(maxsize=16)
def _contact_icon_image(label, colour):
    glyphs = {
        "tel": "\ue98a",
        "mail": "\ue066",
        "pin": "\ue942",
        "web": "\ue0b2",
        "git": "\ueae0",
        "in": "\ueaf9",
    }
    glyph = glyphs.get(label)
    font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "fonts", "icomoon", "icomoon.ttf")
    if not glyph or not os.path.exists(font_path):
        return None

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    size = 96
    font = ImageFont.truetype(font_path, 72)
    image = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0, 0), glyph, font=font)
    x = (size - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = (size - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((x, y), glyph, font=font, fill=colour)

    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output.getvalue()


def _hex_colour(colour):
    red, green, blue = colour.red, colour.green, colour.blue
    return tuple(int(channel * 255) for channel in (red, green, blue)) + (255,)


def _draw_globe_badge(ctx, x, y):
    pdf = ctx["pdf"]
    theme = ctx["theme"]
    pdf.setFillColor(theme["soft"])
    pdf.circle(x, y, 40, fill=1, stroke=0)

    globe_x = x
    globe_y = y + 3
    pdf.setFillColor(theme["globe_blue"])
    pdf.circle(globe_x, globe_y, 22, fill=1, stroke=0)

    pdf.setStrokeColor(theme["white"])
    pdf.setLineWidth(0.6)
    pdf.ellipse(globe_x - 11, globe_y - 21, globe_x + 11, globe_y + 21, stroke=1, fill=0)
    pdf.ellipse(globe_x - 19, globe_y - 12, globe_x + 19, globe_y + 12, stroke=1, fill=0)
    pdf.line(globe_x - 22, globe_y, globe_x + 22, globe_y)
    pdf.line(globe_x, globe_y - 22, globe_x, globe_y + 22)

    pdf.setFillColor(theme["globe_green"])
    pdf.roundRect(globe_x - 15, globe_y + 4, 14, 7, 3, fill=1, stroke=0)
    pdf.roundRect(globe_x + 1, globe_y - 8, 13, 8, 3, fill=1, stroke=0)
    pdf.roundRect(globe_x - 6, globe_y - 15, 8, 5, 2, fill=1, stroke=0)

    pdf.setStrokeColor(theme["globe_gold"])
    pdf.setLineWidth(2.2)
    pdf.arc(globe_x - 25, globe_y - 25, globe_x + 25, globe_y + 25, 300, 112)
    pdf.line(globe_x, globe_y - 23, globe_x, globe_y - 34)
    pdf.line(globe_x - 13, globe_y - 34, globe_x + 13, globe_y - 34)


def _draw_experience(ctx, experience, y):
    y = _section_title(ctx, "EXPERIENCE", ctx["left_x"], y, ctx["left_w"])
    for job in _experience_jobs(experience)[:5]:
        if y < ctx["bottom"] + 74:
            break
        y = _job_block(ctx, job, ctx["left_x"], y, ctx["left_w"])
        if y > ctx["bottom"] + 74:
            _dotted_rule(ctx, ctx["left_x"], y + 4, ctx["left_w"])
            y -= 7
    return y


def _job_block(ctx, job, x, y, width):
    pdf = ctx["pdf"]
    theme = ctx["theme"]

    pdf.setFillColor(theme["ink"])
    pdf.setFont("Helvetica", 10.6)
    pdf.drawString(x, y, _truncate(job["role"], 43))
    y -= 11

    pdf.setFillColor(theme["accent"])
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(x, y, _truncate(job["company"], 36))
    y -= 11

    pdf.setFillColor(theme["muted"])
    pdf.setFont("Helvetica", 7.4)
    meta = "   ".join(item for item in [job["period"], job["location"]] if item)
    pdf.drawString(x, y, _truncate(meta, 70))
    y -= 9

    for bullet in job["bullets"][:4]:
        lines = _wrap(_text(bullet), width - 13, "Helvetica", 8.0, ctx["string_width"], max_lines=2)
        for line_index, line in enumerate(lines):
            if y < ctx["bottom"] + 42:
                return y
            pdf.setFillColor(theme["muted"])
            pdf.setFont("Helvetica", 8.0)
            if line_index == 0:
                pdf.circle(x + 2, y + 2.2, 1.25, fill=1, stroke=0)
            pdf.drawString(x + 9, y, line)
            y -= 8.8
    return y - 2


def _draw_skills(ctx, skills, y):
    y = _section_title(ctx, "SKILLS", ctx["right_x"], y, ctx["right_w"])
    tags = []
    for skill in skills:
        tags.extend(skill.tags or [])
        if skill.title and not skill.tags:
            tags.append(skill.title)

    seen = set()
    unique_tags = []
    for tag in tags:
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            unique_tags.append(tag)

    return _draw_pills(ctx, unique_tags[:14], ctx["right_x"], y, ctx["right_w"], font_size=8, max_y=62)


def _draw_projects(ctx, projects, y):
    if y < ctx["bottom"] + 55:
        return y

    y = _section_title(ctx, "PROJECTS", ctx["left_x"], y, ctx["left_w"])
    pdf = ctx["pdf"]
    theme = ctx["theme"]

    for project in projects[:3]:
        if y < ctx["bottom"] + 40:
            break

        pdf.setFillColor(theme["ink"])
        pdf.setFont("Helvetica", 10.1)
        pdf.drawString(ctx["left_x"], y, _truncate(project.title, 46))
        y -= 10

        if project.desc:
            pdf.setFillColor(theme["muted"])
            pdf.setFont("Helvetica", 7.7)
            for line in _wrap(_text(project.desc), ctx["left_w"], "Helvetica", 7.7, ctx["string_width"], max_lines=2):
                pdf.drawString(ctx["left_x"], y, line)
                y -= 8.4

        tags = (project.tags or [])[:5]
        if tags:
            y = _draw_pills(ctx, tags, ctx["left_x"], y - 1, ctx["left_w"], font_size=7, max_y=15)

        _dotted_rule(ctx, ctx["left_x"], y + 3, ctx["left_w"])
        y -= 8

    return y


def _draw_education(ctx, education, y):
    y = _section_title(ctx, "EDUCATION", ctx["right_x"], y, ctx["right_w"])
    pdf = ctx["pdf"]
    theme = ctx["theme"]

    for edu in education[:3]:
        if y < ctx["bottom"] + 55:
            break
        pdf.setFillColor(theme["ink"])
        pdf.setFont("Helvetica", 10.5)
        for line in _wrap(_text(edu.degree), ctx["right_w"], "Helvetica", 10.5, ctx["string_width"], max_lines=2):
            pdf.drawString(ctx["right_x"], y, line)
            y -= 10.5

        pdf.setFillColor(theme["accent"])
        pdf.setFont("Helvetica-Bold", 8.1)
        pdf.drawString(ctx["right_x"], y, _truncate(edu.university, 34))
        y -= 9.5

        pdf.setFillColor(theme["muted"])
        pdf.setFont("Helvetica", 7.6)
        if edu.year:
            pdf.drawString(ctx["right_x"], y, _text(edu.year))
            y -= 9.5

        for extra in _education_extras(edu):
            pdf.setFillColor(theme["muted"])
            pdf.setFont("Helvetica-Bold", 7.2)
            for line in _wrap(extra, ctx["right_w"], "Helvetica-Bold", 7.2, ctx["string_width"], max_lines=2):
                pdf.drawString(ctx["right_x"], y, line)
                y -= 8.2

        if edu.description:
            for line in _wrap(_text(edu.description), ctx["right_w"], "Helvetica", 7.4, ctx["string_width"], max_lines=2):
                pdf.drawString(ctx["right_x"], y, line)
                y -= 8.5

        stages = edu.stages or {}
        for stage_name, modules in stages.items():
            if y < ctx["bottom"] + 35:
                break
            pdf.setFillColor(theme["ink"])
            pdf.setFont("Helvetica-Bold", 8.2)
            pdf.drawString(ctx["right_x"], y, _text(stage_name))
            y -= 9
            labels = [
                f"{module.get('code', '').strip()}: {module.get('title', '').strip()}".strip(": ")
                for module in modules
            ]
            y = _draw_pills(ctx, labels[:4], ctx["right_x"], y, ctx["right_w"], font_size=7, max_y=35)
            y -= 1

        _dotted_rule(ctx, ctx["right_x"], y + 3, ctx["right_w"])
        y -= 10

    return y


def _draw_certificates(ctx, certificates, y):
    if y < ctx["bottom"] + 35:
        return y

    y = _section_title(ctx, "CERTIFICATES AND OTHER", ctx["left_x"], y, ctx["left_w"])
    pdf = ctx["pdf"]
    theme = ctx["theme"]
    pdf.setFillColor(theme["muted"])
    pdf.setFont("Helvetica-Bold", 7.8)

    for text in _certificate_lines(certificates)[:5]:
        for line in _wrap(_text(text), ctx["left_w"] - 9, "Helvetica-Bold", 7.8, ctx["string_width"], max_lines=2):
            if y < ctx["bottom"] + 10:
                return y
            pdf.circle(ctx["left_x"] + 2, y + 2.2, 1.25, fill=1, stroke=0)
            pdf.drawString(ctx["left_x"] + 9, y, line)
            y -= 8.4
    return y


def _section_title(ctx, title, x, y, width):
    pdf = ctx["pdf"]
    theme = ctx["theme"]
    pdf.setFillColor(theme["heading"])
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(x, y, title)
    y -= 5
    pdf.setStrokeColor(theme["heading"])
    pdf.setLineWidth(1.5)
    pdf.line(x, y, x + width, y)
    return y - 12


def _draw_pills(ctx, labels, x, y, width, font_size=8, max_y=45):
    pdf = ctx["pdf"]
    theme = ctx["theme"]
    cursor_x = x
    start_y = y
    row_h = font_size + 6.5

    for label in labels:
        if start_y - y > max_y:
            break
        label = _truncate(_text(label), 46)
        label_w = min(ctx["string_width"](label, "Helvetica-Bold", font_size), width)
        if cursor_x + label_w > x + width:
            cursor_x = x
            y -= row_h
            if start_y - y > max_y:
                break

        pdf.setFillColor(theme["muted"])
        pdf.setFont("Helvetica-Bold", font_size)
        pdf.drawString(cursor_x, y, label)
        cursor_x += label_w + 9

    return y - row_h


def _dotted_rule(ctx, x, y, width):
    pdf = ctx["pdf"]
    pdf.setStrokeColor(ctx["theme"]["line"])
    pdf.setDash(2, 3)
    pdf.setLineWidth(0.6)
    pdf.line(x, y, x + width, y)
    pdf.setDash()


def _experience_jobs(experience):
    jobs = []
    for exp in experience:
        if exp.timeline:
            for item in exp.timeline:
                jobs.append(
                    {
                        "role": item.get("role", exp.role),
                        "company": exp.company,
                        "period": item.get("period", exp.period),
                        "location": item.get("loc", exp.location),
                        "bullets": _split_bullets(item.get("desc", exp.brief)),
                    }
                )
        else:
            jobs.append(
                {
                    "role": exp.role,
                    "company": exp.company,
                    "period": exp.period,
                    "location": exp.location,
                    "bullets": (exp.details or [exp.brief])[:5],
                }
            )
    return sorted(jobs, key=lambda job: _period_sort_key(job["period"]))


def _period_sort_key(period):
    text = _text(period).lower()
    months = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    year = int(year_match.group(0)) if year_match else 9999
    month = 1
    for name, value in months.items():
        if re.search(rf"\b{name}\b", text):
            month = value
            break
    return year, month


def _split_bullets(value):
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", _text(value)) if part.strip()]
    return parts or [_text(value)]


def _custom_lines(value):
    return [
        re.sub(r"^[-*\u2022]\s*", "", line.strip())
        for line in str(value or "").splitlines()
        if line.strip()
    ]


def _custom_keywords(value):
    return [
        item.strip()
        for item in re.split(r"[\n,]+", str(value or ""))
        if item.strip()
    ]


def _education_extras(edu):
    extras = []
    for attr in ("status", "gpa"):
        value = _text(getattr(edu, attr, ""))
        if value:
            extras.append(value)

    total_credits = getattr(edu, "total_credits", None)
    if total_credits:
        extras.append(f"{total_credits} credits")

    modules_completed = getattr(edu, "modules_completed", None)
    if modules_completed:
        extras.append(f"{modules_completed} modules completed")

    return extras


def _certificate_lines(certificates):
    lines = []
    for cert in certificates:
        text = _text(cert.title)
        details = [value for value in [_text(getattr(cert, "issuer", "")), _text(getattr(cert, "date", ""))] if value]
        if details:
            text = f"{text} ({', '.join(details)})"
        if text:
            lines.append(text)
    return lines


def _wrap(text, width, font_name, font_size, string_width, max_lines=4):
    words = _text(text).split()
    if not words:
        return []

    lines = []
    current = []
    for word in words:
        candidate = " ".join(current + [word])
        if string_width(candidate, font_name, font_size) <= width:
            current.append(word)
            continue

        if current:
            lines.append(" ".join(current))
        current = [word]
        if len(lines) == max_lines:
            break

    if current and len(lines) < max_lines:
        lines.append(" ".join(current))

    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(".,;:") + "..."
    return lines


def _short_url(url):
    return re.sub(r"^https?://(www\.)?", "", url or "").rstrip("/")


def _truncate(value, limit):
    value = _text(value)
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."


def _text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _caps(value):
    return _text(value).upper()


def _safe_filename(value):
    value = unicodedata.normalize("NFKD", value or "portfolio").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
