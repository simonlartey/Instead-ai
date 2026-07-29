from flask import Blueprint, jsonify

from app.authentication import admin_api_required
from app.models.student_deal import StudentDeal
from app.services.student_deal_service import (
    InvalidDealStatusTransitionError,
    StudentDealNotFoundError,
    StudentDealService,
)


deal_moderation_api_bp = Blueprint(
    "deal_moderation_api",
    __name__,
    url_prefix="/api/v1/admin/deals",
)


def _serialize_pending_deal(
    deal: StudentDeal,
) -> dict:
    """Serialize a complete deal submission for admin review."""

    return {
        "id": deal.id,
        "business_name": deal.business_name,
        "business_email": deal.business_email,
        "business_url": deal.business_url,
        "deal_url": deal.deal_url,
        "title": deal.title,
        "description": deal.description,
        "category": deal.category.value,
        "discount_text": deal.discount_text,
        "location_name": deal.location_name,
        "redemption_instructions": (
            deal.redemption_instructions
        ),
        "terms": deal.terms,
        "promo_code": deal.promo_code,
        "starts_at": (
            deal.starts_at.isoformat()
            if deal.starts_at is not None
            else None
        ),
        "expires_at": (
            deal.expires_at.isoformat()
            if deal.expires_at is not None
            else None
        ),
        "source": deal.source.value,
        "status": deal.status.value,
        "is_featured": deal.is_featured,
        "created_at": deal.created_at.isoformat(),
        "updated_at": deal.updated_at.isoformat(),
    }


def _moderation_error_response(
    error: Exception,
):
    """Convert moderation service errors to API responses."""

    if isinstance(error, StudentDealNotFoundError):
        return jsonify(
            {
                "error": {
                    "code": "deal_not_found",
                    "message": str(error),
                }
            }
        ), 404

    if isinstance(
        error,
        InvalidDealStatusTransitionError,
    ):
        return jsonify(
            {
                "error": {
                    "code": "invalid_status_transition",
                    "message": str(error),
                }
            }
        ), 409

    raise error


@deal_moderation_api_bp.get("/pending")
@admin_api_required
def list_pending_deals():
    """Return student deal submissions awaiting review."""

    deals = StudentDealService().list_pending_deals()

    serialized_deals = [
        _serialize_pending_deal(deal)
        for deal in deals
    ]

    return jsonify(
        {
            "deal_count": len(serialized_deals),
            "deals": serialized_deals,
        }
    ), 200


@deal_moderation_api_bp.post(
    "/<int:deal_id>/approve"
)
@admin_api_required
def approve_deal(deal_id: int):
    """Approve a pending student deal."""

    try:
        deal = StudentDealService().approve_deal(
            deal_id
        )
    except (
        StudentDealNotFoundError,
        InvalidDealStatusTransitionError,
    ) as error:
        return _moderation_error_response(error)

    return jsonify(
        {
            "deal": {
                "id": deal.id,
                "status": deal.status.value,
            },
            "message": "The student deal was approved.",
        }
    ), 200


@deal_moderation_api_bp.post(
    "/<int:deal_id>/reject"
)
@admin_api_required
def reject_deal(deal_id: int):
    """Reject a pending student deal."""

    try:
        deal = StudentDealService().reject_deal(
            deal_id
        )
    except (
        StudentDealNotFoundError,
        InvalidDealStatusTransitionError,
    ) as error:
        return _moderation_error_response(error)

    return jsonify(
        {
            "deal": {
                "id": deal.id,
                "status": deal.status.value,
            },
            "message": "The student deal was rejected.",
        }
    ), 200
