import pytest

from app.models.search_filter_updates import (
    SearchFilterUpdates,
)
from app.schemas.search import (
    SearchFilters,
    SearchValidationError,
)


def test_filter_updates_parse_supplied_fields():
    updates = SearchFilterUpdates.from_dict(
        {
            "price_levels": [2, 1, 2],
            "open_now": True,
            "minimum_rating": 4.5,
            "max_distance_meters": 2400,
        }
    )

    assert updates.price_levels == (1, 2)
    assert updates.open_now is True
    assert updates.minimum_rating == 4.5
    assert updates.max_distance_meters == 2400
    assert updates.has_updates() is True


def test_filter_updates_leave_missing_fields_unchanged():
    current_filters = SearchFilters(
        price_levels=(1, 2),
        open_now=False,
        minimum_rating=4.0,
        max_distance_meters=5000,
    )

    updates = SearchFilterUpdates.from_dict(
        {
            "minimum_rating": 4.7,
        }
    )

    merged_filters = updates.apply(
        current_filters
    )

    assert merged_filters == SearchFilters(
        price_levels=(1, 2),
        open_now=False,
        minimum_rating=4.7,
        max_distance_meters=5000,
    )


def test_filter_updates_replace_multiple_fields():
    current_filters = SearchFilters(
        price_levels=(3, 4),
        open_now=None,
        minimum_rating=3.5,
        max_distance_meters=8000,
    )

    updates = SearchFilterUpdates(
        price_levels=(1, 2),
        open_now=True,
        max_distance_meters=1600,
    )

    merged_filters = updates.apply(
        current_filters
    )

    assert merged_filters == SearchFilters(
        price_levels=(1, 2),
        open_now=True,
        minimum_rating=3.5,
        max_distance_meters=1600,
    )


def test_empty_filter_updates_preserve_all_filters():
    current_filters = SearchFilters(
        price_levels=(2,),
        open_now=True,
        minimum_rating=4.2,
        max_distance_meters=3200,
    )

    updates = SearchFilterUpdates.from_dict({})

    assert updates.has_updates() is False
    assert updates.apply(current_filters) == (
        current_filters
    )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            [],
            "Filter updates must be an object",
        ),
        (
            {
                "price_levels": [5],
            },
            "Price levels must be between 1 and 4",
        ),
        (
            {
                "open_now": "yes",
            },
            "Filter open_now must be a boolean",
        ),
        (
            {
                "minimum_rating": 6,
            },
            "Minimum rating must be between 0 and 5",
        ),
        (
            {
                "max_distance_meters": 0,
            },
            "Maximum distance must be between 1 and 50000 meters",
        ),
    ],
)
def test_filter_updates_reject_invalid_values(
    payload,
    message,
):
    with pytest.raises(
        SearchValidationError,
        match=message,
    ):
        SearchFilterUpdates.from_dict(payload)
