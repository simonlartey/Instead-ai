from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login():
    return render_template(
        "login.html",
        oauth_error=request.args.get("oauth_error"),
    )


@auth_bp.get("/signup")
def signup():
    return redirect(url_for("auth.login"))


@auth_bp.post("/logout")
def logout():
    session.clear()

    return redirect(url_for("auth.login"))