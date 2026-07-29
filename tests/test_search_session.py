from app.models.conversation_message import (
    ConversationMessage,
    MessageRole,
)
from app.models.search_intent import SearchIntent
from app.models.search_session import SearchSession
from app.schemas.search import (
    SearchFilters,
    SearchLocation,
)


def create_intent() -> SearchIntent:
    return SearchIntent(
        original_query="Find a quiet cafe",
        search_query="quiet cafe",
        category="cafe",
        preferences=("quiet",),
    )


def test_search_session_stores_search_state():
    intent = create_intent()

    location = SearchLocation(
        latitude=43.6591,
        longitude=-70.2568,
    )

    filters = SearchFilters(
        price_levels=(1, 2),
        open_now=True,
        minimum_rating=4.5,
        max_distance_meters=2400,
    )

    places = [
        {
            "id": "place-1",
            "name": "Campus Cafe",
        }
    ]

    ranked_places = [
        {
            "id": "place-1",
            "name": "Campus Cafe",
        }
    ]

    session = SearchSession(
        original_query="Find a quiet cafe",
        intent=intent,
        location=location,
        filters=filters,
        places=places,
        ranked_places=ranked_places,
    )

    assert session.original_query == "Find a quiet cafe"
    assert session.intent == intent
    assert session.location == location
    assert session.filters == filters
    assert session.places == places
    assert session.ranked_places == ranked_places
    assert session.conversation_history == []


def test_search_session_generates_unique_ids():
    first_session = SearchSession(
        original_query="coffee",
        intent=create_intent(),
    )

    second_session = SearchSession(
        original_query="coffee",
        intent=create_intent(),
    )

    assert first_session.session_id
    assert second_session.session_id
    assert first_session.session_id != second_session.session_id


def test_search_session_adds_conversation_messages():
    session = SearchSession(
        original_query="Find a quiet cafe",
        intent=create_intent(),
    )

    session.add_message(
        role=MessageRole.USER,
        content="Which one is best for studying?",
    )

    session.add_message(
        role=MessageRole.ASSISTANT,
        content="Campus Cafe is the strongest option.",
    )

    assert session.conversation_history == [
        ConversationMessage(
            role=MessageRole.USER,
            content="Which one is best for studying?",
        ),
        ConversationMessage(
            role=MessageRole.ASSISTANT,
            content="Campus Cafe is the strongest option.",
        ),
    ]


def test_search_sessions_do_not_share_mutable_defaults():
    first_session = SearchSession(
        original_query="coffee",
        intent=create_intent(),
    )

    second_session = SearchSession(
        original_query="coffee",
        intent=create_intent(),
    )

    first_session.add_message(
        role=MessageRole.USER,
        content="Show me another.",
    )

    assert len(first_session.conversation_history) == 1
    assert second_session.conversation_history == []
    assert first_session.filters is not second_session.filters
    assert first_session.places is not second_session.places
    assert (
        first_session.ranked_places
        is not second_session.ranked_places
    )
