from app.models.conversation_decision import (
    ConversationDecision,
)
from app.models.search_session import SearchSession
from app.providers.assistant.conversation_decision_provider import (
    ConversationDecisionProvider,
)


class ConversationOrchestrator:
    """Decide how a follow-up search message should be handled."""

    def __init__(
        self,
        decision_provider: ConversationDecisionProvider,
    ) -> None:
        self.decision_provider = decision_provider

    def decide(
        self,
        session: SearchSession,
        message: str,
    ) -> ConversationDecision:
        normalized_message = message.strip()

        if not normalized_message:
            raise ValueError(
                "Conversation message cannot be blank."
            )

        conversation_history = [
            {
                "role": history_message.role.value,
                "content": history_message.content,
            }
            for history_message in session.conversation_history
        ]

        return self.decision_provider.decide(
            message=normalized_message,
            original_intent=session.intent,
            conversation_history=conversation_history,
            places=session.ranked_places,
        )
