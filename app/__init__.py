from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix

from app.authentication import load_current_user
from app.extensions import db, migrate
from app.models.conversation_action import ConversationAction
from app.models.conversation_decision import ConversationDecision
from app.providers.assistant.factory import create_assistant_provider
from app.providers.assistant.fake_conversation_decision_provider import (
    FakeConversationDecisionProvider,
)
from app.providers.places.factory import create_places_provider
from app.repositories.in_memory_search_session import (
    InMemorySearchSessionRepository,
)
from app.services.conversation_manager import ConversationManager
from app.services.conversation_orchestrator import (
    ConversationOrchestrator,
)
from app.services.discovery_cache import (
    DiscoveryCache,
)
from config import Config


def create_app(config_class=Config):
    """Create and configure the CityGuide Flask application."""

    app = Flask(__name__)

    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
    )

    app.config.from_object(config_class)

    @app.before_request
    def reject_invalid_google_oauth_callbacks():
        """Reject direct visits to the Google OAuth callback endpoint."""
        if request.path != "/login/google/authorized":
            return None

        if request.args.get("code") or request.args.get("error"):
            return None

        return (
            "Invalid OAuth callback request.",
            400,
            {
                "X-Robots-Tag": "noindex, nofollow",
                "Content-Type": "text/plain; charset=utf-8",
            },
        )

    app.extensions[
        "search_session_repository"
    ] = InMemorySearchSessionRepository()

    app.extensions[
        "conversation_manager"
    ] = ConversationManager(
        app.extensions["search_session_repository"]
    )

    app.extensions["assistant_provider"] = create_assistant_provider(
        app.config
    )

    app.extensions[
        "conversation_decision_provider"
    ] = FakeConversationDecisionProvider(
        ConversationDecision(
            action=ConversationAction.ANSWER_EXISTING,
        )
    )

    app.extensions[
        "conversation_orchestrator"
    ] = ConversationOrchestrator(
        decision_provider=app.extensions[
            "conversation_decision_provider"
        ]
    )

    app.extensions["places_provider"] = create_places_provider(
        app.config
    )

    app.extensions["discovery_cache"] = (
        DiscoveryCache(
            ttl_seconds=21_600,
        )
    )

    db.init_app(app)
    migrate.init_app(app, db)

    app.before_request(load_current_user)

    from app import models  # noqa: F401
    from app.oauth import create_google_blueprint
    from app.routes.api import search_api_bp
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(search_api_bp)

    google_blueprint = create_google_blueprint()

    app.register_blueprint(
        google_blueprint,
        url_prefix="/login",
    )

    return app
