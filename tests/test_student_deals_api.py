from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.student_deal import (
    DealCategory,
    DealSource,
    DealStatus,
    StudentDeal,
)


REFERENCE_TIME = datetime.now(timezone.utc)


def valid_submission_data(**overrides):
    data = {
        "business_name": "Downtown Coffee",
        "title": "Student coffee discount",
        "description": (
            "Students receive a discount on any regular drink."
        ),
        "category": "coffee",
        "discount_text": "15% off",
        "location_name": "Waterville, Maine",
        "redemption_instructions": (
            "Show a valid student ID before payment."
        ),
        "business_email": "owner@example.com",
        "promo_code": "STUDENT15",
        "terms": "Valid for in-store purchases only.",
    }

    data.update(overrides)

    return data


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
        "promo_code": "STUDENT15",
        "terms": "Valid for in-store purchases only.",
        "source": DealSource.BUSINESS,
        "status": DealStatus.APPROVED,
        "is_featured": False,
        "starts_at": None,
        "expires_at": None,
    }

    values.update(overrides)

    return StudentDeal(**values)


def test_submit_deal_returns_created_response(
    app,
    client,
):
    response = client.post(
        "/api/v1/deals",
        json=valid_submission_data(),
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["deal"]["id"] is not None
    assert data["deal"]["status"] == "pending"
    assert data["message"] == (
        "Your deal was submitted for review."
    )

    with app.app_context():
        deal = db.session.get(
            StudentDeal,
            data["deal"]["id"],
        )

        assert deal is not None
        assert deal.business_name == "Downtown Coffee"
        assert deal.status is DealStatus.PENDING
        assert deal.source is DealSource.BUSINESS


def test_submit_deal_rejects_non_json_request(client):
    response = client.post(
        "/api/v1/deals",
        data="not json",
        content_type="text/plain",
    )

    assert response.status_code == 415
    assert response.get_json() == {
        "error": {
            "code": "invalid_content_type",
            "message": (
                "Request body must use application/json."
            ),
        }
    }


def test_submit_deal_rejects_invalid_submission(client):
    response = client.post(
        "/api/v1/deals",
        json=valid_submission_data(
            business_name=""
        ),
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "code": "invalid_deal_submission",
            "message": "Business name is required.",
        }
    }


def test_submit_deal_rejects_json_array(client):
    response = client.post(
        "/api/v1/deals",
        json=[],
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "code": "invalid_deal_submission",
            "message": (
                "Request body must be a JSON object."
            ),
        }
    }


def test_list_deals_returns_approved_active_deals(
    app,
    client,
):
    with app.app_context():
        deal = build_deal(
            title="Active coffee deal",
            starts_at=(
                REFERENCE_TIME - timedelta(days=1)
            ),
            expires_at=(
                REFERENCE_TIME + timedelta(days=1)
            ),
            is_featured=True,
        )

        db.session.add(deal)
        db.session.commit()

        deal_id = deal.id

    response = client.get("/api/v1/deals")

    assert response.status_code == 200

    data = response.get_json()

    assert data["deal_count"] == 1
    assert len(data["deals"]) == 1

    returned_deal = data["deals"][0]

    assert returned_deal["id"] == deal_id
    assert returned_deal["title"] == (
        "Active coffee deal"
    )
    assert returned_deal["category"] == "coffee"
    assert returned_deal["source"] == "business"
    assert returned_deal["is_featured"] is True
    assert returned_deal["promo_code"] == "STUDENT15"


def test_list_deals_does_not_expose_business_email(
    app,
    client,
):
    with app.app_context():
        db.session.add(build_deal())
        db.session.commit()

    response = client.get("/api/v1/deals")

    returned_deal = response.get_json()["deals"][0]

    assert "business_email" not in returned_deal


def test_list_deals_excludes_pending_deals(
    app,
    client,
):
    with app.app_context():
        db.session.add(
            build_deal(
                title="Pending deal",
                status=DealStatus.PENDING,
            )
        )
        db.session.commit()

    response = client.get("/api/v1/deals")

    assert response.status_code == 200
    assert response.get_json() == {
        "deal_count": 0,
        "deals": [],
    }


def test_list_deals_excludes_expired_deals(
    app,
    client,
):
    with app.app_context():
        db.session.add(
            build_deal(
                title="Expired deal",
                expires_at=(
                    REFERENCE_TIME - timedelta(days=1)
                ),
            )
        )
        db.session.commit()

    response = client.get("/api/v1/deals")

    assert response.status_code == 200
    assert response.get_json()["deal_count"] == 0
    assert response.get_json()["deals"] == []


def test_list_deals_prioritizes_featured_deals(
    app,
    client,
):
    with app.app_context():
        db.session.add_all(
            [
                build_deal(
                    title="Regular deal",
                    is_featured=False,
                ),
                build_deal(
                    title="Featured deal",
                    is_featured=True,
                ),
            ]
        )
        db.session.commit()

    response = client.get("/api/v1/deals")

    titles = [
        deal["title"]
        for deal in response.get_json()["deals"]
    ]

    assert titles == [
        "Featured deal",
        "Regular deal",
    ]
