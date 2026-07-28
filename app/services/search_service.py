from uuid import uuid4

from app.models.search_intent import SearchIntent
from app.providers.assistant.base import AssistantProvider
from app.providers.places.base import PlacesProvider
from app.schemas.search import SearchRequest
from app.services.conversation_manager import ConversationManager
from app.services.place_filter import PlaceFilter
from app.services.place_relevance_ranker import (
    PlaceRelevanceRanker,
)


class SearchService:
    """Coordinate place retrieval, ranking, and response creation."""

    def __init__(
        self,
        places_provider: PlacesProvider,
        assistant_provider: AssistantProvider | None = None,
        conversation_manager: ConversationManager | None = None,
        relevance_ranker: PlaceRelevanceRanker | None = None,
        place_filter: PlaceFilter | None = None,
    ):
        self.places_provider = places_provider
        self.assistant_provider = assistant_provider
        self.conversation_manager = conversation_manager
        self.relevance_ranker = (
            relevance_ranker or PlaceRelevanceRanker()
        )
        self.place_filter = place_filter or PlaceFilter()

    def search(self, search_request: SearchRequest) -> dict:
        latitude = None
        longitude = None

        if search_request.location is not None:
            latitude = search_request.location.latitude
            longitude = search_request.location.longitude

        intent = self._parse_search_intent(search_request.query)

        results = self.places_provider.search(
            query=intent.search_query,
            latitude=latitude,
            longitude=longitude,
        )

        filtered_results = self.place_filter.apply(
            results,
            search_request.filters,
        )

        ranked_results = self.relevance_ranker.rank(
            query=intent.search_query,
            places=filtered_results,
            original_query=search_request.query,
        )

        assistant_response = self._generate_search_response(
            query=search_request.query,
            places=ranked_results,
        )

        session = None

        if self.conversation_manager is not None:
            session = self.conversation_manager.start_session(
                original_query=search_request.query,
                intent=intent,
                places=filtered_results,
                ranked_places=ranked_results,
                assistant_response=assistant_response,
            )

        return {
            "search_id": (
                session.session_id
                if session is not None
                else f"search_{uuid4().hex}"
            ),
            "query": search_request.query,
            "result_count": len(ranked_results),
            "results": ranked_results,
            "assistant_response": assistant_response,
        }

    def _parse_search_intent(
        self,
        query: str,
    ) -> SearchIntent:
        if self.assistant_provider is not None:
            try:
                return self.assistant_provider.parse_search_intent(query)
            except Exception:
                pass

        return SearchIntent(
            original_query=query,
            search_query=query,
        )

    def _generate_search_response(
        self,
        query: str,
        places: list[dict],
    ) -> str | None:
        if self.assistant_provider is None:
            return None

        try:
            return self.assistant_provider.generate_search_response(
                query=query,
                places=places,
            )
        except Exception:
            return None
