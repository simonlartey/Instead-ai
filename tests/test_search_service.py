from app.models.search_intent import SearchIntent
from app.schemas.search import (
    SearchFilters,
    SearchLocation,
    SearchRequest,
)
from app.services.place_filter import PlaceFilterResult
from app.services.search_service import SearchService


class RecordingPlacesProvider:
    """Test provider that records the arguments it receives."""

    def __init__(self):
        self.received_query = None
        self.received_latitude = None
        self.received_longitude = None

    def search(
        self,
        query: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> list[dict]:
        self.received_query = query
        self.received_latitude = latitude
        self.received_longitude = longitude

        return [
            {
                "id": "test-place",
                "name": "Test Place",
            }
        ]


class StaticPlacesProvider:
    """Return a predefined collection of places."""

    def __init__(self, places: list[dict]):
        self.places = places

    def search(
        self,
        query: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> list[dict]:
        return self.places


class RecordingAssistantProvider:
    """Test assistant provider that records and rewrites query intent."""

    def __init__(self):
        self.received_query = None
        self.response_query = None
        self.response_places = None

    def parse_search_intent(
        self,
        query: str,
    ) -> SearchIntent:
        self.received_query = query

        return SearchIntent(
            original_query=query,
            search_query="quiet cafe",
        )

    def generate_search_response(
        self,
        query: str,
        places: list[dict],
    ) -> str:
        self.response_query = query
        self.response_places = places

        return "Campus Cafe is the strongest match."


class RecordingConversationManager:
    def __init__(self):
        self.arguments = None

    def start_session(self, **kwargs):
        self.arguments = kwargs

        class Session:
            session_id = "session-123"

        return Session()


class RecordingPlaceFilter:
    """Record places and filters passed by SearchService."""

    def __init__(
        self,
        filtered_places=None,
        mode="exact",
        title=None,
        message=None,
    ):
        self.received_places = None
        self.received_filters = None
        self.filtered_places = filtered_places
        self.mode = mode
        self.title = title
        self.message = message

    def apply_with_fallback(
        self,
        places,
        filters,
    ):
        self.received_places = places
        self.received_filters = filters

        selected_places = (
            self.filtered_places
            if self.filtered_places is not None
            else list(places)
        )

        return PlaceFilterResult(
            places=selected_places,
            mode=self.mode,
            title=self.title,
            message=self.message,
        )


def test_search_service_returns_expected_response():
    provider = RecordingPlacesProvider()
    service = SearchService(provider)

    response = service.search(
        SearchRequest(query="Quiet coffee shop")
    )

    assert response["query"] == "Quiet coffee shop"
    assert response["result_count"] == 1
    assert response["results"] == [
        {
            "id": "test-place",
            "name": "Test Place",
        }
    ]
    assert response["search_id"].startswith("search_")


def test_search_service_passes_query_to_provider():
    provider = RecordingPlacesProvider()
    service = SearchService(provider)

    service.search(
        SearchRequest(query="Affordable barber")
    )

    assert provider.received_query == "Affordable barber"
    assert provider.received_latitude is None
    assert provider.received_longitude is None


def test_search_service_passes_location_to_provider():
    provider = RecordingPlacesProvider()
    service = SearchService(provider)

    service.search(
        SearchRequest(
            query="Study space",
            location=SearchLocation(
                latitude=43.6591,
                longitude=-70.2568,
            ),
        )
    )

    assert provider.received_query == "Study space"
    assert provider.received_latitude == 43.6591
    assert provider.received_longitude == -70.2568


def test_search_service_handles_empty_provider_results():
    class EmptyPlacesProvider:
        def search(
            self,
            query: str,
            latitude: float | None = None,
            longitude: float | None = None,
        ) -> list[dict]:
            return []

    service = SearchService(EmptyPlacesProvider())

    response = service.search(
        SearchRequest(query="Rare local service")
    )

    assert response["result_count"] == 0
    assert response["results"] == []


def test_search_service_generates_unique_search_ids():
    provider = RecordingPlacesProvider()
    service = SearchService(provider)

    first_response = service.search(
        SearchRequest(query="Coffee")
    )
    second_response = service.search(
        SearchRequest(query="Coffee")
    )

    assert first_response["search_id"] != second_response["search_id"]


def test_search_service_returns_results_in_relevance_order():
    provider = StaticPlacesProvider(
        [
            {
                "id": "popular-grill",
                "name": "Popular Downtown Grill",
                "category": "Restaurant",
                "primary_type": "restaurant",
                "types": [
                    "restaurant",
                    "food",
                ],
                "rating": 4.9,
                "review_count": 2400,
                "distance_miles": 0.2,
            },
            {
                "id": "lagos-kitchen",
                "name": "Lagos Kitchen",
                "category": "African restaurant",
                "primary_type": "african_restaurant",
                "types": [
                    "african_restaurant",
                    "restaurant",
                    "food",
                ],
                "rating": 4.5,
                "review_count": 180,
                "distance_miles": 1.3,
            },
        ]
    )
    service = SearchService(provider)

    response = service.search(
        SearchRequest(
            query="African restaurant near me"
        )
    )

    assert [
        place["id"]
        for place in response["results"]
    ] == [
        "lagos-kitchen",
        "popular-grill",
    ]


def test_search_service_passes_original_query_to_ranker():
    class RecordingRanker:
        def __init__(self):
            self.arguments = None

        def rank(
            self,
            *,
            query,
            places,
            original_query=None,
        ):
            self.arguments = {
                "query": query,
                "places": places,
                "original_query": original_query,
            }
            return list(places)

    places_provider = StaticPlacesProvider(
        [
            {
                "id": "campus-cafe",
                "name": "Campus Cafe",
            }
        ]
    )
    assistant_provider = RecordingAssistantProvider()
    ranker = RecordingRanker()

    service = SearchService(
        places_provider=places_provider,
        assistant_provider=assistant_provider,
        relevance_ranker=ranker,
    )

    search_request = SearchRequest(
        query="Find a cafe near me"
    )

    service.search(search_request)

    assert ranker.arguments == {
        "query": "quiet cafe",
        "places": [
            {
                "id": "campus-cafe",
                "name": "Campus Cafe",
            }
        ],
        "original_query": search_request.query,
    }


def test_search_service_reports_count_after_ranking():
    provider = StaticPlacesProvider(
        [
            {
                "id": "first-place",
                "name": "First Place",
            },
            {
                "id": "second-place",
                "name": "Second Place",
            },
        ]
    )
    service = SearchService(provider)

    response = service.search(
        SearchRequest(query="restaurant")
    )

    assert response["result_count"] == 2


def test_search_service_parses_query_with_assistant_provider():
    places_provider = RecordingPlacesProvider()
    assistant_provider = RecordingAssistantProvider()

    service = SearchService(
        places_provider=places_provider,
        assistant_provider=assistant_provider,
    )

    service.search(
        SearchRequest(query="Find somewhere quiet to study")
    )

    assert assistant_provider.received_query == (
        "Find somewhere quiet to study"
    )


def test_search_service_uses_intent_search_query_for_places():
    places_provider = RecordingPlacesProvider()
    assistant_provider = RecordingAssistantProvider()

    service = SearchService(
        places_provider=places_provider,
        assistant_provider=assistant_provider,
    )

    response = service.search(
        SearchRequest(query="Find somewhere quiet to study")
    )

    assert places_provider.received_query == "quiet cafe"
    assert response["query"] == "Find somewhere quiet to study"


def test_search_service_falls_back_when_assistant_intent_fails():
    class BrokenAssistantProvider:
        def parse_search_intent(self, query):
            raise Exception("AI unavailable")

        def generate_search_response(self, query, places):
            return None

    service = SearchService(
        places_provider=RecordingPlacesProvider(),
        assistant_provider=BrokenAssistantProvider(),
    )

    response = service.search(
        SearchRequest(query="quiet cafe")
    )

    assert response["query"] == "quiet cafe"


def test_search_service_returns_results_when_response_generation_fails():
    class BrokenAssistantProvider(RecordingAssistantProvider):
        def generate_search_response(self, query, places):
            raise Exception("AI unavailable")

    service = SearchService(
        places_provider=RecordingPlacesProvider(),
        assistant_provider=BrokenAssistantProvider(),
    )

    response = service.search(
        SearchRequest(query="coffee")
    )

    assert response["assistant_response"] is None


def test_search_service_generates_response_from_ranked_places():
    places_provider = StaticPlacesProvider(
        [
            {
                "id": "popular-grill",
                "name": "Popular Downtown Grill",
                "category": "Restaurant",
                "primary_type": "restaurant",
                "types": [
                    "restaurant",
                    "food",
                ],
            },
            {
                "id": "lagos-kitchen",
                "name": "Lagos Kitchen",
                "category": "African restaurant",
                "primary_type": "african_restaurant",
                "types": [
                    "african_restaurant",
                    "restaurant",
                    "food",
                ],
            },
        ]
    )
    assistant_provider = RecordingAssistantProvider()

    service = SearchService(
        places_provider=places_provider,
        assistant_provider=assistant_provider,
    )

    response = service.search(
        SearchRequest(query="African restaurant near me")
    )

    assert assistant_provider.response_query == (
        "African restaurant near me"
    )
    assert [
        place["id"]
        for place in assistant_provider.response_places
    ] == [
        "lagos-kitchen",
        "popular-grill",
    ]
    assert response["assistant_response"] == (
        "Campus Cafe is the strongest match."
    )


def test_search_service_returns_no_assistant_response_without_provider():
    service = SearchService(
        RecordingPlacesProvider()
    )

    response = service.search(
        SearchRequest(query="Coffee")
    )

    assert response["assistant_response"] is None


def test_search_service_creates_conversation_session():
    places_provider = RecordingPlacesProvider()
    assistant_provider = RecordingAssistantProvider()
    conversation_manager = RecordingConversationManager()

    service = SearchService(
        places_provider=places_provider,
        assistant_provider=assistant_provider,
        conversation_manager=conversation_manager,
    )

    response = service.search(
        SearchRequest(
            query="Find somewhere quiet to study"
        )
    )

    assert response["search_id"] == "session-123"

    assert (
        conversation_manager.arguments["original_query"]
        == "Find somewhere quiet to study"
    )

    assert (
        conversation_manager.arguments["assistant_response"]
        == "Campus Cafe is the strongest match."
    )


def test_search_service_passes_request_filters_to_place_filter():
    provider_results = [
        {
            "id": "first-place",
            "name": "First Place",
        }
    ]

    places_provider = StaticPlacesProvider(
        provider_results
    )
    place_filter = RecordingPlaceFilter()

    service = SearchService(
        places_provider=places_provider,
        place_filter=place_filter,
    )

    filters = SearchFilters(
        price_levels=(1, 2),
        open_now=True,
        minimum_rating=4.5,
        max_distance_meters=2400,
    )

    service.search(
        SearchRequest(
            query="Coffee shop",
            filters=filters,
        )
    )

    assert place_filter.received_places == provider_results
    assert place_filter.received_filters == filters


def test_search_service_ranks_filtered_results():
    class RecordingRanker:
        def __init__(self):
            self.received_places = None

        def rank(
            self,
            *,
            query,
            places,
            original_query=None,
        ):
            self.received_places = places
            return list(places)

    provider_results = [
        {
            "id": "first-place",
            "name": "First Place",
        },
        {
            "id": "second-place",
            "name": "Second Place",
        },
    ]

    filtered_results = [
        {
            "id": "second-place",
            "name": "Second Place",
        }
    ]

    ranker = RecordingRanker()

    service = SearchService(
        places_provider=StaticPlacesProvider(
            provider_results
        ),
        place_filter=RecordingPlaceFilter(
            filtered_places=filtered_results
        ),
        relevance_ranker=ranker,
    )

    response = service.search(
        SearchRequest(
            query="Coffee shop",
            filters=SearchFilters(
                open_now=True,
            ),
        )
    )

    assert ranker.received_places == filtered_results
    assert response["results"] == filtered_results
    assert response["result_count"] == 1


def test_search_service_generates_response_from_filtered_results():
    provider_results = [
        {
            "id": "first-place",
            "name": "First Place",
        },
        {
            "id": "second-place",
            "name": "Second Place",
        },
    ]

    filtered_results = [
        {
            "id": "second-place",
            "name": "Second Place",
        }
    ]

    assistant_provider = RecordingAssistantProvider()

    service = SearchService(
        places_provider=StaticPlacesProvider(
            provider_results
        ),
        assistant_provider=assistant_provider,
        place_filter=RecordingPlaceFilter(
            filtered_places=filtered_results
        ),
    )

    service.search(
        SearchRequest(
            query="Coffee shop",
            filters=SearchFilters(
                minimum_rating=4.5,
            ),
        )
    )

    assert assistant_provider.response_places == filtered_results


def test_search_service_stores_filtered_places_in_session():
    provider_results = [
        {
            "id": "first-place",
            "name": "First Place",
        },
        {
            "id": "second-place",
            "name": "Second Place",
        },
    ]

    filtered_results = [
        {
            "id": "second-place",
            "name": "Second Place",
        }
    ]

    conversation_manager = RecordingConversationManager()

    service = SearchService(
        places_provider=StaticPlacesProvider(
            provider_results
        ),
        conversation_manager=conversation_manager,
        place_filter=RecordingPlaceFilter(
            filtered_places=filtered_results
        ),
    )

    service.search(
        SearchRequest(
            query="Coffee shop",
            filters=SearchFilters(
                open_now=True,
            ),
        )
    )

    assert conversation_manager.arguments["places"] == (
        filtered_results
    )
    assert conversation_manager.arguments[
        "ranked_places"
    ] == filtered_results


def test_search_service_returns_fallback_results_when_no_exact_match():
    provider_results = [
        {
            "id": "first-place",
            "name": "First Place",
            "open_now": None,
        }
    ]

    service = SearchService(
        places_provider=StaticPlacesProvider(
            provider_results
        ),
        place_filter=RecordingPlaceFilter(
            filtered_places=provider_results,
            mode="fallback",
            title="Matching hours could not be confirmed",
            message=(
                "Showing relevant alternatives because no place "
                "had confirmed hours matching this filter."
            ),
        ),
    )

    response = service.search(
        SearchRequest(
            query="Coffee shop",
            filters=SearchFilters(
                open_now=True,
            ),
        )
    )

    assert response["result_count"] == 1
    assert response["results"] == provider_results

    assert response["filter_status"] == {
        "mode": "fallback",
        "title": "Matching hours could not be confirmed",
        "message": (
            "Showing relevant alternatives because no place "
            "had confirmed hours matching this filter."
        ),
    }


def test_search_service_returns_exact_filter_status():
    provider_results = [
        {
            "id": "open-place",
            "name": "Open Place",
            "open_now": True,
        }
    ]

    service = SearchService(
        places_provider=StaticPlacesProvider(
            provider_results
        ),
        place_filter=RecordingPlaceFilter(
            filtered_places=provider_results,
            mode="exact",
        ),
    )

    response = service.search(
        SearchRequest(
            query="Coffee shop",
            filters=SearchFilters(
                open_now=True,
            ),
        )
    )

    assert response["filter_status"] == {
        "mode": "exact",
        "title": None,
        "message": None,
    }


def test_search_service_returns_empty_filter_status():
    service = SearchService(
        places_provider=StaticPlacesProvider([]),
        place_filter=RecordingPlaceFilter(
            filtered_places=[],
            mode="empty",
            title="No matching places found",
            message=(
                "Try changing your wording or broadening "
                "your search."
            ),
        ),
    )

    response = service.search(
        SearchRequest(
            query="Rare local service",
            filters=SearchFilters(
                open_now=True,
            ),
        )
    )

    assert response["result_count"] == 0
    assert response["results"] == []

    assert response["filter_status"] == {
        "mode": "empty",
        "title": "No matching places found",
        "message": (
            "Try changing your wording or broadening "
            "your search."
        ),
    }
