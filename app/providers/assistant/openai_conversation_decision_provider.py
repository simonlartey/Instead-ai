import json
from typing import Any

from openai import OpenAI

from app.models.conversation_action import (
    ConversationAction,
)
from app.models.conversation_decision import (
    ConversationDecision,
)
from app.models.search_intent import SearchIntent
from app.providers.assistant.conversation_decision_provider import (
    ConversationDecisionProvider,
)


class OpenAIConversationDecisionProvider(
    ConversationDecisionProvider
):
    """Use OpenAI to classify conversational search follow-ups."""

    def __init__(
        self,
        api_key: str,
        model: str,
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required for the "
                "OpenAI conversation decision provider"
            )

        if not model:
            raise ValueError(
                "ASSISTANT_MODEL is required for the "
                "OpenAI conversation decision provider"
            )

        self.client = client or OpenAI(
            api_key=api_key,
        )
        self.model = model

    def decide(
        self,
        message: str,
        original_intent: SearchIntent,
        conversation_history: list[dict[str, str]],
        places: list[dict[str, Any]],
    ) -> ConversationDecision:
        response = self.client.responses.create(
            model=self.model,
            instructions=(
                "Classify the latest follow-up message in an "
                "existing local-search conversation. Return only "
                "valid JSON with these keys: action, "
                "rewritten_query, clarification_question. "
                "The action must be one of: answer_existing, "
                "refine_results, run_new_search, clarify. "
                "Use answer_existing when the user asks a question "
                "that can be answered from the existing places. "
                "Use refine_results when the user adds constraints "
                "to the same type of search. "
                "Use run_new_search when the user changes what kind "
                "of place they want. Include a complete rewritten_query. "
                "Use clarify when the request is too ambiguous to act "
                "on safely. Include a concise clarification_question. "
                "Use null for fields that do not apply."
            ),
            input=(
                "Original search intent:\n"
                f"{json.dumps(self._serialize_intent(original_intent))}"
                "\n\nConversation history:\n"
                f"{json.dumps(conversation_history, ensure_ascii=False)}"
                "\n\nCurrent places:\n"
                f"{json.dumps(self._compact_places(places), ensure_ascii=False)}"
                "\n\nLatest user message:\n"
                f"{message}"
            ),
        )

        output_text = self._extract_output_text(
            response
        )

        payload = json.loads(output_text)

        if not isinstance(payload, dict):
            raise ValueError(
                "OpenAI conversation decision must be a JSON object"
            )

        action_value = payload.get("action")

        if not isinstance(action_value, str):
            raise ValueError(
                "OpenAI conversation decision requires an action"
            )

        try:
            action = ConversationAction(
                action_value.strip()
            )
        except ValueError as error:
            raise ValueError(
                "OpenAI returned an unsupported conversation action"
            ) from error

        return ConversationDecision(
            action=action,
            rewritten_query=self._optional_string(
                payload.get("rewritten_query")
            ),
            clarification_question=self._optional_string(
                payload.get("clarification_question")
            ),
        )

    @staticmethod
    def _serialize_intent(
        intent: SearchIntent,
    ) -> dict[str, Any]:
        return {
            "original_query": intent.original_query,
            "search_query": intent.search_query,
            "category": intent.category,
            "cuisine": intent.cuisine,
            "price_levels": list(intent.price_levels),
            "preferences": list(intent.preferences),
            "max_distance_meters": intent.max_distance_meters,
            "open_now": intent.open_now,
        }

    @staticmethod
    def _compact_places(
        places: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        allowed_fields = (
            "id",
            "name",
            "category",
            "rating",
            "price_level",
            "open_now",
            "distance_miles",
        )

        return [
            {
                field: place[field]
                for field in allowed_fields
                if field in place
            }
            for place in places
            if isinstance(place, dict)
        ]

    @staticmethod
    def _extract_output_text(
        response: Any,
    ) -> str:
        output_text = getattr(
            response,
            "output_text",
            None,
        )

        if not isinstance(output_text, str):
            raise ValueError(
                "OpenAI returned an invalid decision response"
            )

        normalized_output = output_text.strip()

        if not normalized_output:
            raise ValueError(
                "OpenAI returned an empty decision response"
            )

        return normalized_output

    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:
        if not isinstance(value, str):
            return None

        normalized_value = value.strip()

        return normalized_value or None
