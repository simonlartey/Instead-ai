from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.student_deal import (
    DealCategory,
    DealSource,
    DealStatus,
    StudentDeal,
)


def build_student_deal(**overrides):
    """Create a valid student deal for tests."""

    values = {
        "business_name": "Downtown Coffee",
        "title": "Student coffee discount",
        "description": (
            "Students receive a discount on any regular drink."
        ),
        "category": DealCategory.COFFEE,
        "discount_text": "15% off",
        "location_name": "Waterville, Maine",
        "redemption_instructions": (
            "Show a valid student ID before payment."
        ),
        "business_email": "owner@example.com",
    }

    values.update(overrides)

    return StudentDeal(**values)


def test_student_deal_defaults_to_pending_business_submission(app):
    with app.app_context():
        deal = build_student_deal()

        db.session.add(deal)
        db.session.commit()

        assert deal.id is not None
        assert deal.status is DealStatus.PENDING
        assert deal.source is DealSource.BUSINESS
        assert deal.is_featured is False
        assert deal.created_at is not None
        assert deal.updated_at is not None


def test_student_deal_stores_submission_details(app):
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    with app.app_context():
        deal = build_student_deal(
            category=DealCategory.FOOD,
            promo_code="STUDENT15",
            terms="Dine-in orders only.",
            expires_at=expires_at,
        )

        db.session.add(deal)
        db.session.commit()

        stored_deal = db.session.get(StudentDeal, deal.id)

        assert stored_deal is not None
        assert stored_deal.business_name == "Downtown Coffee"
        assert stored_deal.category is DealCategory.FOOD
        assert stored_deal.promo_code == "STUDENT15"
        assert stored_deal.terms == "Dine-in orders only."
        assert stored_deal.expires_at is not None


def test_student_deal_can_be_approved(app):
    with app.app_context():
        deal = build_student_deal()

        db.session.add(deal)
        db.session.commit()

        deal.status = DealStatus.APPROVED
        db.session.commit()

        stored_deal = db.session.get(StudentDeal, deal.id)

        assert stored_deal.status is DealStatus.APPROVED


def test_student_deal_supports_instead_verified_source(app):
    with app.app_context():
        deal = build_student_deal(
            source=DealSource.INSTEAD,
            status=DealStatus.APPROVED,
        )

        db.session.add(deal)
        db.session.commit()

        stored_deal = db.session.get(StudentDeal, deal.id)

        assert stored_deal.source is DealSource.INSTEAD
        assert stored_deal.status is DealStatus.APPROVED


def test_student_deal_repr_contains_business_and_status(app):
    with app.app_context():
        deal = build_student_deal()

        db.session.add(deal)
        db.session.commit()

        representation = repr(deal)

        assert "Downtown Coffee" in representation
        assert "pending" in representation
