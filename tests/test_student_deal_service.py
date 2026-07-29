from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models.student_deal import (
    DealCategory,
    DealSource,
    DealStatus,
    StudentDeal,
)
from app.schemas.student_deal import StudentDealSubmission
from app.services.student_deal_service import (
    StudentDealService,
)


REFERENCE_TIME = datetime(
    2026,
    8,
    15,
    12,
    0,
    tzinfo=timezone.utc,
)


def build_submission(**overrides):
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
        "terms": None,
        "promo_code": None,
        "starts_at": None,
        "expires_at": None,
    }

    values.update(overrides)

    return StudentDealSubmission(**values)


def build_deal(**overrides):
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
        "source": DealSource.BUSINESS,
        "status": DealStatus.APPROVED,
        "is_featured": False,
        "starts_at": None,
        "expires_at": None,
    }

    values.update(overrides)

    return StudentDeal(**values)


def test_submit_business_deal_creates_pending_record(app):
    with app.app_context():
        service = StudentDealService()

        deal = service.submit_business_deal(
            build_submission(
                promo_code="STUDENT15",
                terms="Valid for in-store purchases only.",
            )
        )

        stored_deal = db.session.get(
            StudentDeal,
            deal.id,
        )

        assert stored_deal is not None
        assert stored_deal.status is DealStatus.PENDING
        assert stored_deal.source is DealSource.BUSINESS
        assert stored_deal.is_featured is False
        assert stored_deal.promo_code == "STUDENT15"
        assert (
            stored_deal.terms
            == "Valid for in-store purchases only."
        )


def test_submit_business_deal_copies_submission_fields(app):
    starts_at = REFERENCE_TIME + timedelta(days=1)
    expires_at = REFERENCE_TIME + timedelta(days=30)

    with app.app_context():
        service = StudentDealService()

        deal = service.submit_business_deal(
            build_submission(
                starts_at=starts_at,
                expires_at=expires_at,
            )
        )

        assert deal.business_name == "Downtown Coffee"
        assert deal.category is DealCategory.COFFEE
        assert deal.discount_text == "15% off"
        assert deal.business_email == "owner@example.com"
        assert deal.starts_at is not None
        assert deal.expires_at is not None


def test_list_active_deals_returns_approved_current_deals(app):
    with app.app_context():
        active_deal = build_deal(
            title="Active deal",
            starts_at=REFERENCE_TIME - timedelta(days=1),
            expires_at=REFERENCE_TIME + timedelta(days=1),
        )
        no_date_deal = build_deal(
            title="No date limits",
        )

        db.session.add_all(
            [
                active_deal,
                no_date_deal,
            ]
        )
        db.session.commit()

        deals = StudentDealService().list_active_deals(
            now=REFERENCE_TIME
        )

        assert {
            deal.title for deal in deals
        } == {
            "Active deal",
            "No date limits",
        }


def test_list_active_deals_excludes_pending_deals(app):
    with app.app_context():
        pending_deal = build_deal(
            title="Pending deal",
            status=DealStatus.PENDING,
        )

        db.session.add(pending_deal)
        db.session.commit()

        deals = StudentDealService().list_active_deals(
            now=REFERENCE_TIME
        )

        assert deals == []


def test_list_active_deals_excludes_future_deals(app):
    with app.app_context():
        future_deal = build_deal(
            title="Future deal",
            starts_at=REFERENCE_TIME + timedelta(hours=1),
        )

        db.session.add(future_deal)
        db.session.commit()

        deals = StudentDealService().list_active_deals(
            now=REFERENCE_TIME
        )

        assert deals == []


def test_list_active_deals_excludes_expired_deals(app):
    with app.app_context():
        expired_deal = build_deal(
            title="Expired deal",
            expires_at=REFERENCE_TIME - timedelta(seconds=1),
        )

        db.session.add(expired_deal)
        db.session.commit()

        deals = StudentDealService().list_active_deals(
            now=REFERENCE_TIME
        )

        assert deals == []


def test_list_active_deals_excludes_deal_at_expiration_time(app):
    with app.app_context():
        expiring_deal = build_deal(
            title="Expiring now",
            expires_at=REFERENCE_TIME,
        )

        db.session.add(expiring_deal)
        db.session.commit()

        deals = StudentDealService().list_active_deals(
            now=REFERENCE_TIME
        )

        assert deals == []


def test_list_active_deals_includes_deal_at_start_time(app):
    with app.app_context():
        starting_deal = build_deal(
            title="Starting now",
            starts_at=REFERENCE_TIME,
        )

        db.session.add(starting_deal)
        db.session.commit()

        deals = StudentDealService().list_active_deals(
            now=REFERENCE_TIME
        )

        assert [
            deal.title for deal in deals
        ] == [
            "Starting now",
        ]


def test_list_active_deals_prioritizes_featured_deals(app):
    with app.app_context():
        regular_deal = build_deal(
            title="Regular deal",
            is_featured=False,
        )
        featured_deal = build_deal(
            title="Featured deal",
            is_featured=True,
        )

        db.session.add_all(
            [
                regular_deal,
                featured_deal,
            ]
        )
        db.session.commit()

        deals = StudentDealService().list_active_deals(
            now=REFERENCE_TIME
        )

        assert [
            deal.title for deal in deals
        ] == [
            "Featured deal",
            "Regular deal",
        ]


def test_list_active_deals_rejects_naive_reference_time(app):
    with app.app_context():
        service = StudentDealService()

        with pytest.raises(
            ValueError,
            match="Reference time must include a timezone.",
        ):
            service.list_active_deals(
                now=datetime(2026, 8, 15, 12, 0)
            )
