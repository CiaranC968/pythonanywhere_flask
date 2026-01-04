from flask import Blueprint, request, current_app, render_template

contact_bp = Blueprint("contact", __name__)

@contact_bp.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name")
    email = request.form.get("email")
    subject = request.form.get("subject")
    message = request.form.get("message")

    if not name or not email or not message:
        return render_template("partials/contact_error.html"), 200

    current_app.logger.info("----- NEW MESSAGE -----")
    current_app.logger.info(f"From: {name} <{email}>")
    current_app.logger.info(f"Subject: {subject}")
    current_app.logger.info(f"Message: {message}")
    current_app.logger.info("-----------------------")

    return render_template(
        "partials/contact_success.html",
        name=name
    )
#To be completed