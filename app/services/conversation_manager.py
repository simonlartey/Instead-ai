from typing import Any

from app.models.conversation_message import MessageRole
from app.models.search_intent import SearchIntent
from app.models.search_session import SearchSession
from app.repositories.search_session import SearchSessionRepository
from app.schemas.search import (
    SearchFilters,
    SearchLocation,
)


class ConversationManager:
    """Create and retrieve search conversation sessions."""

    def __init__(
        self,
        session_repository: SearchSessionRepository,
    ) -> None:
        self.session_repository = session_repository

    def start_session(
        self,
        original_query: str,
        intent: SearchIntent,
        places: list[dict[str, Any]],
        ranked_places: list[dict[str, Any]],
        location: SearchLocation | None = None,
        filters: SearchFilters | None = None,
        assistant_response: str | None = None,
    ) -> SearchSession:
        session = SearchSession(
            original_query=original_query,
            intent=intent,
            location=location,
            filters=filters or SearchFilters(),
            places=places,
            ranked_places=ranked_places,
        )

        session.add_message(
            role=MessageRole.USER,
            content=original_query,
        )

        if assistant_response:
            session.add_message(
                role=MessageRole.ASSISTANT,
                content=assistant_response,
            )

        self.session_repository.save(session)

        return session

    def get_session(
        self,
        session_id: str,
    ) -> SearchSession | None:
        return self.session_repository.get(session_id)

    def continue_session(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
    ) -> SearchSession | None:
        session = self.get_session(session_id)

        if session is None:
            return None

        session.add_message(
            role=MessageRole.USER,
            content=user_message,
        )

        session.add_message(
            role=MessageRole.ASSISTANT,
            content=assistant_response,
        )

        self.session_repository.save(session)

        return session

    def get_conversation_history(
        self,
        session_id: str,
    ) -> list[dict[str, str]] | None:
        session = self.get_session(session_id)

        if session is None:
            return None

        return [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in session.conversation_history
        ]

    def get_session_details(
        self,
        session_id: str,
    ) -> dict[str, Any] | None:
        session = self.get_session(session_id)

        if session is None:
            return None

        return {
            "session_id": session.session_id,
            "query": session.original_query,
            "intent": {
                "search_query": session.intent.search_query,
                "category": session.intent.category,
                "cuisine": session.intent.cuisine,
                "price_levels": session.intent.price_levels,
                "preferences": session.intent.preferences,
                "max_distance_meters": (
                    session.intent.max_distance_meters
                ),
                "open_now": session.intent.open_now,
            },
            "conversation_history": [
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in session.conversation_history
            ],
            "results": session.ranked_places,
        }
