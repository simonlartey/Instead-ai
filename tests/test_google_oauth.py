from unittest.mock import Mock

from flask import session
from flask_dance.consumer import oauth_authorized, oauth_error
from requests import RequestException

from app.extensions import db
from app.models import User


class FakeResponse:
    def __init__(
        self,
        *,
        ok=True,
        status_code=200,
        payload=None,
    ):
        self.ok = ok
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def get_google_blueprint(app):
    return app.blueprints["google"]


def send_authorized_signal(app, token, response):
    google_blueprint = get_google_blueprint(app)
    google_blueprint.session.get = Mock(return_value=response)

    with app.test_request_context("/login/google/authorized"):
        results = oauth_authorized.send(
            google_blueprint,
            token=token,
        )

        assert results

        redirect_response = results[0][1]
        session_data = dict(session)

        return redirect_response, session_data


def test_google_callback_creates_session(app):
    response = FakeResponse(
        payload={
            "sub": "google-user-123",
            "email": "simon@example.com",
            "email_verified": True,
            "name": "Simon Lartey",
            "picture": "https://example.com/avatar.jpg",
        }
    )

    result, session_data = send_authorized_signal(
        app,
        token={"access_token": "token"},
        response=response,
    )

    assert result.status_code == 302
    assert result.headers["Location"].endswith("/dashboard")
    assert "user_id" in session_data
    assert session_data["user_id"] is not None

    with app.app_context():
        user = db.session.execute(
            db.select(User).where(
                User.google_sub == "google-user-123"
            )
        ).scalar_one()

        assert user.email == "simon@example.com"


def test_google_callback_rejects_missing_token(app):
    result, _ = send_authorized_signal(
        app,
        token=None,
        response=FakeResponse(),
    )

    assert result.status_code == 302
    assert "oauth_error=missing_token" in result.headers["Location"]


def test_google_callback_handles_profile_request_failure(app):
    result, _ = send_authorized_signal(
        app,
        token={"access_token": "token"},
        response=FakeResponse(
            ok=False,
            status_code=500,
        ),
    )

    assert result.status_code == 302
    assert "oauth_error=profile_request" in result.headers["Location"]


def test_google_callback_handles_network_failure(app):
    google_blueprint = get_google_blueprint(app)
    google_blueprint.session.get = Mock(side_effect=RequestException())

    with app.test_request_context("/login/google/authorized"):
        results = oauth_authorized.send(
            google_blueprint,
            token={"access_token": "token"},
        )

        assert results

        result = results[0][1]

    assert result.status_code == 302
    assert "oauth_error=network" in result.headers["Location"]


def test_google_callback_handles_invalid_profile(app):
    result, _ = send_authorized_signal(
        app,
        token={"access_token": "token"},
        response=FakeResponse(
            payload={
                "sub": "",
                "email": "",
                "email_verified": False,
            }
        ),
    )

    assert result.status_code == 302
    assert "oauth_error=account_linking" in result.headers["Location"]


def test_google_oauth_error_redirects_to_login(app):
    google_blueprint = get_google_blueprint(app)

    with app.test_request_context("/login/google/authorized"):
        results = oauth_error.send(
            google_blueprint,
            error="access_denied",
            error_description="The user denied access.",
            error_uri=None,
        )

        assert results
        response = results[0][1]

        assert response.status_code == 302
        assert "oauth_error=authorization" in response.headers["Location"]


def test_google_callback_without_oauth_parameters_is_rejected(client):
    response = client.get("/login/google/authorized")

    assert response.status_code == 400
    assert b"Invalid OAuth callback request" in response.data
    assert response.headers["X-Robots-Tag"] == "noindex, nofollow"


def test_google_callback_with_code_is_not_blocked_by_guard(
    client,
    app,
    monkeypatch,
):
    monkeypatch.setitem(
        app.view_functions,
        "google.authorized",
        lambda: "OAuth callback reached.",
    )

    response = client.get(
        "/login/google/authorized",
        query_string={"code": "test-code", "state": "test-state"},
    )

    assert response.status_code != 400
