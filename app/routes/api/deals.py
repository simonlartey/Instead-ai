from flask import Blueprint, jsonify, request

from app.models.student_deal import StudentDeal
from app.schemas.student_deal import (
    DealValidationError,
    StudentDealSubmission,
)
from app.services.student_deal_service import (
    StudentDealService,
)


deals_api_bp = Blueprint(
    "deals_api",
    __name__,
    url_prefix="/api/v1",
)


def _serialize_public_deal(
    deal: StudentDeal,
) -> dict:
    """Serialize a deal for the student-facing API."""

    return {
        "id": deal.id,
        "business_name": deal.business_name,
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
        "is_featured": deal.is_featured,
    }


@deals_api_bp.post("/deals")
def submit_student_deal():
    """Accept a student deal submission from a local business."""

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
        submission = StudentDealSubmission.from_dict(
            request.get_json(silent=True)
        )
    except DealValidationError as error:
        return jsonify(
            {
                "error": {
                    "code": "invalid_deal_submission",
                    "message": str(error),
                }
            }
        ), 400

    service = StudentDealService()
    deal = service.submit_business_deal(submission)

    return jsonify(
        {
            "deal": {
                "id": deal.id,
                "status": deal.status.value,
            },
            "message": (
                "Your deal was submitted for review."
            ),
        }
    ), 201


@deals_api_bp.get("/deals")
def list_student_deals():
    """Return approved student deals that are currently active."""

    service = StudentDealService()
    deals = service.list_active_deals()

    serialized_deals = [
        _serialize_public_deal(deal)
        for deal in deals
    ]

    return jsonify(
        {
            "deal_count": len(serialized_deals),
            "deals": serialized_deals,
        }
    ), 200
