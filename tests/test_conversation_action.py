from app.models.conversation_action import (
    ConversationAction,
)


def test_conversation_action_contains_supported_actions():
    assert ConversationAction.ANSWER_EXISTING.value == (
        "answer_existing"
    )
    assert ConversationAction.REFINE_RESULTS.value == (
        "refine_results"
    )
    assert ConversationAction.RUN_NEW_SEARCH.value == (
        "run_new_search"
    )
    assert ConversationAction.CLARIFY.value == "clarify"


def test_conversation_action_is_string_compatible():
    assert ConversationAction.ANSWER_EXISTING == (
        "answer_existing"
    )


def test_conversation_action_can_be_created_from_value():
    assert ConversationAction("refine_results") is (
        ConversationAction.REFINE_RESULTS
    )
