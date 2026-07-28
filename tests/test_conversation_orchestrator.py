import pytest

from app.models.conversation_action import (
    ConversationAction,
)
from app.models.conversation_decision import (
    ConversationDecision,
)
from app.models.conversation_message import MessageRole
from app.models.search_intent import SearchIntent
from app.models.search_session import SearchSession
from app.providers.assistant.fake_conversation_decision_provider import (
    FakeConversationDecisionProvider,
)
from app.services.conversation_orchestrator import (
    ConversationOrchestrator,
)


def create_session() -> SearchSession:
    session = SearchSession(
        original_query="Find a quiet cafe",
        intent=SearchIntent(
            original_query="Find a quiet cafe",
            search_query="quiet cafe",
            category="cafe",
            preferences=("quiet",),
        ),
        places=[
            {
                "id": "cafe-1",
                "name": "Campus Cafe",
            }
        ],
        ranked_places=[
            {
                "id": "cafe-1",
                "name": "Campus Cafe",
            }
        ],
    )

    session.add_message(
        role=MessageRole.USER,
        content="Find a quiet cafe",
    )
    session.add_message(
        role=MessageRole.ASSISTANT,
        content="Campus Cafe is a strong option.",
    )

    return session


@pytest.mark.parametrize(
    "decision",
    [
        ConversationDecision(
            action=ConversationAction.ANSWER_EXISTING,
        ),
        ConversationDecision(
            action=ConversationAction.REFINE_RESULTS,
        ),
        ConversationDecision(
            action=ConversationAction.RUN_NEW_SEARCH,
            rewritten_query="barber near campus",
        ),
        ConversationDecision(
            action=ConversationAction.CLARIFY,
            clarification_question=(
                "What kind of place are you looking for?"
            ),
        ),
    ],
)
def test_orchestrator_returns_provider_decision(
    decision,
):
    provider = FakeConversationDecisionProvider(
        decision
    )
    orchestrator = ConversationOrchestrator(
        decision_provider=provider
    )

    result = orchestrator.decide(
        session=create_session(),
        message="Show me something else",
    )

    assert result is decision


def test_orchestrator_passes_session_context_to_provider():
    decision = ConversationDecision(
        action=ConversationAction.ANSWER_EXISTING,
    )
    provider = FakeConversationDecisionProvider(
        decision
    )
    orchestrator = ConversationOrchestrator(
        decision_provider=provider
    )
    session = create_session()

    orchestrator.decide(
        session=session,
        message="  Which one is closest?  ",
    )

    assert provider.received_message == (
        "Which one is closest?"
    )
    assert provider.received_original_intent is (
        session.intent
    )
    assert provider.received_conversation_history == [
        {
            "role": "user",
            "content": "Find a quiet cafe",
        },
        {
            "role": "assistant",
            "content": "Campus Cafe is a strong option.",
        },
    ]
    assert provider.received_places is (
        session.ranked_places
    )


def test_orchestrator_rejects_blank_message():
    provider = FakeConversationDecisionProvider(
        ConversationDecision(
            action=ConversationAction.ANSWER_EXISTING,
        )
    )
    orchestrator = ConversationOrchestrator(
        decision_provider=provider
    )

    with pytest.raises(
        ValueError,
        match="Conversation message cannot be blank",
    ):
        orchestrator.decide(
            session=create_session(),
            message="   ",
        )
