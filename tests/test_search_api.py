from unittest.mock import Mock
from uuid import UUID

from app.models.conversation_message import MessageRole
from app.models.search_intent import SearchIntent
from app.providers.places.errors import PlacesProviderError


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

    response = client.post(
        f"/api/v1/search/{session_id}/continue",
        json={
            "message": "Which one is cheaper?",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["session_id"] == session_id
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
