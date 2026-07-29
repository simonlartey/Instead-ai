import pytest

from app.providers.assistant.conversation_decision_provider import (
    ConversationDecisionProvider,
)


def test_conversation_decision_provider_cannot_be_instantiated():
    with pytest.raises(TypeError):
        ConversationDecisionProvider()
