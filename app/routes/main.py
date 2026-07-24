from flask import Blueprint, current_app, g, render_template

from app.authentication import login_required

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.get("/terms")
def terms():
    return render_template("terms.html")


@main_bp.get("/privacy")
def privacy():
    return render_template("privacy.html")


@main_bp.get("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        current_user=g.current_user,
        maps_javascript_api_key=current_app.config.get(
            "MAPS_JAVASCRIPT_API_KEY"
        ),
        google_map_id=current_app.config.get(
            "GOOGLE_MAP_ID"
        ),
    )