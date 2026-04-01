import re

from flask import Blueprint, current_app, render_template, request

contact_bp = Blueprint("contact", __name__)

_NEWLINE_RE = re.compile(r"[\r\n]")


def _sanitise(value: str) -> str:
    """Strip newlines to prevent log injection."""
    return _NEWLINE_RE.sub(" ", value)


@contact_bp.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        return render_template("partials/contact_error.html"), 422

    current_app.logger.info("----- NEW MESSAGE -----")
    current_app.logger.info("From: %s <%s>", _sanitise(name), _sanitise(email))
    current_app.logger.info("Subject: %s", _sanitise(subject))
    current_app.logger.info("Message: %s", _sanitise(message))
    current_app.logger.info("-----------------------")

    return render_template("partials/contact_success.html", name=_sanitise(name))
