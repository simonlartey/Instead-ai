from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flask import (
    current_app,
    g,
    jsonify,
    redirect,
    session,
    url_for,
)

from app.extensions import db
from app.models import User

ViewFunction = TypeVar(
    "ViewFunction",
    bound=Callable[..., Any],
)


def load_current_user() -> None:
    """Load the signed-in user into Flask's request context."""

    user_id = session.get("user_id")

    if user_id is None:
        g.current_user = None
        return

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()
        g.current_user = None
        return

    g.current_user = user


def login_required(view: ViewFunction) -> ViewFunction:
    """Require a signed-in user before running a route."""

    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any):
        if g.current_user is None:
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return cast(ViewFunction, wrapped_view)


def admin_api_required(
    view: ViewFunction,
) -> ViewFunction:
    """Require an authorized admin for an API route."""

    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any):
        current_user = g.current_user

        if current_user is None:
            return jsonify(
                {
                    "error": {
                        "code": "authentication_required",
                        "message": (
                            "You must sign in to access "
                            "deal moderation."
                        ),
                    }
                }
            ), 401

        admin_emails = {
            str(email).strip().lower()
            for email in current_app.config.get(
                "ADMIN_EMAILS",
                (),
            )
            if str(email).strip()
        }

        if current_user.email.lower() not in admin_emails:
            return jsonify(
                {
                    "error": {
                        "code": "admin_access_required",
                        "message": (
                            "You do not have permission to "
                            "moderate student deals."
                        ),
                    }
                }
            ), 403

        return view(*args, **kwargs)

    return cast(ViewFunction, wrapped_view)
