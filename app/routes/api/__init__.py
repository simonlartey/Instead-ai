from app.routes.api.deal_moderation import (
    deal_moderation_api_bp,
)
from app.routes.api.deals import deals_api_bp
from app.routes.api.search import search_api_bp

__all__ = [
    "deal_moderation_api_bp",
    "deals_api_bp",
    "search_api_bp",
]
