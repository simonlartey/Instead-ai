from dataclasses import dataclass
from typing import Any

from app.schemas.search import SearchFilters


METERS_PER_MILE = 1609.344


@dataclass
class PlaceFilterResult:
    """Describe the outcome of applying search filters."""

    places: list[dict[str, Any]]
    mode: str
    title: str | None = None
    message: str | None = None


class PlaceFilter:
    """Apply validated search filters to normalized places."""

    def apply_with_fallback(
        self,
        places: list[dict[str, Any]],
        filters: SearchFilters,
    ) -> PlaceFilterResult:
        """
        Return exact matches when available.

        When filters remove every retrieved place, return the original
        candidates as clearly identified fallback alternatives instead
        of presenting the search as completely empty.
        """

        exact_matches = self.apply(
            places,
            filters,
        )

        if exact_matches:
            return PlaceFilterResult(
                places=exact_matches,
                mode="exact",
            )

        if not places:
            return PlaceFilterResult(
                places=[],
                mode="empty",
                title="No matching places found",
                message=(
                    "Try changing your wording or broadening "
                    "your search."
                ),
            )

        if not self._has_active_filters(filters):
            return PlaceFilterResult(
                places=[],
                mode="empty",
                title="No matching places found",
                message=(
                    "Try changing your wording or broadening "
                    "your search."
                ),
            )

        title, message = self._build_fallback_message(
            filters
        )

        return PlaceFilterResult(
            places=list(places),
            mode="fallback",
            title=title,
            message=message,
        )

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

    @staticmethod
    def _has_active_filters(
        filters: SearchFilters,
    ) -> bool:
        return bool(
            filters.price_levels
            or filters.open_now is not None
            or filters.minimum_rating is not None
            or filters.max_distance_meters is not None
        )

    @staticmethod
    def _build_fallback_message(
        filters: SearchFilters,
    ) -> tuple[str, str]:
        active_filter_count = sum(
            (
                bool(filters.price_levels),
                filters.open_now is not None,
                filters.minimum_rating is not None,
                filters.max_distance_meters is not None,
            )
        )

        if active_filter_count > 1:
            return (
                "No exact matches for every selected filter",
                (
                    "Showing the most relevant nearby alternatives. "
                    "Some selected details could not be verified."
                ),
            )

        if filters.price_levels:
            return (
                "Selected pricing could not be verified",
                (
                    "Showing relevant alternatives because the "
                    "retrieved places did not include verified pricing "
                    "in the selected range."
                ),
            )

        if filters.open_now is not None:
            return (
                "Matching hours could not be confirmed",
                (
                    "Showing relevant alternatives because no place "
                    "had confirmed hours matching this filter."
                ),
            )

        if filters.minimum_rating is not None:
            return (
                "No places met the selected rating",
                (
                    "Showing the highest-ranked nearby alternatives "
                    "instead."
                ),
            )

        return (
            "No places were found within that distance",
            (
                "Showing the closest relevant alternatives instead."
            ),
        )
