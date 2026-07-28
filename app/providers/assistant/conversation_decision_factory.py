from app.models.conversation_action import ConversationAction
from app.models.conversation_decision import ConversationDecision
from app.providers.assistant.conversation_decision_provider import (
    ConversationDecisionProvider,
)
from app.providers.assistant.fake_conversation_decision_provider import (
    FakeConversationDecisionProvider,
)
from app.providers.assistant.openai_conversation_decision_provider import (
    OpenAIConversationDecisionProvider,
)


def create_conversation_decision_provider(
    config: dict,
) -> ConversationDecisionProvider:
    """Create the configured conversation decision provider."""

    provider_name = config.get(
        "ASSISTANT_PROVIDER",
        "fake",
    )

    if provider_name == "fake":
        return FakeConversationDecisionProvider(
            ConversationDecision(
                action=ConversationAction.ANSWER_EXISTING,
            )
        )

    if provider_name == "openai":
        return OpenAIConversationDecisionProvider(
            api_key=config.get("OPENAI_API_KEY"),
            model=config.get("ASSISTANT_MODEL"),
        )

    raise ValueError(
        "Unsupported conversation decision provider: "
        f"{provider_name}"
    )
