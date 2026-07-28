import pytest

from app.models.conversation_action import ConversationAction
from app.providers.assistant.conversation_decision_factory import (
    create_conversation_decision_provider,
)
from app.providers.assistant.fake_conversation_decision_provider import (
    FakeConversationDecisionProvider,
)
from app.providers.assistant.openai_conversation_decision_provider import (
    OpenAIConversationDecisionProvider,
)


def test_factory_defaults_to_fake_provider():
    provider = create_conversation_decision_provider({})

    assert isinstance(
        provider,
        FakeConversationDecisionProvider,
    )
    assert provider.decision.action is (
        ConversationAction.ANSWER_EXISTING
    )


def test_factory_creates_fake_provider():
    provider = create_conversation_decision_provider(
        {
            "ASSISTANT_PROVIDER": "fake",
        }
    )

    assert isinstance(
        provider,
        FakeConversationDecisionProvider,
    )


def test_factory_creates_openai_provider():
    provider = create_conversation_decision_provider(
        {
            "ASSISTANT_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "ASSISTANT_MODEL": "test-model",
        }
    )

    assert isinstance(
        provider,
        OpenAIConversationDecisionProvider,
    )
    assert provider.model == "test-model"


def test_factory_rejects_unsupported_provider():
    with pytest.raises(
        ValueError,
        match=(
            "Unsupported conversation decision provider: unknown"
        ),
    ):
        create_conversation_decision_provider(
            {
                "ASSISTANT_PROVIDER": "unknown",
            }
        )
