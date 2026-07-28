from app.models.conversation_action import (
    ConversationAction,
)
from app.models.conversation_decision import (
    ConversationDecision,
)
from app.models.search_intent import SearchIntent
from app.providers.assistant.fake_conversation_decision_provider import (
    FakeConversationDecisionProvider,
)


def create_intent() -> SearchIntent:
    return SearchIntent(
        original_query="Find a quiet cafe",
        search_query="quiet cafe",
        category="cafe",
        preferences=("quiet",),
    )


def test_fake_provider_returns_configured_decision():
    decision = ConversationDecision(
        action=ConversationAction.ANSWER_EXISTING,
    )

    provider = FakeConversationDecisionProvider(
        decision
    )

    result = provider.decide(
        message="Which one is closest?",
        original_intent=create_intent(),
        conversation_history=[],
        places=[],
    )

    assert result is decision


def test_fake_provider_records_decision_inputs():
    decision = ConversationDecision(
        action=ConversationAction.REFINE_RESULTS,
    )

    provider = FakeConversationDecisionProvider(
        decision
    )

    intent = create_intent()

    history = [
        {
            "role": "user",
            "content": "Find a quiet cafe",
        }
    ]

    places = [
        {
            "id": "cafe-1",
            "name": "Campus Cafe",
        }
    ]

    provider.decide(
        message="Only show affordable ones",
        original_intent=intent,
        conversation_history=history,
        places=places,
    )

    assert provider.received_message == (
        "Only show affordable ones"
    )
    assert provider.received_original_intent is intent
    assert provider.received_conversation_history is history
    assert provider.received_places is places
