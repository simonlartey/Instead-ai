from dataclasses import dataclass
from typing import Any


class SearchValidationError(ValueError):
    """Raised when search request data is invalid."""


@dataclass(frozen=True)
class SearchLocation:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class SearchFilters:
    price_levels: tuple[int, ...] = ()
    open_now: bool | None = None
    minimum_rating: float | None = None
    max_distance_meters: int | None = None

    @classmethod
    def from_dict(cls, data: Any) -> "SearchFilters":
        if data is None:
            return cls()

        if not isinstance(data, dict):
            raise SearchValidationError(
                "The filters field must be an object."
            )

        price_levels = cls._parse_price_levels(
            data.get("price_levels")
        )
        open_now = cls._parse_open_now(
            data.get("open_now")
        )
        minimum_rating = cls._parse_minimum_rating(
            data.get("minimum_rating")
        )
        max_distance_meters = cls._parse_max_distance_meters(
            data.get("max_distance_meters")
        )

        return cls(
            price_levels=price_levels,
            open_now=open_now,
            minimum_rating=minimum_rating,
            max_distance_meters=max_distance_meters,
        )

    @staticmethod
    def _parse_price_levels(value: Any) -> tuple[int, ...]:
        if value is None:
            return ()

        if not isinstance(value, list):
            raise SearchValidationError(
                "Filter price_levels must be an array."
            )

        normalized_levels = []

        for price_level in value:
            if (
                isinstance(price_level, bool)
                or not isinstance(price_level, int)
            ):
                raise SearchValidationError(
                    "Each price level must be an integer."
                )

            if not 1 <= price_level <= 4:
                raise SearchValidationError(
                    "Price levels must be between 1 and 4."
                )

            if price_level not in normalized_levels:
                normalized_levels.append(price_level)

        return tuple(sorted(normalized_levels))

    @staticmethod
    def _parse_open_now(value: Any) -> bool | None:
        if value is None:
            return None

        if not isinstance(value, bool):
            raise SearchValidationError(
                "Filter open_now must be a boolean."
            )

        return value

    @staticmethod
    def _parse_minimum_rating(
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise SearchValidationError(
                "Filter minimum_rating must be a number."
            )

        if not 0 <= value <= 5:
            raise SearchValidationError(
                "Minimum rating must be between 0 and 5."
            )

        return float(value)

    @staticmethod
    def _parse_max_distance_meters(
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        if isinstance(value, bool) or not isinstance(
            value,
            int,
        ):
            raise SearchValidationError(
                "Filter max_distance_meters must be an integer."
            )

        if not 1 <= value <= 50000:
            raise SearchValidationError(
                "Maximum distance must be between 1 and 50000 meters."
            )

        return value


@dataclass(frozen=True)
class SearchRequest:
    query: str
    location: SearchLocation | None = None
    filters: SearchFilters = SearchFilters()

    @classmethod
    def from_dict(cls, data: Any) -> "SearchRequest":
        if not isinstance(data, dict):
            raise SearchValidationError(
                "Request body must be a JSON object."
            )

        raw_query = data.get("query")

        if not isinstance(raw_query, str):
            raise SearchValidationError(
                "The query field must be a string."
            )

        query = raw_query.strip()

        if not query:
            raise SearchValidationError(
                "Please enter a search query."
            )

        if len(query) > 500:
            raise SearchValidationError(
                "The search query must be 500 characters or fewer."
            )

        filters = SearchFilters.from_dict(
            data.get("filters")
        )

        raw_location = data.get("location")

        if raw_location is None:
            return cls(
                query=query,
                filters=filters,
            )

        if not isinstance(raw_location, dict):
            raise SearchValidationError(
                "The location field must be an object."
            )

        latitude = raw_location.get("latitude")
        longitude = raw_location.get("longitude")

        if isinstance(latitude, bool) or not isinstance(
            latitude,
            (int, float),
        ):
            raise SearchValidationError(
                "Location latitude must be a number."
            )

        if isinstance(longitude, bool) or not isinstance(
            longitude,
            (int, float),
        ):
            raise SearchValidationError(
                "Location longitude must be a number."
            )

        if not -90 <= latitude <= 90:
            raise SearchValidationError(
                "Latitude must be between -90 and 90."
            )

        if not -180 <= longitude <= 180:
            raise SearchValidationError(
                "Longitude must be between -180 and 180."
            )

        return cls(
            query=query,
            location=SearchLocation(
                latitude=float(latitude),
                longitude=float(longitude),
            ),
            filters=filters,
        )
