from dataclasses import dataclass

from app.models.conversation_action import (
    ConversationAction,
)
from app.models.search_filter_updates import (
    SearchFilterUpdates,
)


@dataclass(frozen=True)
class ConversationDecision:
    """Represent how a conversational message should be handled."""

    action: ConversationAction
    rewritten_query: str | None = None
    clarification_question: str | None = None
    filter_updates: SearchFilterUpdates | None = None

    def __post_init__(self) -> None:
        rewritten_query = self._normalize_optional_text(
            self.rewritten_query
        )
        clarification_question = self._normalize_optional_text(
            self.clarification_question
        )

        object.__setattr__(
            self,
            "rewritten_query",
            rewritten_query,
        )
        object.__setattr__(
            self,
            "clarification_question",
            clarification_question,
        )

        if (
            self.action is ConversationAction.RUN_NEW_SEARCH
            and rewritten_query is None
        ):
            raise ValueError(
                "RUN_NEW_SEARCH requires a rewritten query."
            )

        if (
            self.action is ConversationAction.CLARIFY
            and clarification_question is None
        ):
            raise ValueError(
                "CLARIFY requires a clarification question."
            )

        if self.action is ConversationAction.REFINE_RESULTS:
            if (
                self.filter_updates is None
                or not self.filter_updates.has_updates()
            ):
                raise ValueError(
                    "REFINE_RESULTS requires filter updates."
                )

        if (
            self.action is not ConversationAction.REFINE_RESULTS
            and self.filter_updates is not None
        ):
            raise ValueError(
                "Filter updates are only valid for "
                "REFINE_RESULTS."
            )

    @staticmethod
    def _normalize_optional_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None
