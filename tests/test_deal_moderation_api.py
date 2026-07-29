from app.extensions import db
from app.models import User
from app.models.student_deal import (
    DealCategory,
    DealSource,
    DealStatus,
    StudentDeal,
)


ADMIN_EMAIL = "admin@example.com"


def create_user(
    app,
    *,
    email: str,
) -> int:
    with app.app_context():
        user = User(
            email=email,
            display_name="Test User",
            google_sub=f"google-{email}",
            avatar_url=None,
        )

        db.session.add(user)
        db.session.commit()

        return user.id


def authenticate_client(
    client,
    *,
    user_id: int,
) -> None:
    with client.session_transaction() as session:
        session["user_id"] = user_id


def authenticate_admin(
    app,
    client,
) -> None:
    app.config["ADMIN_EMAILS"] = {
        ADMIN_EMAIL,
    }

    user_id = create_user(
        app,
        email=ADMIN_EMAIL,
    )

    authenticate_client(
        client,
        user_id=user_id,
    )


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
        "business_url": (
            "https://downtowncoffee.example.com"
        ),
        "deal_url": (
            "https://downtowncoffee.example.com/"
            "student-discount"
        ),
        "promo_code": "STUDENT15",
        "terms": "Valid for in-store purchases only.",
        "source": DealSource.BUSINESS,
        "status": DealStatus.PENDING,
        "is_featured": False,
        "starts_at": None,
        "expires_at": None,
    }

    values.update(overrides)

    return StudentDeal(**values)


def test_pending_deals_requires_authentication(
    client,
):
    response = client.get(
        "/api/v1/admin/deals/pending"
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == (
        "authentication_required"
    )


def test_pending_deals_rejects_non_admin(
    app,
    client,
):
    app.config["ADMIN_EMAILS"] = {
        ADMIN_EMAIL,
    }

    user_id = create_user(
        app,
        email="student@example.com",
    )

    authenticate_client(
        client,
        user_id=user_id,
    )

    response = client.get(
        "/api/v1/admin/deals/pending"
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == (
        "admin_access_required"
    )


def test_pending_deals_returns_pending_submissions(
    app,
    client,
):
    authenticate_admin(app, client)

    with app.app_context():
        pending_deal = build_deal(
            title="Pending coffee deal",
        )
        approved_deal = build_deal(
            title="Approved coffee deal",
            status=DealStatus.APPROVED,
        )

        db.session.add_all(
            [
                pending_deal,
                approved_deal,
            ]
        )
        db.session.commit()

        pending_deal_id = pending_deal.id

    response = client.get(
        "/api/v1/admin/deals/pending"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["deal_count"] == 1
    assert len(data["deals"]) == 1

    returned_deal = data["deals"][0]

    assert returned_deal["id"] == pending_deal_id
    assert returned_deal["title"] == (
        "Pending coffee deal"
    )
    assert returned_deal["status"] == "pending"
    assert returned_deal["business_email"] == (
        "owner@example.com"
    )
    assert returned_deal["business_url"] == (
        "https://downtowncoffee.example.com"
    )
    assert returned_deal["deal_url"] == (
        "https://downtowncoffee.example.com/"
        "student-discount"
    )
    assert returned_deal["promo_code"] == (
        "STUDENT15"
    )
    assert returned_deal["terms"] == (
        "Valid for in-store purchases only."
    )


def test_pending_deals_returns_empty_collection(
    app,
    client,
):
    authenticate_admin(app, client)

    response = client.get(
        "/api/v1/admin/deals/pending"
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "deal_count": 0,
        "deals": [],
    }


def test_admin_can_approve_pending_deal(
    app,
    client,
):
    authenticate_admin(app, client)

    with app.app_context():
        deal = build_deal()

        db.session.add(deal)
        db.session.commit()

        deal_id = deal.id

    response = client.post(
        f"/api/v1/admin/deals/{deal_id}/approve"
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "deal": {
            "id": deal_id,
            "status": "approved",
        },
        "message": "The student deal was approved.",
    }

    with app.app_context():
        stored_deal = db.session.get(
            StudentDeal,
            deal_id,
        )

        assert stored_deal is not None
        assert stored_deal.status is DealStatus.APPROVED


def test_admin_can_reject_pending_deal(
    app,
    client,
):
    authenticate_admin(app, client)

    with app.app_context():
        deal = build_deal()

        db.session.add(deal)
        db.session.commit()

        deal_id = deal.id

    response = client.post(
        f"/api/v1/admin/deals/{deal_id}/reject"
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "deal": {
            "id": deal_id,
            "status": "rejected",
        },
        "message": "The student deal was rejected.",
    }

    with app.app_context():
        stored_deal = db.session.get(
            StudentDeal,
            deal_id,
        )

        assert stored_deal is not None
        assert stored_deal.status is DealStatus.REJECTED


def test_approve_returns_not_found_for_unknown_deal(
    app,
    client,
):
    authenticate_admin(app, client)

    response = client.post(
        "/api/v1/admin/deals/999/approve"
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "error": {
            "code": "deal_not_found",
            "message": (
                "Student deal 999 was not found."
            ),
        }
    }


def test_reject_returns_not_found_for_unknown_deal(
    app,
    client,
):
    authenticate_admin(app, client)

    response = client.post(
        "/api/v1/admin/deals/999/reject"
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "error": {
            "code": "deal_not_found",
            "message": (
                "Student deal 999 was not found."
            ),
        }
    }


def test_approve_returns_conflict_for_reviewed_deal(
    app,
    client,
):
    authenticate_admin(app, client)

    with app.app_context():
        deal = build_deal(
            status=DealStatus.REJECTED,
        )

        db.session.add(deal)
        db.session.commit()

        deal_id = deal.id

    response = client.post(
        f"/api/v1/admin/deals/{deal_id}/approve"
    )

    assert response.status_code == 409
    assert response.get_json() == {
        "error": {
            "code": "invalid_status_transition",
            "message": (
                "Only pending deals can be reviewed."
            ),
        }
    }


def test_reject_returns_conflict_for_reviewed_deal(
    app,
    client,
):
    authenticate_admin(app, client)

    with app.app_context():
        deal = build_deal(
            status=DealStatus.APPROVED,
        )

        db.session.add(deal)
        db.session.commit()

        deal_id = deal.id

    response = client.post(
        f"/api/v1/admin/deals/{deal_id}/reject"
    )

    assert response.status_code == 409
    assert response.get_json() == {
        "error": {
            "code": "invalid_status_transition",
            "message": (
                "Only pending deals can be reviewed."
            ),
        }
    }


def test_approve_requires_admin_access(
    app,
    client,
):
    with app.app_context():
        deal = build_deal()

        db.session.add(deal)
        db.session.commit()

        deal_id = deal.id

    response = client.post(
        f"/api/v1/admin/deals/{deal_id}/approve"
    )

    assert response.status_code == 401


def test_reject_requires_admin_access(
    app,
    client,
):
    with app.app_context():
        deal = build_deal()

        db.session.add(deal)
        db.session.commit()

        deal_id = deal.id

    response = client.post(
        f"/api/v1/admin/deals/{deal_id}/reject"
    )

    assert response.status_code == 401
