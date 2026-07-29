from dataclasses import dataclass, field
from typing import Any

from app.models.search_intent import SearchIntent


@dataclass(frozen=True)
class SearchExecutionResult:
    """Results produced by the search pipeline before session storage."""

    intent: SearchIntent
    places: list[dict[str, Any]] = field(
        default_factory=list
    )
    ranked_places: list[dict[str, Any]] = field(
        default_factory=list
    )
    assistant_response: str | None = None
    filter_mode: str = "exact"
    filter_title: str | None = None
    filter_message: str | None = None
