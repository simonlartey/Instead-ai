from typing import Any

from app.models.conversation_decision import ConversationDecision
from app.models.search_intent import SearchIntent
from app.providers.assistant.conversation_decision_provider import (
    ConversationDecisionProvider,
)


class FakeConversationDecisionProvider(
    ConversationDecisionProvider
):
    """Return a configured conversation decision for tests."""

    def __init__(
        self,
        decision: ConversationDecision,
    ) -> None:
        self.decision = decision
        self.received_message: str | None = None
        self.received_original_intent: SearchIntent | None = None
        self.received_conversation_history: (
            list[dict[str, str]] | None
        ) = None
        self.received_places: (
            list[dict[str, Any]] | None
        ) = None

    def decide(
        self,
        message: str,
        original_intent: SearchIntent,
        conversation_history: list[dict[str, str]],
        places: list[dict[str, Any]],
    ) -> ConversationDecision:
        self.received_message = message
        self.received_original_intent = original_intent
        self.received_conversation_history = (
            conversation_history
        )
        self.received_places = places

        return self.decision
