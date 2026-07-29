from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    request,
)

from app.models.conversation_action import (
    ConversationAction,
)
from app.providers.places.errors import PlacesProviderError
from app.schemas.discovery import DiscoveryRequest
from app.schemas.search import (
    SearchFilters,
    SearchRequest,
    SearchValidationError,
)
from app.services.discovery_service import DiscoveryService
from app.services.search_service import SearchService


def _serialize_search_filters(
    filters: SearchFilters,
) -> dict:
    """Serialize active search filters for API responses."""

    return {
        "price_levels": list(
            filters.price_levels
        ),
        "open_now": filters.open_now,
        "minimum_rating": filters.minimum_rating,
        "max_distance_meters": (
            filters.max_distance_meters
        ),
    }


search_api_bp = Blueprint(
    "search_api",
    __name__,
    url_prefix="/api/v1",
)


@search_api_bp.post("/search")
def search_places():
    """Return normalized place recommendations for a user query."""

    if not request.is_json:
        return jsonify(
            {
                "error": {
                    "code": "invalid_content_type",
                    "message": "Request body must use application/json.",
                }
            }
        ), 415

    try:
        search_request = SearchRequest.from_dict(
            request.get_json(silent=True)
        )
    except SearchValidationError as error:
        return jsonify(
            {
                "error": {
                    "code": "invalid_search_request",
                    "message": str(error),
                }
            }
        ), 400

    places_provider = current_app.extensions["places_provider"]
    assistant_provider = current_app.extensions["assistant_provider"]
    conversation_manager = current_app.extensions[
        "conversation_manager"
    ]

    service = SearchService(
        places_provider=places_provider,
        assistant_provider=assistant_provider,
        conversation_manager=conversation_manager,
    )

    try:
        response = service.search(search_request)
    except PlacesProviderError:
        current_app.logger.exception(
            "Places provider failed during search."
        )

        return jsonify(
            {
                "error": {
                    "code": "places_provider_unavailable",
                    "message": (
                        "Local recommendations are temporarily unavailable."
                    ),
                }
            }
        ), 503

    return jsonify(response), 200


@search_api_bp.get("/search/<session_id>")
def get_search_session(session_id: str):
    """Return a previous search conversation session."""

    conversation_manager = current_app.extensions[
        "conversation_manager"
    ]

    session = conversation_manager.get_session_details(
        session_id
    )

    if session is None:
        return jsonify(
            {
                "error": {
                    "code": "search_session_not_found",
                    "message": (
                        "The requested search session does not exist."
                    ),
                }
            }
        ), 404

    return jsonify(session), 200


