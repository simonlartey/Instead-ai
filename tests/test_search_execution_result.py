from app.models.search_execution_result import (
    SearchExecutionResult,
)
from app.models.search_intent import SearchIntent


def create_intent() -> SearchIntent:
    return SearchIntent(
        original_query="Find a quiet cafe",
        search_query="quiet cafe",
    )


def test_search_execution_result_stores_pipeline_output():
    intent = create_intent()

    places = [
        {
            "id": "cafe-1",
            "name": "Campus Cafe",
        }
    ]

    ranked_places = list(places)

    result = SearchExecutionResult(
        intent=intent,
        places=places,
        ranked_places=ranked_places,
        assistant_response=(
            "Campus Cafe is the strongest match."
        ),
        filter_mode="fallback",
        filter_title="Selected filters were broadened",
        filter_message="Showing relevant alternatives.",
    )

    assert result.intent == intent
    assert result.places == places
    assert result.ranked_places == ranked_places
    assert result.assistant_response == (
        "Campus Cafe is the strongest match."
    )
    assert result.filter_mode == "fallback"
    assert result.filter_title == (
        "Selected filters were broadened"
    )
    assert result.filter_message == (
        "Showing relevant alternatives."
    )


def test_search_execution_results_do_not_share_lists():
    first_result = SearchExecutionResult(
        intent=create_intent()
    )
    second_result = SearchExecutionResult(
        intent=create_intent()
    )

    assert first_result.places is not second_result.places
    assert (
        first_result.ranked_places
        is not second_result.ranked_places
    )
