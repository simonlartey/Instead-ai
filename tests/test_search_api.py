from unittest.mock import Mock
from uuid import UUID

from app.models.conversation_action import (
    ConversationAction,
)
from app.models.conversation_decision import (
    ConversationDecision,
)
from app.models.conversation_message import MessageRole
from app.models.search_filter_updates import (
    SearchFilterUpdates,
)
from app.models.search_intent import SearchIntent
from app.providers.places.errors import PlacesProviderError


class StubSearchService:
    def __init__(self, response_payload):
        self.response_payload = response_payload

    def search(self, search_request):
        return self.response_payload


def test_search_api_returns_results(client):
    response = client.post(
        "/api/v1/search",
        json={
            "query": "Affordable barber for textured hair",
            "location": {
                "latitude": 43.6591,
                "longitude": -70.2568,
            },
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["query"] == "Affordable barber for textured hair"
    assert data["result_count"] == 3
    assert len(data["results"]) == 3
    assert str(UUID(data["search_id"])) == data["search_id"]


def test_search_api_applies_server_side_filters(client):
    response = client.post(
        "/api/v1/search",
        json={
            "query": "Barber",
            "filters": {
                "price_levels": [1],
                "open_now": True,
                "minimum_rating": 4.5,
                "max_distance_meters": 2000,
            },
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["result_count"] == 1

    assert [
        place["id"]
        for place in data["results"]
    ] == ["elevate-cuts"]


def test_search_api_returns_exact_filter_status(
    client,
    monkeypatch,
):
    response_payload = {
        "search_id": "search-123",
        "query": "coffee",
        "result_count": 1,
        "results": [
            {
                "id": "place-1",
                "name": "Coffee Place",
            }
        ],
        "assistant_response": "Here is one option.",
        "filter_status": {
            "mode": "exact",
            "title": None,
            "message": None,
        },
    }

    monkeypatch.setattr(
        "app.routes.api.search.SearchService",
        lambda **kwargs: StubSearchService(
            response_payload
        ),
    )

    response = client.post(
        "/api/v1/search",
        json={
            "query": "coffee",
            "filters": {
                "open_now": True,
            },
        },
    )

    assert response.status_code == 200
    assert response.get_json()["filter_status"] == {
        "mode": "exact",
        "title": None,
        "message": None,
    }


def test_search_api_returns_fallback_filter_status(
    client,
    monkeypatch,
):
    response_payload = {
        "search_id": "search-123",
        "query": "affordable barber",
        "result_count": 2,
        "results": [
            {
                "id": "place-1",
                "name": "First Barber",
            },
            {
                "id": "place-2",
                "name": "Second Barber",
            },
        ],
        "assistant_response": (
            "Pricing could not be verified for these options."
        ),
        "filter_status": {
            "mode": "fallback",
            "title": (
                "Selected pricing could not be verified"
            ),
            "message": (
                "Showing relevant alternatives because the "
                "retrieved places did not include verified pricing "
                "in the selected range."
            ),
        },
    }

    monkeypatch.setattr(
        "app.routes.api.search.SearchService",
        lambda **kwargs: StubSearchService(
            response_payload
        ),
    )

    response = client.post(
        "/api/v1/search",
        json={
            "query": "barber",
            "filters": {
                "price_levels": [1],
            },
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["result_count"] == 2
    assert data["filter_status"]["mode"] == "fallback"
    assert data["filter_status"]["title"] == (
        "Selected pricing could not be verified"
    )
    assert "relevant alternatives" in (
        data["filter_status"]["message"]
    )


def test_search_api_returns_empty_filter_status(
    client,
    monkeypatch,
):
    response_payload = {
        "search_id": "search-123",
        "query": "rare service",
        "result_count": 0,
        "results": [],
        "assistant_response": "No places were found.",
        "filter_status": {
            "mode": "empty",
            "title": "No matching places found",
            "message": (
                "Try changing your wording or broadening "
                "your search."
            ),
        },
    }

    monkeypatch.setattr(
        "app.routes.api.search.SearchService",
        lambda **kwargs: StubSearchService(
            response_payload
        ),
    )

    response = client.post(
        "/api/v1/search",
        json={
            "query": "rare service",
            "filters": {
                "open_now": True,
            },
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["results"] == []
    assert data["filter_status"] == {
        "mode": "empty",
        "title": "No matching places found",
        "message": (
            "Try changing your wording or broadening "
            "your search."
        ),
    }


def test_search_api_creates_conversation_session(
    app,
    client,
):
    response = client.post(
        "/api/v1/search",
        json={
            "query": "Affordable barber for textured hair",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    session_id = data["search_id"]

    repository = app.extensions[
        "search_session_repository"
    ]

    session = repository.get(session_id)

    assert session is not None

    assert len(session.conversation_history) == 2

    assert (
        session.conversation_history[0].role
        == MessageRole.USER
    )

    assert (
        session.conversation_history[1].role
        == MessageRole.ASSISTANT
    )


def test_search_api_returns_normalized_place_fields(client):
    response = client.post(
        "/api/v1/search",
        json={"query": "Barber"},
    )

    place = response.get_json()["results"][0]

    assert place["id"] == "portland-fade-studio"
    assert place["name"] == "Portland Fade Studio"
    assert place["category"] == "Barber shop"
    assert place["rating"] == 4.9
    assert place["open_now"] is True
    assert isinstance(place["match_reasons"], list)


def test_search_api_rejects_blank_query(client):
    response = client.post(
        "/api/v1/search",
        json={"query": "   "},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "code": "invalid_search_request",
            "message": "Please enter a search query.",
        }
    }


def test_search_api_rejects_missing_query(client):
    response = client.post(
        "/api/v1/search",
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == (
        "invalid_search_request"
    )


def test_search_api_rejects_non_json_request(client):
    response = client.post(
        "/api/v1/search",
        data="query=barber",
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 415
    assert response.get_json() == {
        "error": {
            "code": "invalid_content_type",
            "message": "Request body must use application/json.",
        }
    }


def test_search_api_rejects_malformed_json(client):
    response = client.post(
        "/api/v1/search",
        data='{"query":',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == (
        "invalid_search_request"
    )


def test_search_api_rejects_invalid_location(client):
    response = client.post(
        "/api/v1/search",
        json={
            "query": "Coffee shop",
            "location": {
                "latitude": 200,
                "longitude": -70.2568,
            },
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == (
        "Latitude must be between -90 and 90."
    )


def test_search_api_handles_provider_failure(
    app,
    client,
):
    provider = Mock()
    provider.search.side_effect = PlacesProviderError(
        "Google Places search failed."
    )

    app.extensions["places_provider"] = provider

    response = client.post(
        "/api/v1/search",
        json={
            "query": "Coffee shops",
        },
    )

    assert response.status_code == 503
    assert response.get_json() == {
        "error": {
            "code": "places_provider_unavailable",
            "message": (
                "Local recommendations are temporarily unavailable."
            ),
        }
    }

    provider.search.assert_called_once_with(
        query="Coffee shops",
        latitude=None,
        longitude=None,
    )


def test_search_api_does_not_hide_unexpected_errors(
    app,
    client,
):
    provider = Mock()
    provider.search.side_effect = RuntimeError(
        "Unexpected programming error"
    )

    app.extensions["places_provider"] = provider

    try:
        client.post(
            "/api/v1/search",
            json={
                "query": "Coffee shops",
            },
        )
    except RuntimeError as error:
        assert str(error) == "Unexpected programming error"
    else:
        raise AssertionError(
            "Unexpected errors should not be converted "
            "into provider availability responses."
        )


def test_discovery_api_returns_location_aware_sections(
    client,
):
    response = client.post(
        "/api/v1/discovery",
        json={
            "location": {
                "latitude": 43.6591,
                "longitude": -70.2568,
            }
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data["sections"]) == 3
    assert len(data["moods"]) == 4
    assert data["location"]["latitude"] == 43.6591
    assert data["location"]["longitude"] == -70.2568
    assert data["moods"][0]["id"] == "eat"
    assert data["moods"][0]["place"]["name"]

    assert data["sections"][0]["title"] == (
        "Trending Near You"
    )

    assert data["sections"][0]["description"] == (
        "See what is trending right now."
    )


def test_discovery_api_rejects_invalid_location(
    client,
):
    response = client.post(
        "/api/v1/discovery",
        json={
            "location": {
                "latitude": 200,
                "longitude": -70.2568,
            }
        },
    )

    assert response.status_code == 400

    assert response.get_json()["error"]["code"] == (
        "invalid_discovery_request"
    )


def test_place_photo_redirects_to_resolved_url(
    app,
    client,
):
    provider = Mock()
    provider.get_photo_url.return_value = (
        "https://images.example.com/photo.jpg"
    )

    app.extensions["places_provider"] = provider

    response = client.get(
        "/api/v1/place-photo",
        query_string={
            "name": "places/place-123/photos/photo-456",
            "width": "1200",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] == (
        "https://images.example.com/photo.jpg"
    )
    provider.get_photo_url.assert_called_once_with(
        "places/place-123/photos/photo-456",
        max_width=1200,
    )


def test_place_photo_rejects_invalid_width(client):
    response = client.get(
        "/api/v1/place-photo",
        query_string={
            "name": "places/place-123/photos/photo-456",
            "width": "wide",
        },
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "code": "invalid_photo_request",
            "message": "Photo width must be an integer.",
        }
    }


def test_place_photo_route_rejects_unavailable_provider(
    app,
    client,
):
    app.extensions["places_provider"] = Mock(spec=[])

    response = client.get(
        "/api/v1/place-photo",
        query_string={
            "name": "places/place-123/photos/photo-456",
        },
    )

    assert response.status_code == 503
    assert response.get_json() == {
        "error": {
            "code": "place_photos_unavailable",
            "message": (
                "Place photos are unavailable for "
                "the configured provider."
            ),
        }
    }


def test_place_photo_route_handles_provider_validation_error(
    app,
    client,
):
    provider = Mock()
    provider.get_photo_url.side_effect = ValueError(
        "Invalid Google Places photo name."
    )

    app.extensions["places_provider"] = provider

    response = client.get(
        "/api/v1/place-photo",
        query_string={
            "name": "bad-name",
        },
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "code": "invalid_photo_request",
            "message": "Invalid Google Places photo name.",
        }
    }


def test_place_photo_handles_provider_failure(
    app,
    client,
):
    provider = Mock()
    provider.get_photo_url.side_effect = PlacesProviderError("photo failed")

    app.extensions["places_provider"] = provider

    response = client.get(
        "/api/v1/place-photo",
        query_string={
            "name": "places/place-123/photos/photo-456",
        },
    )

    assert response.status_code == 503
    assert response.get_json() == {
        "error": {
            "code": "place_photo_unavailable",
            "message": (
                "This place photo is temporarily unavailable."
            ),
        }
    }


def test_search_api_uses_assistant_intent_for_places(
    app,
    client,
):
    assistant_provider = Mock()
    assistant_provider.parse_search_intent.return_value = SearchIntent(
        original_query="Find somewhere quiet to study",
        search_query="quiet cafe",
    )
    assistant_provider.generate_search_response.return_value = (
        "I found no matching places."
    )

    places_provider = Mock()
    places_provider.search.return_value = []

    app.extensions["assistant_provider"] = assistant_provider
    app.extensions["places_provider"] = places_provider

    response = client.post(
        "/api/v1/search",
        json={
            "query": "Find somewhere quiet to study",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["query"] == (
        "Find somewhere quiet to study"
    )
    assert response.get_json()["assistant_response"] == (
        "I found no matching places."
    )

    assistant_provider.parse_search_intent.assert_called_once_with(
        "Find somewhere quiet to study"
    )
    assistant_provider.generate_search_response.assert_called_once_with(
        query="Find somewhere quiet to study",
        places=[],
    )

    places_provider.search.assert_called_once_with(
        query="quiet cafe",
        latitude=None,
        longitude=None,
    )


def test_get_search_session_returns_session(
    app,
    client,
):
    conversation_manager = app.extensions[
        "conversation_manager"
    ]

    session = conversation_manager.start_session(
        original_query="Find a quiet cafe",
        intent=SearchIntent(
            original_query="Find a quiet cafe",
            search_query="quiet cafe",
        ),
        places=[],
        ranked_places=[],
        assistant_response=(
            "Campus Cafe is a good option."
        ),
    )

    response = client.get(
        f"/api/v1/search/{session.session_id}"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["session_id"] == session.session_id

    assert data["conversation_history"] == [
        {
            "role": "user",
            "content": "Find a quiet cafe",
        },
        {
            "role": "assistant",
            "content": (
                "Campus Cafe is a good option."
            ),
        },
    ]


def test_get_search_session_returns_404_for_missing_session(
    client,
):
    response = client.get(
        "/api/v1/search/missing-session"
    )

    assert response.status_code == 404

    assert response.get_json()["error"]["code"] == (
        "search_session_not_found"
    )


def test_continue_search_returns_response(
    app,
    client,
):
    search_response = client.post(
        "/api/v1/search",
        json={
            "query": "Affordable barber for textured hair",
        },
    )

    assert search_response.status_code == 200

    session_id = search_response.get_json()["search_id"]

    conversation_orchestrator = Mock()
    conversation_orchestrator.decide.return_value = (
        ConversationDecision(
            action=ConversationAction.ANSWER_EXISTING,
        )
    )

    app.extensions[
        "conversation_orchestrator"
    ] = conversation_orchestrator

    response = client.post(
        f"/api/v1/search/{session_id}/continue",
        json={
            "message": "Which one is cheaper?",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["session_id"] == session_id
    assert data["action"] == "answer_existing"
    assert data["response"].startswith(
        "You asked: Which one is cheaper?. "
    )
    assert "I can help compare these options:" in data[
        "response"
    ]

    repository = app.extensions[
        "search_session_repository"
    ]

    session = repository.get(session_id)
    assert session is not None
    assert len(session.conversation_history) == 4

    conversation_orchestrator.decide.assert_called_once()

    decision_call = (
        conversation_orchestrator.decide.call_args.kwargs
    )

    assert decision_call["session"].session_id == session_id
    assert decision_call["message"] == (
        "Which one is cheaper?"
    )


def test_continue_search_returns_clarification_question(
    app,
    client,
):
    initial_response = client.post(
        "/api/v1/search",
        json={
            "query": "Find quiet cafes",
        },
    )

    session_id = initial_response.get_json()[
        "search_id"
    ]

    conversation_orchestrator = Mock()
    conversation_orchestrator.decide.return_value = (
        ConversationDecision(
            action=ConversationAction.CLARIFY,
            clarification_question=(
                "What would you like to improve: "
                "price, distance, rating, or atmosphere?"
            ),
        )
    )

    app.extensions[
        "conversation_orchestrator"
    ] = conversation_orchestrator

    assistant_provider = app.extensions[
        "assistant_provider"
    ]
    assistant_provider.continue_conversation = Mock()

    response = client.post(
        f"/api/v1/search/{session_id}/continue",
        json={
            "message": "Show me something better",
        },
    )

    assert response.status_code == 200

    assert response.get_json() == {
        "session_id": session_id,
        "action": "clarify",
        "response": (
            "What would you like to improve: "
            "price, distance, rating, or atmosphere?"
        ),
    }

    assistant_provider.continue_conversation.assert_not_called()

    repository = app.extensions[
        "search_session_repository"
    ]

    session = repository.get(session_id)

    assert session is not None
    assert len(session.conversation_history) == 4

    assert (
        session.conversation_history[-2].content
        == "Show me something better"
    )

    assert session.conversation_history[-1].content == (
        "What would you like to improve: "
        "price, distance, rating, or atmosphere?"
    )


def test_continue_search_handles_decision_failure(
    app,
    client,
):
    initial_response = client.post(
        "/api/v1/search",
        json={
            "query": "Find quiet cafes",
        },
    )

    session_id = initial_response.get_json()[
        "search_id"
    ]

    conversation_orchestrator = Mock()
    conversation_orchestrator.decide.side_effect = (
        RuntimeError("Decision failed.")
    )

    app.extensions[
        "conversation_orchestrator"
    ] = conversation_orchestrator

    response = client.post(
        f"/api/v1/search/{session_id}/continue",
        json={
            "message": "Show me something better",
        },
    )

    assert response.status_code == 503

    assert response.get_json() == {
        "error": {
            "code": "conversation_decision_unavailable",
            "message": (
                "The search assistant could not interpret "
                "that follow-up message."
            ),
        }
    }

    repository = app.extensions[
        "search_session_repository"
    ]

    session = repository.get(session_id)

    assert session is not None
    assert len(session.conversation_history) == 2


def test_continue_search_refines_existing_results(
    app,
    client,
):
    initial_response = client.post(
        "/api/v1/search",
        json={
            "query": "Barber",
            "location": {
                "latitude": 43.6591,
                "longitude": -70.2568,
            },
            "filters": {
                "minimum_rating": 4.0,
            },
        },
    )

    session_id = initial_response.get_json()[
        "search_id"
    ]

    repository = app.extensions[
        "search_session_repository"
    ]

    original_session = repository.get(session_id)

    conversation_orchestrator = Mock()
    conversation_orchestrator.decide.return_value = (
        ConversationDecision(
            action=ConversationAction.REFINE_RESULTS,
            filter_updates=SearchFilterUpdates(
                price_levels=(1,),
                open_now=True,
                minimum_rating=4.5,
            ),
        )
    )

    app.extensions[
        "conversation_orchestrator"
    ] = conversation_orchestrator

    response = client.post(
        f"/api/v1/search/{session_id}/continue",
        json={
            "message": (
                "Only show affordable places that are "
                "open now and rated at least 4.5"
            ),
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["session_id"] == session_id
    assert data["action"] == "refine_results"
    assert data["query"] == "Barber"
    assert data["result_count"] == len(
        data["results"]
    )
    assert data["response"]
    assert data["filters"] == {
        "price_levels": [1],
        "open_now": True,
        "minimum_rating": 4.5,
        "max_distance_meters": None,
    }

    updated_session = repository.get(session_id)

    assert updated_session is original_session
    assert updated_session.original_query == "Barber"

    assert updated_session.filters.price_levels == (
        1,
    )
    assert updated_session.filters.open_now is True
    assert updated_session.filters.minimum_rating == (
        4.5
    )

    assert updated_session.location.latitude == (
        43.6591
    )
    assert updated_session.location.longitude == (
        -70.2568
    )

    assert len(
        updated_session.conversation_history
    ) == 4

    assert (
        updated_session.conversation_history[-2].content
        == (
            "Only show affordable places that are "
            "open now and rated at least 4.5"
        )
    )

    assert (
        updated_session.conversation_history[-1].content
        == data["response"]
    )


def test_continue_search_handles_refinement_provider_failure(
    app,
    client,
):
    initial_response = client.post(
        "/api/v1/search",
        json={
            "query": "Find quiet cafes",
            "filters": {
                "open_now": True,
            },
        },
    )

    session_id = initial_response.get_json()[
        "search_id"
    ]

    conversation_orchestrator = Mock()
    conversation_orchestrator.decide.return_value = (
        ConversationDecision(
            action=ConversationAction.REFINE_RESULTS,
            filter_updates=SearchFilterUpdates(
                minimum_rating=4.5,
            ),
        )
    )

    app.extensions[
        "conversation_orchestrator"
    ] = conversation_orchestrator

    places_provider = app.extensions[
        "places_provider"
    ]
    places_provider.search = Mock(
        side_effect=PlacesProviderError(
            "Provider unavailable"
        )
    )

    response = client.post(
        f"/api/v1/search/{session_id}/continue",
        json={
            "message": "Only show highly rated ones",
        },
    )

    assert response.status_code == 503

    repository = app.extensions[
        "search_session_repository"
    ]

    session = repository.get(session_id)

    assert session is not None
    assert session.original_query == (
        "Find quiet cafes"
    )
    assert session.filters.open_now is True
    assert session.filters.minimum_rating is None
    assert len(session.conversation_history) == 2


def test_continue_search_runs_new_search_in_existing_session(
    app,
    client,
):
    initial_response = client.post(
        "/api/v1/search",
        json={
            "query": "Find quiet cafes",
            "location": {
                "latitude": 43.6591,
                "longitude": -70.2568,
            },
            "filters": {
                "open_now": True,
            },
        },
    )

    session_id = initial_response.get_json()[
        "search_id"
    ]

    repository = app.extensions[
        "search_session_repository"
    ]

    original_session = repository.get(session_id)

    conversation_orchestrator = Mock()
    conversation_orchestrator.decide.return_value = (
        ConversationDecision(
            action=ConversationAction.RUN_NEW_SEARCH,
            rewritten_query="barber near campus",
        )
    )

    app.extensions[
        "conversation_orchestrator"
    ] = conversation_orchestrator

    response = client.post(
        f"/api/v1/search/{session_id}/continue",
        json={
            "message": "Find a barber instead",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["session_id"] == session_id
    assert data["action"] == "run_new_search"
    assert data["query"] == "barber near campus"
    assert data["result_count"] == len(
        data["results"]
    )
    assert data["response"]
    assert data["filters"] == {
        "price_levels": [],
        "open_now": True,
        "minimum_rating": None,
        "max_distance_meters": None,
    }

    updated_session = repository.get(session_id)

    assert updated_session is original_session
    assert updated_session.session_id == session_id
    assert updated_session.original_query == (
        "barber near campus"
    )
    assert updated_session.intent.original_query == (
        "barber near campus"
    )

    assert updated_session.location.latitude == (
        43.6591
    )
    assert updated_session.location.longitude == (
        -70.2568
    )
    assert updated_session.filters.open_now is True

    assert len(
        updated_session.conversation_history
    ) == 4

    assert (
        updated_session.conversation_history[-2].content
        == "Find a barber instead"
    )

    assert (
        updated_session.conversation_history[-1].content
        == data["response"]
    )


def test_continue_search_handles_new_search_provider_failure(
    app,
    client,
):
    initial_response = client.post(
        "/api/v1/search",
        json={
            "query": "Find quiet cafes",
        },
    )

    session_id = initial_response.get_json()[
        "search_id"
    ]

    conversation_orchestrator = Mock()
    conversation_orchestrator.decide.return_value = (
        ConversationDecision(
            action=ConversationAction.RUN_NEW_SEARCH,
            rewritten_query="barber near campus",
        )
    )

    app.extensions[
        "conversation_orchestrator"
    ] = conversation_orchestrator

    places_provider = app.extensions[
        "places_provider"
    ]
    places_provider.search = Mock(
        side_effect=PlacesProviderError(
            "Provider unavailable"
        )
    )

    response = client.post(
        f"/api/v1/search/{session_id}/continue",
        json={
            "message": "Find a barber instead",
        },
    )

    assert response.status_code == 503

    assert response.get_json()["error"]["code"] == (
        "places_provider_unavailable"
    )

    repository = app.extensions[
        "search_session_repository"
    ]

    session = repository.get(session_id)

    assert session is not None
    assert session.original_query == (
        "Find quiet cafes"
    )
    assert len(session.conversation_history) == 2


def test_continue_search_requires_message(
    app,
    client,
):
    conversation_manager = app.extensions[
        "conversation_manager"
    ]

    session = conversation_manager.start_session(
        original_query="Find a quiet cafe",
        intent=SearchIntent(
            original_query="Find a quiet cafe",
            search_query="quiet cafe",
        ),
        places=[],
        ranked_places=[],
        assistant_response="Campus Cafe is a good option.",
    )

    response = client.post(
        f"/api/v1/search/{session.session_id}/continue",
        json={},
    )

    assert response.status_code == 400

    assert response.get_json()["error"]["code"] == (
        "invalid_message"
    )


def test_continue_search_rejects_non_json_request(client):
    response = client.post(
        "/api/v1/search/session-123/continue",
        data="message=Which one is cheaper?",
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 415

    assert response.get_json() == {
        "error": {
            "code": "invalid_content_type",
            "message": "Request body must use application/json.",
        }
    }


def test_continue_search_handles_assistant_failure(
    app,
    client,
):
    initial_response = client.post(
        "/api/v1/search",
        json={
            "query": "Find quiet cafes",
        },
    )

    assert initial_response.status_code == 200

    session_id = initial_response.get_json()["search_id"]

    assistant_provider = Mock()
    assistant_provider.continue_conversation.side_effect = (
        RuntimeError("Assistant API failed.")
    )

    app.extensions["assistant_provider"] = assistant_provider

    response = client.post(
        f"/api/v1/search/{session_id}/continue",
        json={
            "message": "Which one has the highest rating?",
        },
    )

    assert response.status_code == 503

    assert response.get_json() == {
        "error": {
            "code": "assistant_provider_unavailable",
            "message": (
                "The search assistant is temporarily unavailable."
            ),
        }
    }

    repository = app.extensions[
        "search_session_repository"
    ]

    session = repository.get(session_id)

    assert session is not None
    assert len(session.conversation_history) == 2

    assistant_provider.continue_conversation.assert_called_once()
