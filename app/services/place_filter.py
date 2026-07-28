from typing import Any

from app.schemas.search import SearchFilters


METERS_PER_MILE = 1609.344


class PlaceFilter:
    """Apply validated search filters to normalized places."""

    def apply(
        self,
        places: list[dict[str, Any]],
        filters: SearchFilters,
    ) -> list[dict[str, Any]]:
        return [
            place
            for place in places
            if self._matches_filters(place, filters)
        ]

    def _matches_filters(
        self,
        place: dict[str, Any],
        filters: SearchFilters,
    ) -> bool:
        return (
            self._matches_price_levels(
                place,
                filters.price_levels,
            )
            and self._matches_open_status(
                place,
                filters.open_now,
            )
            and self._matches_minimum_rating(
                place,
                filters.minimum_rating,
            )
            and self._matches_maximum_distance(
                place,
                filters.max_distance_meters,
            )
        )

    @staticmethod
    def _matches_price_levels(
        place: dict[str, Any],
        price_levels: tuple[int, ...],
    ) -> bool:
        if not price_levels:
            return True

        price_level = place.get("price_level")

        if (
            isinstance(price_level, bool)
            or not isinstance(price_level, int)
        ):
            return False

        return price_level in price_levels

    @staticmethod
    def _matches_open_status(
        place: dict[str, Any],
        open_now: bool | None,
    ) -> bool:
        if open_now is None:
            return True

        place_open_now = place.get("open_now")

        if not isinstance(place_open_now, bool):
            return False

        return place_open_now is open_now

    @staticmethod
    def _matches_minimum_rating(
        place: dict[str, Any],
        minimum_rating: float | None,
    ) -> bool:
        if minimum_rating is None:
            return True

        rating = place.get("rating")

        if isinstance(rating, bool) or not isinstance(
            rating,
            (int, float),
        ):
            return False

        return float(rating) >= minimum_rating

    @staticmethod
    def _matches_maximum_distance(
        place: dict[str, Any],
        max_distance_meters: int | None,
    ) -> bool:
        if max_distance_meters is None:
            return True

        distance_miles = place.get("distance_miles")

        if isinstance(distance_miles, bool) or not isinstance(
            distance_miles,
            (int, float),
        ):
            return False

        distance_meters = (
            float(distance_miles) * METERS_PER_MILE
        )

        return distance_meters <= max_distance_meters
