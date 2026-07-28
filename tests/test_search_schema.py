import pytest

from app.schemas.search import (
    SearchFilters,
    SearchLocation,
    SearchRequest,
    SearchValidationError,
)


def test_search_request_accepts_query_without_location():
    search_request = SearchRequest.from_dict(
        {"query": "Affordable barber"}
    )

    assert search_request.query == "Affordable barber"
    assert search_request.location is None


def test_search_request_strips_query_whitespace():
    search_request = SearchRequest.from_dict(
        {"query": "  Quiet study space  "}
    )

    assert search_request.query == "Quiet study space"


def test_search_request_accepts_valid_location():
    search_request = SearchRequest.from_dict(
        {
            "query": "Coffee shop",
            "location": {
                "latitude": 43.6591,
                "longitude": -70.2568,
            },
        }
    )

    assert search_request.location == SearchLocation(
        latitude=43.6591,
        longitude=-70.2568,
    )


def test_search_request_defaults_to_empty_filters():
    search_request = SearchRequest.from_dict(
        {"query": "Coffee shop"}
    )

    assert search_request.filters == SearchFilters()


def test_search_request_accepts_valid_filters():
    search_request = SearchRequest.from_dict(
        {
            "query": "Coffee shop",
            "filters": {
                "price_levels": [2, 1, 2],
                "open_now": True,
                "minimum_rating": 4.5,
                "max_distance_meters": 2400,
            },
        }
    )

    assert search_request.filters == SearchFilters(
        price_levels=(1, 2),
        open_now=True,
        minimum_rating=4.5,
        max_distance_meters=2400,
    )


def test_search_request_accepts_filters_with_location():
    search_request = SearchRequest.from_dict(
        {
            "query": "Coffee shop",
            "location": {
                "latitude": 43.6591,
                "longitude": -70.2568,
            },
            "filters": {
                "open_now": True,
            },
        }
    )

    assert search_request.location == SearchLocation(
        latitude=43.6591,
        longitude=-70.2568,
    )
    assert search_request.filters == SearchFilters(
        open_now=True,
    )


def test_search_filters_accept_empty_object():
    assert SearchFilters.from_dict({}) == SearchFilters()


@pytest.mark.parametrize(
    ("filters", "expected_message"),
    [
        (
            [],
            "The filters field must be an object.",
        ),
        (
            "open",
            "The filters field must be an object.",
        ),
        (
            {"price_levels": 2},
            "Filter price_levels must be an array.",
        ),
        (
            {"price_levels": ["2"]},
            "Each price level must be an integer.",
        ),
        (
            {"price_levels": [True]},
            "Each price level must be an integer.",
        ),
        (
            {"price_levels": [0]},
            "Price levels must be between 1 and 4.",
        ),
        (
            {"price_levels": [5]},
            "Price levels must be between 1 and 4.",
        ),
        (
            {"open_now": "true"},
            "Filter open_now must be a boolean.",
        ),
        (
            {"minimum_rating": "4.5"},
            "Filter minimum_rating must be a number.",
        ),
        (
            {"minimum_rating": True},
            "Filter minimum_rating must be a number.",
        ),
        (
            {"minimum_rating": -0.1},
            "Minimum rating must be between 0 and 5.",
        ),
        (
            {"minimum_rating": 5.1},
            "Minimum rating must be between 0 and 5.",
        ),
        (
            {"max_distance_meters": 1500.5},
            "Filter max_distance_meters must be an integer.",
        ),
        (
            {"max_distance_meters": True},
            "Filter max_distance_meters must be an integer.",
        ),
        (
            {"max_distance_meters": 0},
            "Maximum distance must be between 1 and 50000 meters.",
        ),
        (
            {"max_distance_meters": 50001},
            "Maximum distance must be between 1 and 50000 meters.",
        ),
    ],
)
def test_search_request_rejects_invalid_filters(
    filters,
    expected_message,
):
    with pytest.raises(
        SearchValidationError,
        match=expected_message,
    ):
        SearchRequest.from_dict(
            {
                "query": "Coffee shop",
                "filters": filters,
            }
        )


@pytest.mark.parametrize(
    ("payload", "expected_message"),
    [
        (None, "Request body must be a JSON object."),
        ([], "Request body must be a JSON object."),
        ({}, "The query field must be a string."),
        ({"query": None}, "The query field must be a string."),
        ({"query": 123}, "The query field must be a string."),
        ({"query": ""}, "Please enter a search query."),
        ({"query": "   "}, "Please enter a search query."),
        (
            {"query": "a" * 501},
            "The search query must be 500 characters or fewer.",
        ),
    ],
)
def test_search_request_rejects_invalid_query(
    payload,
    expected_message,
):
    with pytest.raises(
        SearchValidationError,
        match=expected_message,
    ):
        SearchRequest.from_dict(payload)


def test_search_request_rejects_non_object_location():
    with pytest.raises(
        SearchValidationError,
        match="The location field must be an object.",
    ):
        SearchRequest.from_dict(
            {
                "query": "Barber",
                "location": "Portland",
            }
        )


@pytest.mark.parametrize(
    ("latitude", "longitude", "expected_message"),
    [
        ("43.6591", -70.2568, "Location latitude must be a number."),
        (True, -70.2568, "Location latitude must be a number."),
        (43.6591, "-70.2568", "Location longitude must be a number."),
        (43.6591, False, "Location longitude must be a number."),
        (91, -70.2568, "Latitude must be between -90 and 90."),
        (-91, -70.2568, "Latitude must be between -90 and 90."),
        (43.6591, 181, "Longitude must be between -180 and 180."),
        (43.6591, -181, "Longitude must be between -180 and 180."),
    ],
)
def test_search_request_rejects_invalid_coordinates(
    latitude,
    longitude,
    expected_message,
):
    with pytest.raises(
        SearchValidationError,
        match=expected_message,
    ):
        SearchRequest.from_dict(
            {
                "query": "Barber",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
            }
        )
