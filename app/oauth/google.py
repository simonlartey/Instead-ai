from flask import current_app, redirect, session, url_for
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.contrib.google import make_google_blueprint
from requests import RequestException

from app.services.auth_service import create_or_link_google_user


GOOGLE_USERINFO_URL = (
    "https://openidconnect.googleapis.com/v1/userinfo"
)


def create_google_blueprint():
    """Create and configure the Google OAuth blueprint."""

    google_blueprint = make_google_blueprint(
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        redirect_to="main.dashboard",
        reprompt_select_account=True,
    )

    @oauth_authorized.connect_via(google_blueprint)
    def handle_google_authorized(blueprint, token):
        if not token:
            return redirect(
                url_for("auth.login", oauth_error="missing_token")
            )

        try:
            response = blueprint.session.get(
                GOOGLE_USERINFO_URL,
                timeout=10,
            )
        except RequestException:
            current_app.logger.exception(
                "Failed to contact Google userinfo endpoint."
            )
            return redirect(
                url_for("auth.login", oauth_error="network")
            )

        if not response.ok:
            current_app.logger.warning(
                "Google profile request failed with status %s.",
                response.status_code,
            )
            return redirect(
                url_for("auth.login", oauth_error="profile_request")
            )

        profile = response.json()

        try:
            user = create_or_link_google_user(
                google_sub=profile.get("sub", ""),
                email=profile.get("email", ""),
                email_verified=bool(profile.get("email_verified")),
                display_name=profile.get("name", ""),
                avatar_url=profile.get("picture"),
            )
        except ValueError as error:
            current_app.logger.warning(
                "Google account linking failed: %s",
                error,
            )
            return redirect(
                url_for("auth.login", oauth_error="account_linking")
            )

        session.clear()
        session["user_id"] = user.id
        session.permanent = True

        return redirect(url_for("main.dashboard"))

    @oauth_error.connect_via(google_blueprint)
    def handle_google_error(
        blueprint,
        error,
        error_description=None,
        error_uri=None,
    ):
        current_app.logger.warning(
            "Google OAuth failed: %s — %s",
            error,
            error_description,
        )

        return redirect(
            url_for("auth.login", oauth_error="authorization")
        )

    return google_blueprint