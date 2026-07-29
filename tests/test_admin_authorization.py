from flask import Blueprint, jsonify

from app.authentication import admin_api_required
from app.extensions import db
from app.models import User


def create_user(
    app,
    *,
    email: str,
) -> int:
    with app.app_context():
        user = User(
            email=email,
            display_name="Test User",
            google_sub=f"google-{email}",
            avatar_url=None,
        )

        db.session.add(user)
        db.session.commit()

        return user.id


def authenticate_client(
    client,
    *,
    user_id: int,
) -> None:
    with client.session_transaction() as session:
        session["user_id"] = user_id


def register_admin_test_route(app) -> None:
    blueprint = Blueprint(
        "admin_authorization_test",
        __name__,
    )

    @blueprint.get("/test/admin-only")
    @admin_api_required
    def admin_only():
        return jsonify(
            {
                "message": "Admin access granted.",
            }
        )

    app.register_blueprint(blueprint)


def test_admin_api_rejects_unauthenticated_user(
    app,
    client,
):
    register_admin_test_route(app)

    response = client.get("/test/admin-only")

    assert response.status_code == 401
    assert response.get_json() == {
        "error": {
            "code": "authentication_required",
            "message": (
                "You must sign in to access "
                "deal moderation."
            ),
        }
    }


def test_admin_api_rejects_signed_in_non_admin(
    app,
    client,
):
    register_admin_test_route(app)

    app.config["ADMIN_EMAILS"] = {
        "admin@example.com",
    }

    user_id = create_user(
        app,
        email="student@example.com",
    )

    authenticate_client(
        client,
        user_id=user_id,
    )

    response = client.get("/test/admin-only")

    assert response.status_code == 403
    assert response.get_json() == {
        "error": {
            "code": "admin_access_required",
            "message": (
                "You do not have permission to "
                "moderate student deals."
            ),
        }
    }


def test_admin_api_allows_configured_admin(
    app,
    client,
):
    register_admin_test_route(app)

    app.config["ADMIN_EMAILS"] = {
        "admin@example.com",
    }

    user_id = create_user(
        app,
        email="admin@example.com",
    )

    authenticate_client(
        client,
        user_id=user_id,
    )

    response = client.get("/test/admin-only")

    assert response.status_code == 200
    assert response.get_json() == {
        "message": "Admin access granted.",
    }


def test_admin_email_comparison_is_case_insensitive(
    app,
    client,
):
    register_admin_test_route(app)

    app.config["ADMIN_EMAILS"] = {
        "ADMIN@EXAMPLE.COM",
    }

    user_id = create_user(
        app,
        email="admin@example.com",
    )

    authenticate_client(
        client,
        user_id=user_id,
    )

    response = client.get("/test/admin-only")

    assert response.status_code == 200


def test_admin_api_denies_access_when_no_admins_configured(
    app,
    client,
):
    register_admin_test_route(app)

    app.config["ADMIN_EMAILS"] = frozenset()

    user_id = create_user(
        app,
        email="admin@example.com",
    )

    authenticate_client(
        client,
        user_id=user_id,
    )

    response = client.get("/test/admin-only")

    assert response.status_code == 403
