import pytest

from app.models.conversation_action import (
    ConversationAction,
)
from app.models.conversation_decision import (
    ConversationDecision,
)


def test_conversation_decision_stores_answer_existing_action():
    decision = ConversationDecision(
        action=ConversationAction.ANSWER_EXISTING,
    )

    assert decision.action is (
        ConversationAction.ANSWER_EXISTING
    )
    assert decision.rewritten_query is None
    assert decision.clarification_question is None


def test_conversation_decision_normalizes_optional_text():
    decision = ConversationDecision(
        action=ConversationAction.RUN_NEW_SEARCH,
        rewritten_query="  barber near Boston  ",
    )

    assert decision.rewritten_query == "barber near Boston"


def test_run_new_search_requires_rewritten_query():
    with pytest.raises(
        ValueError,
        match="RUN_NEW_SEARCH requires a rewritten query",
    ):
        ConversationDecision(
            action=ConversationAction.RUN_NEW_SEARCH,
        )


def test_clarify_requires_clarification_question():
    with pytest.raises(
        ValueError,
        match="CLARIFY requires a clarification question",
    ):
        ConversationDecision(
            action=ConversationAction.CLARIFY,
        )


def test_clarify_stores_normalized_question():
    decision = ConversationDecision(
        action=ConversationAction.CLARIFY,
        clarification_question=(
            "  What kind of place are you looking for?  "
        ),
    )

    assert decision.clarification_question == (
        "What kind of place are you looking for?"
    )


def test_blank_optional_text_is_normalized_to_none():
    decision = ConversationDecision(
        action=ConversationAction.ANSWER_EXISTING,
        rewritten_query="   ",
        clarification_question="   ",
    )

    assert decision.rewritten_query is None
    assert decision.clarification_question is None
