from abc import ABC, abstractmethod
from typing import Any

from app.models.conversation_decision import ConversationDecision
from app.models.search_intent import SearchIntent


class ConversationDecisionProvider(ABC):
    """Classify how a follow-up search message should be handled."""

    @abstractmethod
    def decide(
        self,
        message: str,
        original_intent: SearchIntent,
        conversation_history: list[dict[str, str]],
        places: list[dict[str, Any]],
    ) -> ConversationDecision:
        """Return a structured decision for the follow-up message."""
        raise NotImplementedError
