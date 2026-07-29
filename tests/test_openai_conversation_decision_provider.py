from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.models.conversation_action import (
    ConversationAction,
)
from app.models.search_intent import SearchIntent
from app.providers.assistant.openai_conversation_decision_provider import (
    OpenAIConversationDecisionProvider,
)
from app.schemas.search import SearchValidationError


def build_provider(output_text: str):
    client = Mock()
    client.responses.create.return_value = (
        SimpleNamespace(
            output_text=output_text,
        )
    )

    provider = OpenAIConversationDecisionProvider(
        api_key="test-key",
        model="test-model",
        client=client,
    )

    return provider, client


def create_intent() -> SearchIntent:
    return SearchIntent(
        original_query="Find a quiet cafe",
        search_query="quiet cafe",
        category="cafe",
        preferences=("quiet",),
    )


def decide(provider):
    return provider.decide(
        message="Which one is closest?",
        original_intent=create_intent(),
        conversation_history=[
            {
                "role": "user",
                "content": "Find a quiet cafe",
            }
        ],
        places=[
            {
                "id": "cafe-1",
                "name": "Campus Cafe",
                "rating": 4.7,
                "phone": "555-0100",
            }
        ],
    )


def test_provider_requires_api_key():
    with pytest.raises(
        ValueError,
        match="OPENAI_API_KEY is required",
    ):
        OpenAIConversationDecisionProvider(
            api_key="",
            model="test-model",
        )


def test_provider_requires_model():
    with pytest.raises(
        ValueError,
        match="ASSISTANT_MODEL is required",
    ):
        OpenAIConversationDecisionProvider(
            api_key="test-key",
            model="",
        )


def test_provider_configures_default_client_timeout():
    client = Mock()

    with patch(
        "app.providers.assistant."
        "openai_conversation_decision_provider.OpenAI",
        return_value=client,
    ) as openai:
        provider = OpenAIConversationDecisionProvider(
            api_key="test-key",
            model="test-model",
        )

    openai.assert_called_once_with(
        api_key="test-key",
        timeout=20.0,
    )
    assert provider.client is client


def test_provider_returns_answer_existing_decision():
    provider, client = build_provider(
        """
        {
          "action": "answer_existing",
          "rewritten_query": null,
          "clarification_question": null
        }
        """
    )

    decision = decide(provider)

    assert decision.action is (
        ConversationAction.ANSWER_EXISTING
    )
    assert decision.rewritten_query is None
    assert decision.clarification_question is None

    call = client.responses.create.call_args.kwargs

    assert call["model"] == "test-model"
    assert "Which one is closest?" in call["input"]
    assert "Campus Cafe" in call["input"]
    assert "555-0100" not in call["input"]


def test_provider_returns_new_search_decision():
    provider, _ = build_provider(
        """
        {
          "action": "run_new_search",
          "rewritten_query": "barber near campus",
          "clarification_question": null
        }
        """
    )

    decision = decide(provider)

    assert decision.action is (
        ConversationAction.RUN_NEW_SEARCH
    )
    assert decision.rewritten_query == (
        "barber near campus"
    )


def test_provider_returns_clarification_decision():
    provider, _ = build_provider(
        """
        {
          "action": "clarify",
          "rewritten_query": null,
          "clarification_question": "What should be better?"
        }
        """
    )

    decision = decide(provider)

    assert decision.action is ConversationAction.CLARIFY
    assert decision.clarification_question == (
        "What should be better?"
    )


def test_provider_returns_refine_results_decision():
    provider, client = build_provider(
        """
        {
          "action": "refine_results",
          "rewritten_query": null,
          "clarification_question": null,
          "filter_updates": {
            "price_levels": [1, 2],
            "open_now": true,
            "minimum_rating": 4.5,
            "max_distance_meters": 2400
          }
        }
        """
    )

    decision = decide(provider)

    assert decision.action is (
        ConversationAction.REFINE_RESULTS
    )
    assert decision.filter_updates is not None
    assert decision.filter_updates.price_levels == (
        1,
        2,
    )
    assert decision.filter_updates.open_now is True
    assert (
        decision.filter_updates.minimum_rating
        == 4.5
    )
    assert (
        decision.filter_updates.max_distance_meters
        == 2400
    )

    call = client.responses.create.call_args.kwargs

    assert "filter_updates" in call["instructions"]
    assert "price_levels" in call["instructions"]
    assert "minimum_rating" in call["instructions"]


def test_provider_rejects_refine_results_without_updates():
    provider, _ = build_provider(
        """
        {
          "action": "refine_results",
          "rewritten_query": null,
          "clarification_question": null,
          "filter_updates": null
        }
        """
    )

    with pytest.raises(
        SearchValidationError,
        match="Filter updates must be an object",
    ):
        decide(provider)


def test_provider_rejects_empty_refine_updates():
    provider, _ = build_provider(
        """
        {
          "action": "refine_results",
          "rewritten_query": null,
          "clarification_question": null,
          "filter_updates": {}
        }
        """
    )

    with pytest.raises(
        ValueError,
        match="REFINE_RESULTS requires filter updates",
    ):
        decide(provider)


def test_provider_rejects_non_object_json():
    provider, _ = build_provider("[]")

    with pytest.raises(
        ValueError,
        match="must be a JSON object",
    ):
        decide(provider)


def test_provider_rejects_unsupported_action():
    provider, _ = build_provider(
        """
        {
          "action": "unknown_action"
        }
        """
    )

    with pytest.raises(
        ValueError,
        match="unsupported conversation action",
    ):
        decide(provider)


def test_provider_rejects_missing_output_text():
    client = Mock()
    client.responses.create.return_value = (
        SimpleNamespace()
    )

    provider = OpenAIConversationDecisionProvider(
        api_key="test-key",
        model="test-model",
        client=client,
    )

    with pytest.raises(
        ValueError,
        match="invalid decision response",
    ):
        decide(provider)
