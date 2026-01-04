import os
from flask import Blueprint, send_from_directory, abort, current_app, make_response

cv_bp = Blueprint("cv", __name__)

@cv_bp.route("/get-cv")
def get_cv():
    directory = os.path.join(current_app.root_path, "static", "docs")
    filename = "Ciaran_Cairns_CV.pdf"
    filepath = os.path.join(directory, filename)

    if not os.path.exists(filepath):
        abort(404)

    response = make_response(send_from_directory(directory, filename))
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response
