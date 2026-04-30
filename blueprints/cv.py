from io import BytesIO
from functools import lru_cache
import os
import re
import unicodedata

from flask import Blueprint, abort, make_response

from portfolio_data import get_portfolio, get_profile

cv_bp = Blueprint("cv", __name__)


@cv_bp.route("/get-cv")
def get_cv():
    try:
        pdf_bytes = build_cv_pdf()
    except ImportError:
        abort(500, description="Install reportlab from requirements.txt to generate PDFs.")

    profile = get_profile()
    filename = f"{_safe_filename(profile.full_name)}_CV.pdf"
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    response.headers["Cache-Control"] = "no-store"
    return response


def build_cv_pdf():
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas

    profile = get_profile()
    portfolio = get_portfolio()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    theme = {
        "ink": colors.HexColor("#28282b"),
        "muted": colors.HexColor("#646464"),
        "line": colors.HexColor("#d9d4cc"),
        "accent": colors.HexColor("#7a1f3d"),
        "heading": colors.HexColor("#6b2418"),
        "soft": colors.HexColor("#eee8d8"),
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
    }

    pdf.setFillColor(theme["white"])
    pdf.rect(0, 0, width, height, fill=1, stroke=0)

    _draw_header(ctx, profile, width, height)
    section_top = height - 136
    left_y = _draw_experience(ctx, portfolio["experience"], section_top)
    _draw_certificates(ctx, portfolio["certificates"], left_y - 8)
    right_y = _draw_skills(ctx, portfolio["skills"], section_top)
    _draw_education(ctx, portfolio["education"], right_y - 12)

    pdf.setTitle(f"{profile.full_name} CV")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


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
    pdf.drawString(x, y, _text(profile.cv_subtitle or profile.title))

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
        pill_w = min(ctx["string_width"](label, "Helvetica-Bold", font_size) + 9, width)
        if cursor_x + pill_w > x + width:
            cursor_x = x
            y -= row_h
            if start_y - y > max_y:
                break

        pdf.setStrokeColor(theme["line"])
        pdf.roundRect(cursor_x, y - 3, pill_w, font_size + 5.5, 3, fill=0, stroke=1)
        pdf.setFillColor(theme["muted"])
        pdf.setFont("Helvetica-Bold", font_size)
        pdf.drawString(cursor_x + 5, y, label)
        cursor_x += pill_w + 3

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
