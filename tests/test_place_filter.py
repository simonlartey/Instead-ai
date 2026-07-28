from app.schemas.search import SearchFilters
from app.services.place_filter import (
    PlaceFilter,
    PlaceFilterResult,
)


def make_place(
    *,
    place_id: str,
    price_level=2,
    open_now=True,
    rating=4.5,
    distance_miles=1.0,
):
    return {
        "id": place_id,
        "name": f"Place {place_id}",
        "price_level": price_level,
        "open_now": open_now,
        "rating": rating,
        "distance_miles": distance_miles,
    }


def test_place_filter_returns_all_places_without_filters():
    places = [
        make_place(place_id="first"),
        make_place(place_id="second"),
    ]

    results = PlaceFilter().apply(
        places,
        SearchFilters(),
    )

    assert results == places


def test_place_filter_filters_by_price_level():
    places = [
        make_place(
            place_id="inexpensive",
            price_level=1,
        ),
        make_place(
            place_id="moderate",
            price_level=2,
        ),
        make_place(
            place_id="expensive",
            price_level=3,
        ),
    ]

    results = PlaceFilter().apply(
        places,
        SearchFilters(
            price_levels=(1, 2),
        ),
    )

    assert [
        place["id"]
        for place in results
    ] == [
        "inexpensive",
        "moderate",
    ]


def test_place_filter_filters_by_open_status():
    places = [
        make_place(
            place_id="open",
            open_now=True,
        ),
        make_place(
            place_id="closed",
            open_now=False,
        ),
    ]

    results = PlaceFilter().apply(
        places,
        SearchFilters(
            open_now=True,
        ),
    )

    assert [
        place["id"]
        for place in results
    ] == ["open"]


def test_place_filter_can_select_closed_places():
    places = [
        make_place(
            place_id="open",
            open_now=True,
        ),
        make_place(
            place_id="closed",
            open_now=False,
        ),
    ]

    results = PlaceFilter().apply(
        places,
        SearchFilters(
            open_now=False,
        ),
    )

    assert [
        place["id"]
        for place in results
    ] == ["closed"]


def test_place_filter_filters_by_minimum_rating():
    places = [
        make_place(
            place_id="highly-rated",
            rating=4.7,
        ),
        make_place(
            place_id="boundary",
            rating=4.5,
        ),
        make_place(
            place_id="below-boundary",
            rating=4.4,
        ),
    ]

    results = PlaceFilter().apply(
        places,
        SearchFilters(
            minimum_rating=4.5,
        ),
    )

    assert [
        place["id"]
        for place in results
    ] == [
        "highly-rated",
        "boundary",
    ]


def test_place_filter_filters_by_maximum_distance():
    places = [
        make_place(
            place_id="nearby",
            distance_miles=0.5,
        ),
        make_place(
            place_id="boundary",
            distance_miles=1.0,
        ),
        make_place(
            place_id="far-away",
            distance_miles=2.0,
        ),
    ]

    results = PlaceFilter().apply(
        places,
        SearchFilters(
            max_distance_meters=1610,
        ),
    )

    assert [
        place["id"]
        for place in results
    ] == [
        "nearby",
        "boundary",
    ]


def test_place_filter_combines_filters():
    places = [
        make_place(
            place_id="full-match",
            price_level=2,
            open_now=True,
            rating=4.8,
            distance_miles=1.0,
        ),
        make_place(
            place_id="wrong-price",
            price_level=3,
            open_now=True,
            rating=4.8,
            distance_miles=1.0,
        ),
        make_place(
            place_id="closed",
            price_level=2,
            open_now=False,
            rating=4.8,
            distance_miles=1.0,
        ),
        make_place(
            place_id="low-rating",
            price_level=2,
            open_now=True,
            rating=4.2,
            distance_miles=1.0,
        ),
        make_place(
            place_id="too-far",
            price_level=2,
            open_now=True,
            rating=4.8,
            distance_miles=3.0,
        ),
    ]

    results = PlaceFilter().apply(
        places,
        SearchFilters(
            price_levels=(2,),
            open_now=True,
            minimum_rating=4.5,
            max_distance_meters=2500,
        ),
    )

    assert [
        place["id"]
        for place in results
    ] == ["full-match"]


