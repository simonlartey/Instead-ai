from app import create_app
from app.providers.assistant.fake_provider import (
    FakeAssistantProvider,
)
from app.providers.assistant.fake_conversation_decision_provider import (
    FakeConversationDecisionProvider,
)
from app.providers.assistant.openai_provider import (
    OpenAIAssistantProvider,
)
from app.providers.places.mock_provider import MockPlacesProvider
from app.repositories.in_memory_search_session import (
    InMemorySearchSessionRepository,
)
from app.services.conversation_manager import ConversationManager
from app.services.conversation_orchestrator import (
    ConversationOrchestrator,
)
from tests.conftest import TestConfig


class MockProviderConfig(TestConfig):
    ASSISTANT_PROVIDER = "fake"
    PLACES_PROVIDER = "mock"
    PLACES_API_KEY = None
    PLACES_REQUEST_TIMEOUT_SECONDS = 10


class OpenAIProviderConfig(TestConfig):
    ASSISTANT_PROVIDER = "openai"
    OPENAI_API_KEY = "test-openai-key"
    ASSISTANT_MODEL = "test-model"
    PLACES_PROVIDER = "mock"
    PLACES_API_KEY = None
    PLACES_REQUEST_TIMEOUT_SECONDS = 10


def test_create_app_registers_configured_places_provider():
    app = create_app(MockProviderConfig)

    assert isinstance(
        app.extensions["places_provider"],
        MockPlacesProvider,
    )


def test_create_app_registers_configured_assistant_provider():
    app = create_app(MockProviderConfig)

    assert isinstance(
        app.extensions["assistant_provider"],
        FakeAssistantProvider,
    )


def test_create_app_registers_openai_assistant_provider():
    app = create_app(OpenAIProviderConfig)

    provider = app.extensions["assistant_provider"]

    assert isinstance(
        provider,
        OpenAIAssistantProvider,
    )

    assert provider.model == "test-model"


def test_create_app_registers_search_session_repository():
    app = create_app(MockProviderConfig)

    assert isinstance(
        app.extensions["search_session_repository"],
        InMemorySearchSessionRepository,
    )


def test_create_app_registers_conversation_manager():
    app = create_app(MockProviderConfig)

    assert isinstance(
        app.extensions["conversation_manager"],
        ConversationManager,
    )


def test_app_registers_conversation_decision_provider(app):
    provider = app.extensions[
        "conversation_decision_provider"
    ]

    assert isinstance(
        provider,
        FakeConversationDecisionProvider,
    )


def test_app_registers_conversation_orchestrator(app):
    orchestrator = app.extensions[
        "conversation_orchestrator"
    ]

    assert isinstance(
        orchestrator,
        ConversationOrchestrator,
    )

    assert (
        orchestrator.decision_provider
        is app.extensions[
            "conversation_decision_provider"
        ]
    )
