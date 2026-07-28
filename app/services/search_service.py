from uuid import uuid4

from app.models.search_execution_result import (
    SearchExecutionResult,
)
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
        execution = self.execute(search_request)

        session = None

        if self.conversation_manager is not None:
            session = self.conversation_manager.start_session(
                original_query=search_request.query,
                intent=execution.intent,
                location=search_request.location,
                filters=search_request.filters,
                places=execution.places,
                ranked_places=execution.ranked_places,
                assistant_response=execution.assistant_response,
            )

        return {
            "search_id": (
                session.session_id
                if session is not None
                else f"search_{uuid4().hex}"
            ),
            "query": search_request.query,
            "result_count": len(
                execution.ranked_places
            ),
            "results": execution.ranked_places,
            "assistant_response": (
                execution.assistant_response
            ),
            "filter_status": {
                "mode": execution.filter_mode,
                "title": execution.filter_title,
                "message": execution.filter_message,
            },
        }

    def execute(
        self,
        search_request: SearchRequest,
    ) -> SearchExecutionResult:
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

        filter_result = self.place_filter.apply_with_fallback(
            results,
            search_request.filters,
        )

        filtered_results = filter_result.places

        ranked_results = self.relevance_ranker.rank(
            query=intent.search_query,
            places=filtered_results,
            original_query=search_request.query,
        )

        assistant_response = self._generate_search_response(
            query=search_request.query,
            places=ranked_results,
        )

        return SearchExecutionResult(
            intent=intent,
            places=filtered_results,
            ranked_places=ranked_results,
            assistant_response=assistant_response,
            filter_mode=filter_result.mode,
            filter_title=filter_result.title,
            filter_message=filter_result.message,
        )

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