@search_api_bp.post("/search/<session_id>/continue")
def continue_search(session_id: str):
    """Continue an existing search conversation."""

    if not request.is_json:
        return jsonify(
            {
                "error": {
                    "code": "invalid_content_type",
                    "message": "Request body must use application/json.",
                }
            }
        ), 415

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        data = {}

    message = data.get("message")

    if not isinstance(message, str) or not message.strip():
        return jsonify(
            {
                "error": {
                    "code": "invalid_message",
                    "message": (
                        "Conversation message must be a non-empty string."
                    ),
                }
            }
        ), 400

    message = message.strip()

    conversation_manager = current_app.extensions[
        "conversation_manager"
    ]

    assistant_provider = current_app.extensions[
        "assistant_provider"
    ]

    places_provider = current_app.extensions[
        "places_provider"
    ]

    conversation_orchestrator = current_app.extensions[
        "conversation_orchestrator"
    ]

    session = conversation_manager.get_session(
        session_id
    )

    if session is None:
        return jsonify(
            {
                "error": {
                    "code": "search_session_not_found",
                    "message": "Session does not exist.",
                }
            }
        ), 404

    try:
        decision = conversation_orchestrator.decide(
            session=session,
            message=message,
        )
    except Exception:
        current_app.logger.exception(
            "Conversation decision failed."
        )

        return jsonify(
            {
                "error": {
                    "code": "conversation_decision_unavailable",
                    "message": (
                        "The search assistant could not interpret "
                        "that follow-up message."
                    ),
                }
            }
        ), 503

    if decision.action is ConversationAction.CLARIFY:
        clarification_question = (
            decision.clarification_question
        )

        conversation_manager.continue_session(
            session_id=session_id,
            user_message=message,
            assistant_response=clarification_question,
        )

        return jsonify(
            {
                "session_id": session_id,
                "action": decision.action.value,
                "response": clarification_question,
            }
        ), 200

    if decision.action is ConversationAction.REFINE_RESULTS:
        refined_filters = decision.filter_updates.apply(
            session.filters
        )

        search_service = SearchService(
            places_provider=places_provider,
            assistant_provider=assistant_provider,
            conversation_manager=conversation_manager,
        )

        search_request = SearchRequest(
            query=session.original_query,
            location=session.location,
            filters=refined_filters,
        )

        try:
            execution = search_service.execute(
                search_request
            )
        except PlacesProviderError:
            current_app.logger.exception(
                "Places provider failed during conversational refinement."
            )

            return jsonify(
                {
                    "error": {
                        "code": "places_provider_unavailable",
                        "message": (
                            "Local recommendations are "
                            "temporarily unavailable."
                        ),
                    }
                }
            ), 503

        assistant_response = (
            execution.assistant_response
            or "I refined the results for your request."
        )

        conversation_manager.replace_search_state(
            session_id=session_id,
            original_query=session.original_query,
            intent=execution.intent,
            places=execution.places,
            ranked_places=execution.ranked_places,
            user_message=message,
            assistant_response=assistant_response,
            filters=refined_filters,
        )

        return jsonify(
            {
                "session_id": session_id,
                "action": decision.action.value,
                "query": session.original_query,
                "result_count": len(
                    execution.ranked_places
                ),
                "results": execution.ranked_places,
                "response": assistant_response,
                "filters": _serialize_search_filters(
                    refined_filters
                ),
                "filter_status": {
                    "mode": execution.filter_mode,
                    "title": execution.filter_title,
                    "message": execution.filter_message,
                },
            }
        ), 200

    if decision.action is ConversationAction.RUN_NEW_SEARCH:
        search_service = SearchService(
            places_provider=places_provider,
            assistant_provider=assistant_provider,
            conversation_manager=conversation_manager,
        )

        search_request = SearchRequest(
            query=decision.rewritten_query,
            location=session.location,
            filters=session.filters,
        )

        try:
            execution = search_service.execute(
                search_request
            )
        except PlacesProviderError:
            current_app.logger.exception(
                "Places provider failed during conversational search."
            )

            return jsonify(
                {
                    "error": {
                        "code": "places_provider_unavailable",
                        "message": (
                            "Local recommendations are "
                            "temporarily unavailable."
                        ),
                    }
                }
            ), 503

        assistant_response = (
            execution.assistant_response
            or "I found updated results for your request."
        )

        conversation_manager.replace_search_state(
            session_id=session_id,
            original_query=decision.rewritten_query,
            intent=execution.intent,
            places=execution.places,
            ranked_places=execution.ranked_places,
            user_message=message,
            assistant_response=assistant_response,
        )

        return jsonify(
            {
                "session_id": session_id,
                "action": decision.action.value,
                "query": decision.rewritten_query,
                "result_count": len(
                    execution.ranked_places
                ),
                "results": execution.ranked_places,
                "response": assistant_response,
                "filters": _serialize_search_filters(
                    session.filters
                ),
                "filter_status": {
                    "mode": execution.filter_mode,
                    "title": execution.filter_title,
                    "message": execution.filter_message,
                },
            }
        ), 200

    if decision.action is not ConversationAction.ANSWER_EXISTING:
        return jsonify(
            {
                "error": {
                    "code": "conversation_action_not_supported",
                    "message": (
                        "This type of follow-up is not supported yet."
                    ),
                    "action": decision.action.value,
                }
            }
        ), 409

    history = conversation_manager.get_conversation_history(
        session_id
    ) or []

    try:
        response = assistant_provider.continue_conversation(
            history=history,
            message=message,
            places=session.ranked_places,
        )
    except Exception:
        current_app.logger.exception(
            "Assistant provider failed while continuing conversation."
        )

        return jsonify(
            {
                "error": {
                    "code": "assistant_provider_unavailable",
                    "message": (
                        "The search assistant is temporarily unavailable."
                    ),
                }
            }
        ), 503

    conversation_manager.continue_session(
        session_id=session_id,
        user_message=message,
        assistant_response=response,
    )

    return jsonify(
        {
            "session_id": session_id,
            "action": decision.action.value,
            "response": response,
        }
    ), 200