def test_place_filter_excludes_missing_values_for_active_filters():
    places = [
        make_place(
            place_id="complete",
        ),
        make_place(
            place_id="missing-price",
            price_level=None,
        ),
        make_place(
            place_id="missing-open-status",
            open_now=None,
        ),
        make_place(
            place_id="missing-rating",
            rating=None,
        ),
        make_place(
            place_id="missing-distance",
            distance_miles=None,
        ),
    ]

    results = PlaceFilter().apply(
        places,
        SearchFilters(
            price_levels=(2,),
            open_now=True,
            minimum_rating=4.0,
            max_distance_meters=2000,
        ),
    )

    assert [
        place["id"]
        for place in results
    ] == ["complete"]


def test_place_filter_does_not_modify_original_places():
    places = [
        make_place(place_id="first"),
        make_place(
            place_id="second",
            rating=3.0,
        ),
    ]

    original_places = [
        place.copy()
        for place in places
    ]

    PlaceFilter().apply(
        places,
        SearchFilters(
            minimum_rating=4.0,
        ),
    )

    assert places == original_places


def test_place_filter_result_returns_exact_matches():
    places = [
        make_place(
            place_id="affordable",
            price_level=1,
        ),
        make_place(
            place_id="premium",
            price_level=4,
        ),
    ]

    result = PlaceFilter().apply_with_fallback(
        places,
        SearchFilters(
            price_levels=(1,),
        ),
    )

    assert isinstance(result, PlaceFilterResult)
    assert result.mode == "exact"
    assert [
        place["id"]
        for place in result.places
    ] == ["affordable"]
    assert result.title is None
    assert result.message is None


def test_place_filter_returns_price_fallback_when_no_exact_match():
    places = [
        make_place(
            place_id="unknown-price",
            price_level=None,
        ),
        make_place(
            place_id="moderate",
            price_level=2,
        ),
    ]

    result = PlaceFilter().apply_with_fallback(
        places,
        SearchFilters(
            price_levels=(1,),
        ),
    )

    assert result.mode == "fallback"
    assert result.places == places
    assert result.title == (
        "Selected pricing could not be verified"
    )
    assert "verified pricing" in result.message


def test_place_filter_returns_open_status_fallback():
    places = [
        make_place(
            place_id="unknown-hours",
            open_now=None,
        ),
        make_place(
            place_id="closed",
            open_now=False,
        ),
    ]

    result = PlaceFilter().apply_with_fallback(
        places,
        SearchFilters(
            open_now=True,
        ),
    )

    assert result.mode == "fallback"
    assert result.places == places
    assert result.title == (
        "Matching hours could not be confirmed"
    )


def test_place_filter_returns_rating_fallback():
    places = [
        make_place(
            place_id="first",
            rating=4.3,
        ),
        make_place(
            place_id="second",
            rating=4.2,
        ),
    ]

    result = PlaceFilter().apply_with_fallback(
        places,
        SearchFilters(
            minimum_rating=4.5,
        ),
    )

    assert result.mode == "fallback"
    assert result.places == places
    assert result.title == (
        "No places met the selected rating"
    )


def test_place_filter_returns_distance_fallback():
    places = [
        make_place(
            place_id="first",
            distance_miles=2.0,
        ),
        make_place(
            place_id="second",
            distance_miles=3.0,
        ),
    ]

    result = PlaceFilter().apply_with_fallback(
        places,
        SearchFilters(
            max_distance_meters=1600,
        ),
    )

    assert result.mode == "fallback"
    assert result.places == places
    assert result.title == (
        "No places were found within that distance"
    )


def test_place_filter_returns_combined_filter_fallback():
    places = [
        make_place(
            place_id="first",
            price_level=None,
            open_now=None,
        )
    ]

    result = PlaceFilter().apply_with_fallback(
        places,
        SearchFilters(
            price_levels=(1,),
            open_now=True,
        ),
    )

    assert result.mode == "fallback"
    assert result.places == places
    assert result.title == (
        "No exact matches for every selected filter"
    )
    assert "could not be verified" in result.message


def test_place_filter_returns_empty_when_provider_found_nothing():
    result = PlaceFilter().apply_with_fallback(
        [],
        SearchFilters(
            price_levels=(1,),
        ),
    )

    assert result.mode == "empty"
    assert result.places == []
    assert result.title == "No matching places found"


def test_place_filter_returns_empty_without_filters_or_places():
    result = PlaceFilter().apply_with_fallback(
        [],
        SearchFilters(),
    )

    assert result.mode == "empty"
    assert result.places == []
