from app.models.conversation_message import (
    ConversationMessage,
    MessageRole,
)
from app.models.search_intent import SearchIntent
from app.repositories.in_memory_search_session import (
    InMemorySearchSessionRepository,
)
from app.schemas.search import (
    SearchFilters,
    SearchLocation,
)
from app.services.conversation_manager import ConversationManager


def create_intent() -> SearchIntent:
    return SearchIntent(
        original_query="Find a quiet cafe",
        search_query="quiet cafe",
        category="cafe",
        preferences=("quiet",),
    )


def test_start_session_stores_search_state():
    repository = InMemorySearchSessionRepository()
    manager = ConversationManager(repository)

    location = SearchLocation(
        latitude=43.6591,
        longitude=-70.2568,
    )

    filters = SearchFilters(
        price_levels=(1,),
        open_now=True,
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

    session = manager.start_session(
        original_query="Find a quiet cafe",
        intent=create_intent(),
        location=location,
        filters=filters,
        places=places,
        ranked_places=ranked_places,
    )

    assert session.original_query == "Find a quiet cafe"
    assert session.intent == create_intent()
    assert session.location == location
    assert session.filters == filters
    assert session.places == places
    assert session.ranked_places == ranked_places
    assert repository.get(session.session_id) is session


def test_start_session_records_opening_user_message():
    manager = ConversationManager(
        InMemorySearchSessionRepository()
    )

    session = manager.start_session(
        original_query="Find a quiet cafe",
        intent=create_intent(),
        places=[],
        ranked_places=[],
    )

    assert session.conversation_history == [
        ConversationMessage(
            role=MessageRole.USER,
            content="Find a quiet cafe",
        )
    ]


def test_get_session_returns_stored_session():
    repository = InMemorySearchSessionRepository()
    manager = ConversationManager(repository)

    session = manager.start_session(
        original_query="Find a quiet cafe",
        intent=create_intent(),
        places=[],
        ranked_places=[],
    )

    assert manager.get_session(session.session_id) is session


def test_get_session_returns_none_for_unknown_id():
    manager = ConversationManager(
        InMemorySearchSessionRepository()
    )

    assert manager.get_session("missing-session") is None


def test_start_session_records_assistant_response():
    manager = ConversationManager(
        InMemorySearchSessionRepository()
    )

    session = manager.start_session(
        original_query="Find a quiet cafe",
        intent=create_intent(),
        places=[],
        ranked_places=[],
        assistant_response="Campus Cafe is the best option.",
    )

    assert session.conversation_history == [
        ConversationMessage(
            role=MessageRole.USER,
            content="Find a quiet cafe",
        ),
        ConversationMessage(
            role=MessageRole.ASSISTANT,
            content="Campus Cafe is the best option.",
        ),
    ]


def test_get_session_details_returns_serialized_session():
    repository = InMemorySearchSessionRepository()

    manager = ConversationManager(repository)

    session = manager.start_session(
        original_query="Find a quiet cafe",
        intent=create_intent(),
        places=[
            {
                "id": "cafe-1",
                "name": "Campus Cafe",
            }
        ],
        ranked_places=[
            {
                "id": "cafe-1",
                "name": "Campus Cafe",
            }
        ],
        assistant_response="Campus Cafe is the best option.",
    )

    details = manager.get_session_details(
        session.session_id
    )

    assert details["session_id"] == session.session_id

    assert details["query"] == (
        "Find a quiet cafe"
    )

    assert details["conversation_history"] == [
        {
            "role": "user",
            "content": "Find a quiet cafe",
        },
        {
            "role": "assistant",
            "content": (
                "Campus Cafe is the best option."
            ),
        },
    ]

    assert details["results"] == [
        {
            "id": "cafe-1",
            "name": "Campus Cafe",
        }
    ]


def test_continue_session_adds_messages():
    repository = InMemorySearchSessionRepository()
    manager = ConversationManager(repository)

    session = manager.start_session(
        original_query="Find a quiet cafe",
        intent=create_intent(),
        places=[],
        ranked_places=[],
        assistant_response="Campus Cafe is the best option.",
    )

    assert [
        message.role
        for message in session.conversation_history
    ] == [
        MessageRole.USER,
        MessageRole.ASSISTANT,
    ]

    updated_session = manager.continue_session(
        session_id=session.session_id,
        user_message="Which one is cheaper?",
        assistant_response="Campus Cafe is typically cheaper.",
    )

    assert updated_session is not None

    assert [
        message.role
        for message in updated_session.conversation_history
    ] == [
        MessageRole.USER,
        MessageRole.ASSISTANT,
        MessageRole.USER,
        MessageRole.ASSISTANT,
    ]


def test_replace_search_state_updates_existing_session():
    repository = InMemorySearchSessionRepository()
    manager = ConversationManager(repository)

    session = manager.start_session(
        original_query="Find a quiet cafe",
        intent=create_intent(),
        places=[
            {
                "id": "cafe-1",
                "name": "Campus Cafe",
            }
        ],
        ranked_places=[
            {
                "id": "cafe-1",
                "name": "Campus Cafe",
            }
        ],
        assistant_response=(
            "Campus Cafe is a strong option."
        ),
    )

    new_intent = SearchIntent(
        original_query="Find a barber instead",
        search_query="barber",
        category="barber",
    )

    updated_session = manager.replace_search_state(
        session_id=session.session_id,
        original_query="Find a barber instead",
        intent=new_intent,
        places=[
            {
                "id": "barber-1",
                "name": "Campus Cuts",
            }
        ],
        ranked_places=[
            {
                "id": "barber-1",
                "name": "Campus Cuts",
            }
        ],
        user_message="Find a barber instead",
        assistant_response=(
            "Campus Cuts is the strongest match."
        ),
    )

    assert updated_session is session
    assert session.original_query == (
        "Find a barber instead"
    )
    assert session.intent == new_intent
    assert session.places == [
        {
            "id": "barber-1",
            "name": "Campus Cuts",
        }
    ]
    assert session.ranked_places == [
        {
            "id": "barber-1",
            "name": "Campus Cuts",
        }
    ]

    assert len(session.conversation_history) == 4
    assert session.conversation_history[-2].content == (
        "Find a barber instead"
    )
    assert session.conversation_history[-1].content == (
        "Campus Cuts is the strongest match."
    )

    assert repository.get(session.session_id) is session


def test_replace_search_state_returns_none_for_missing_session():
    repository = InMemorySearchSessionRepository()
    manager = ConversationManager(repository)

    result = manager.replace_search_state(
        session_id="missing-session",
        original_query="Find a barber",
        intent=create_intent(),
        places=[],
        ranked_places=[],
        user_message="Find a barber",
        assistant_response="No places were found.",
    )

    assert result is None


def test_get_conversation_history_returns_serialized_messages():
    manager = ConversationManager(
        InMemorySearchSessionRepository()
    )

    session = manager.start_session(
        original_query="Find a quiet cafe",
        intent=create_intent(),
        places=[],
        ranked_places=[],
        assistant_response="Campus Cafe is the best option.",
    )

    manager.continue_session(
        session_id=session.session_id,
        user_message="Which one is cheaper?",
        assistant_response="Campus Cafe is typically cheaper.",
    )

    history = manager.get_conversation_history(
        session.session_id
    )

    assert history == [
        {
            "role": "user",
            "content": "Find a quiet cafe",
        },
        {
            "role": "assistant",
            "content": "Campus Cafe is the best option.",
        },
        {
            "role": "user",
            "content": "Which one is cheaper?",
        },
        {
            "role": "assistant",
            "content": "Campus Cafe is typically cheaper.",
        },
    ]