@search_api_bp.post("/discovery")
def get_discovery_collections():
    """Return location-aware discovery collections."""

    if not request.is_json:
        return jsonify(
            {
                "error": {
                    "code": "invalid_content_type",
                    "message": (
                        "Request body must use application/json."
                    ),
                }
            }
        ), 415

    try:
        discovery_request = DiscoveryRequest.from_dict(
            request.get_json(silent=True)
        )
    except SearchValidationError as error:
        return jsonify(
            {
                "error": {
                    "code": "invalid_discovery_request",
                    "message": str(error),
                }
            }
        ), 400

    discovery_cache = current_app.extensions[
        "discovery_cache"
    ]

    cache_key = discovery_cache.build_key(
        discovery_request.location.latitude,
        discovery_request.location.longitude,
    )

    cached_response = discovery_cache.get(
        cache_key
    )

    if cached_response is not None:
        return jsonify(cached_response), 200

    places_provider = current_app.extensions[
        "places_provider"
    ]

    service = DiscoveryService(
        places_provider=places_provider
    )

    try:
        response = service.discover(
            discovery_request
        )
    except PlacesProviderError:
        current_app.logger.exception(
            "Places provider failed during discovery."
        )

        return jsonify(
            {
                "error": {
                    "code": "discovery_unavailable",
                    "message": (
                        "Local discovery collections are "
                        "temporarily unavailable."
                    ),
                }
            }
        ), 503

    discovery_cache.set(
        cache_key,
        response,
    )

    return jsonify(response), 200


@search_api_bp.get("/place-photo")
def get_place_photo():
    """Resolve a Google Places photo without exposing the API key."""

    photo_name = request.args.get("name", "").strip()
    width_value = request.args.get("width", "800")

    try:
        max_width = int(width_value)
    except ValueError:
        return jsonify(
            {
                "error": {
                    "code": "invalid_photo_request",
                    "message": "Photo width must be an integer.",
                }
            }
        ), 400

    places_provider = current_app.extensions["places_provider"]

    get_photo_url = getattr(
        places_provider,
        "get_photo_url",
        None,
    )

    if not callable(get_photo_url):
        return jsonify(
            {
                "error": {
                    "code": "place_photos_unavailable",
                    "message": (
                        "Place photos are unavailable for "
                        "the configured provider."
                    ),
                }
            }
        ), 503

    try:
        photo_url = get_photo_url(
            photo_name,
            max_width=max_width,
        )
    except ValueError as error:
        return jsonify(
            {
                "error": {
                    "code": "invalid_photo_request",
                    "message": str(error),
                }
            }
        ), 400
    except PlacesProviderError:
        current_app.logger.exception(
            "Places provider failed while loading a photo."
        )

        return jsonify(
            {
                "error": {
                    "code": "place_photo_unavailable",
                    "message": (
                        "This place photo is temporarily "
                        "unavailable."
                    ),
                }
            }
        ), 503

    return redirect(photo_url, code=302)
