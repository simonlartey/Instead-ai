from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.models.conversation_action import (
    ConversationAction,
)
from app.models.search_intent import SearchIntent
from app.providers.assistant.openai_conversation_decision_provider import (
    OpenAIConversationDecisionProvider,
)


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
