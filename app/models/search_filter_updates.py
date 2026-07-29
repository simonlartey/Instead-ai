from dataclasses import dataclass
from typing import Any

from app.schemas.search import (
    SearchFilters,
    SearchValidationError,
)


@dataclass(frozen=True)
class SearchFilterUpdates:
    """Represent validated partial changes to search filters."""

    price_levels: tuple[int, ...] | None = None
    open_now: bool | None = None
    minimum_rating: float | None = None
    max_distance_meters: int | None = None

    @classmethod
    def from_dict(
        cls,
        data: Any,
    ) -> "SearchFilterUpdates":
        if not isinstance(data, dict):
            raise SearchValidationError(
                "Filter updates must be an object."
            )

        price_levels = None

        if "price_levels" in data:
            price_levels = (
                SearchFilters._parse_price_levels(
                    data["price_levels"]
                )
            )

        open_now = None

        if "open_now" in data:
            open_now = SearchFilters._parse_open_now(
                data["open_now"]
            )

        minimum_rating = None

        if "minimum_rating" in data:
            minimum_rating = (
                SearchFilters._parse_minimum_rating(
                    data["minimum_rating"]
                )
            )

        max_distance_meters = None

        if "max_distance_meters" in data:
            max_distance_meters = (
                SearchFilters._parse_max_distance_meters(
                    data["max_distance_meters"]
                )
            )

        return cls(
            price_levels=price_levels,
            open_now=open_now,
            minimum_rating=minimum_rating,
            max_distance_meters=max_distance_meters,
        )

    def apply(
        self,
        current_filters: SearchFilters,
    ) -> SearchFilters:
        """Merge supplied updates into an existing filter set."""

        return SearchFilters(
            price_levels=(
                self.price_levels
                if self.price_levels is not None
                else current_filters.price_levels
            ),
            open_now=(
                self.open_now
                if self.open_now is not None
                else current_filters.open_now
            ),
            minimum_rating=(
                self.minimum_rating
                if self.minimum_rating is not None
                else current_filters.minimum_rating
            ),
            max_distance_meters=(
                self.max_distance_meters
                if self.max_distance_meters is not None
                else current_filters.max_distance_meters
            ),
        )

    def has_updates(self) -> bool:
        return any(
            (
                self.price_levels is not None,
                self.open_now is not None,
                self.minimum_rating is not None,
                self.max_distance_meters is not None,
            )
        )
