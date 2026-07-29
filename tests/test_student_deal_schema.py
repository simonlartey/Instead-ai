from datetime import timezone

import pytest

from app.models.student_deal import DealCategory
from app.schemas.student_deal import (
    DealValidationError,
    StudentDealSubmission,
)


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
        "business_email": "OWNER@EXAMPLE.COM",
        "business_url": (
            "https://downtowncoffee.example.com"
        ),
        "deal_url": (
            "https://downtowncoffee.example.com/"
            "student-discount"
        ),
    }

    data.update(overrides)

    return data


def test_submission_parses_required_fields():
    submission = StudentDealSubmission.from_dict(
        valid_submission_data()
    )

    assert submission.business_name == "Downtown Coffee"
    assert submission.title == "Student coffee discount"
    assert submission.category is DealCategory.COFFEE
    assert submission.discount_text == "15% off"
    assert submission.business_email == "owner@example.com"
    assert submission.business_url == (
        "https://downtowncoffee.example.com"
    )
    assert submission.deal_url == (
        "https://downtowncoffee.example.com/"
        "student-discount"
    )
    assert submission.terms is None
    assert submission.promo_code is None
    assert submission.starts_at is None
    assert submission.expires_at is None


def test_submission_strips_text_values():
    submission = StudentDealSubmission.from_dict(
        valid_submission_data(
            business_name="  Downtown Coffee  ",
            title="  Student coffee discount  ",
            promo_code="  STUDENT15  ",
        )
    )

    assert submission.business_name == "Downtown Coffee"
    assert submission.title == "Student coffee discount"
    assert submission.promo_code == "STUDENT15"


def test_submission_converts_blank_optional_text_to_none():
    submission = StudentDealSubmission.from_dict(
        valid_submission_data(
            terms="   ",
            promo_code="",
            business_url="  ",
            deal_url="",
        )
    )

    assert submission.terms is None
    assert submission.promo_code is None
    assert submission.business_url is None
    assert submission.deal_url is None


def test_submission_parses_iso_datetimes():
    submission = StudentDealSubmission.from_dict(
        valid_submission_data(
            starts_at="2026-08-01T09:00:00-04:00",
            expires_at="2026-08-31T23:59:00Z",
        )
    )

    assert submission.starts_at is not None
    assert submission.expires_at is not None
    assert submission.starts_at.utcoffset() is not None
    assert submission.expires_at.tzinfo is timezone.utc


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            None,
            "Request body must be a JSON object.",
        ),
        (
            [],
            "Request body must be a JSON object.",
        ),
        (
            valid_submission_data(business_name=""),
            "Business name is required.",
        ),
        (
            valid_submission_data(title=123),
            "Deal title must be a string.",
        ),
        (
            valid_submission_data(category="travel"),
            "Category must be one of:",
        ),
        (
            valid_submission_data(business_email="invalid-email"),
            "Business email must be a valid email address.",
        ),
        (
            valid_submission_data(
                starts_at="2026-08-01T09:00:00"
            ),
            "starts_at must include a timezone.",
        ),
        (
            valid_submission_data(
                expires_at="not-a-date"
            ),
            (
                "Expiration date must be an ISO 8601 "
                "date and time."
            ),
        ),
    ],
)
def test_submission_rejects_invalid_data(
    payload,
    message,
):
    with pytest.raises(
        DealValidationError,
        match=message,
    ):
        StudentDealSubmission.from_dict(payload)


def test_submission_rejects_expiration_before_start():
    with pytest.raises(
        DealValidationError,
        match=(
            "Expiration date must be after the start date."
        ),
    ):
        StudentDealSubmission.from_dict(
            valid_submission_data(
                starts_at="2026-08-10T09:00:00-04:00",
                expires_at="2026-08-09T09:00:00-04:00",
            )
        )


@pytest.mark.parametrize(
    ("field_name", "label", "max_length"),
    [
        ("business_name", "Business name", 120),
        ("title", "Deal title", 140),
        ("description", "Description", 2000),
        ("discount_text", "Discount", 80),
        ("location_name", "Location", 160),
        (
            "redemption_instructions",
            "Redemption instructions",
            2000,
        ),
        ("terms", "Terms", 2000),
        ("promo_code", "Promo code", 80),
    ],
)
def test_submission_rejects_text_over_maximum_length(
    field_name,
    label,
    max_length,
):
    with pytest.raises(
        DealValidationError,
        match=(
            f"{label} must be {max_length} "
            "characters or fewer."
        ),
    ):
        StudentDealSubmission.from_dict(
            valid_submission_data(
                **{
                    field_name: "x" * (max_length + 1),
                }
            )
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "business_url",
        "deal_url",
    ],
)
def test_submission_accepts_http_and_https_urls(
    field_name,
):
    http_submission = (
        StudentDealSubmission.from_dict(
            valid_submission_data(
                **{
                    field_name: (
                        "http://example.com/student-deal"
                    ),
                }
            )
        )
    )

    https_submission = (
        StudentDealSubmission.from_dict(
            valid_submission_data(
                **{
                    field_name: (
                        "https://example.com/student-deal"
                    ),
                }
            )
        )
    )

    assert getattr(
        http_submission,
        field_name,
    ).startswith("http://")

    assert getattr(
        https_submission,
        field_name,
    ).startswith("https://")


@pytest.mark.parametrize(
    ("field_name", "label"),
    [
        ("business_url", "Business URL"),
        ("deal_url", "Deal URL"),
    ],
)
@pytest.mark.parametrize(
    "invalid_url",
    [
        "javascript:alert(1)",
        "ftp://example.com/deal",
        "example.com/deal",
        "https://",
        "not a url",
    ],
)
def test_submission_rejects_invalid_urls(
    field_name,
    label,
    invalid_url,
):
    with pytest.raises(
        DealValidationError,
        match=(
            f"{label} must be a valid HTTP or HTTPS URL."
        ),
    ):
        StudentDealSubmission.from_dict(
            valid_submission_data(
                **{
                    field_name: invalid_url,
                }
            )
        )


@pytest.mark.parametrize(
    ("field_name", "label"),
    [
        ("business_url", "Business URL"),
        ("deal_url", "Deal URL"),
    ],
)
def test_submission_rejects_url_over_maximum_length(
    field_name,
    label,
):
    with pytest.raises(
        DealValidationError,
        match=(
            f"{label} must be 500 characters or fewer."
        ),
    ):
        StudentDealSubmission.from_dict(
            valid_submission_data(
                **{
                    field_name: (
                        "https://example.com/"
                        + ("x" * 500)
                    ),
                }
            )
        )
