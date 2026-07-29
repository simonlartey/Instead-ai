import pytest

from app.models.conversation_action import (
    ConversationAction,
)
from app.models.conversation_decision import (
    ConversationDecision,
)
from app.models.search_filter_updates import (
    SearchFilterUpdates,
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
    assert decision.filter_updates is None


def test_refine_results_stores_filter_updates():
    updates = SearchFilterUpdates(
        price_levels=(1, 2),
        open_now=True,
    )

    decision = ConversationDecision(
        action=ConversationAction.REFINE_RESULTS,
        filter_updates=updates,
    )

    assert decision.action is (
        ConversationAction.REFINE_RESULTS
    )
    assert decision.filter_updates is updates


def test_refine_results_requires_filter_updates():
    with pytest.raises(
        ValueError,
        match="REFINE_RESULTS requires filter updates",
    ):
        ConversationDecision(
            action=ConversationAction.REFINE_RESULTS,
        )


def test_refine_results_rejects_empty_filter_updates():
    with pytest.raises(
        ValueError,
        match="REFINE_RESULTS requires filter updates",
    ):
        ConversationDecision(
            action=ConversationAction.REFINE_RESULTS,
            filter_updates=SearchFilterUpdates(),
        )


def test_other_actions_reject_filter_updates():
    with pytest.raises(
        ValueError,
        match=(
            "Filter updates are only valid for "
            "REFINE_RESULTS"
        ),
    ):
        ConversationDecision(
            action=ConversationAction.ANSWER_EXISTING,
            filter_updates=SearchFilterUpdates(
                open_now=True,
            ),
        )


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
