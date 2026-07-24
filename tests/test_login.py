from app.extensions import db
from app.models import User


def create_google_user(
    *,
    email="simon@example.com",
    display_name="Simon Lartey",
    google_sub="google-user-123",
    avatar_url=None,
):
    user = User(
        email=email,
        display_name=display_name,
        google_sub=google_sub,
        avatar_url=avatar_url,
    )

    db.session.add(user)
    db.session.commit()

    return user.id


def test_login_page_contains_google_sign_in(client):
    response = client.get("/login")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "Continue with Google" in html
    assert 'name="email"' not in html
    assert 'name="password"' not in html
    assert "or continue with email" not in html


def test_password_login_is_not_available(client):
    response = client.post(
        "/login",
        data={
            "email": "simon@example.com",
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 405


def test_signup_redirects_to_login(client):
    response = client.get(
        "/signup",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_password_signup_is_not_available(client):
    response = client.post(
        "/signup",
        data={
            "display_name": "Simon Lartey",
            "email": "simon@example.com",
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 405


def test_dashboard_requires_authentication(client):
    response = client.get(
        "/dashboard",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_authenticated_user_can_access_dashboard(client, app):
    with app.app_context():
        user_id = create_google_user()

    with client.session_transaction() as session:
        session["user_id"] = user_id

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Simon Lartey" in response.data
    assert b"simon@example.com" in response.data


def test_dashboard_uses_branded_initials_when_avatar_exists(
    client,
    app,
):
    avatar_url = "https://example.com/avatar.jpg"

    with app.app_context():
        user_id = create_google_user(
            display_name="Simon Lartey",
            avatar_url=avatar_url,
        )

    with client.session_transaction() as session:
        session["user_id"] = user_id

    response = client.get("/dashboard")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "SL" in html
    assert avatar_url not in html
    assert "profile-avatar-image" not in html


def test_dashboard_uses_initials_without_profile_photo(client, app):
    with app.app_context():
        user_id = create_google_user(
            display_name="Simon Lartey",
            avatar_url=None,
        )

    with client.session_transaction() as session:
        session["user_id"] = user_id

    response = client.get("/dashboard")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "SL" in html
    assert "Simon Lartey" in html
    assert "simon@example.com" in html


def test_dashboard_contains_account_menu(client, app):
    with app.app_context():
        user_id = create_google_user(
            display_name="Simon Lartey",
        )

    with client.session_transaction() as session:
        session["user_id"] = user_id

    response = client.get("/dashboard")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "data-profile-menu-trigger" in html
    assert "data-profile-menu-popover" in html
    assert "Signed in as" in html
    assert "Sign out" in html
    assert 'action="/logout"' in html
    assert 'method="post"' in html


def test_invalid_user_session_is_cleared(client):
    with client.session_transaction() as session:
        session["user_id"] = 999_999

    response = client.get(
        "/dashboard",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    with client.session_transaction() as session:
        assert "user_id" not in session


def test_logout_clears_session(client, app):
    with app.app_context():
        user_id = create_google_user()

    with client.session_transaction() as session:
        session["user_id"] = user_id

    response = client.post(
        "/logout",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    with client.session_transaction() as session:
        assert "user_id" not in session