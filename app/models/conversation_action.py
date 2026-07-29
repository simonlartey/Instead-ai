from enum import Enum


class ConversationAction(str, Enum):
    """Describe how a conversational search message should be handled."""

    ANSWER_EXISTING = "answer_existing"
    REFINE_RESULTS = "refine_results"
    RUN_NEW_SEARCH = "run_new_search"
    CLARIFY = "clarify"
