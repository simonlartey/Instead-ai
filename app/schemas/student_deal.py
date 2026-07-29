from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from app.models.student_deal import DealCategory


class DealValidationError(ValueError):
    """Raised when student deal submission data is invalid."""


@dataclass(frozen=True)
class StudentDealSubmission:
    """Validated data submitted by a local business."""

    business_name: str
    title: str
    description: str
    category: DealCategory
    discount_text: str
    location_name: str
    redemption_instructions: str
    business_email: str
    business_url: str | None = None
    deal_url: str | None = None
    terms: str | None = None
    promo_code: str | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None

    @classmethod
    def from_dict(
        cls,
        data: Any,
    ) -> "StudentDealSubmission":
        if not isinstance(data, dict):
            raise DealValidationError(
                "Request body must be a JSON object."
            )

        business_name = cls._required_text(
            data,
            field_name="business_name",
            label="Business name",
            max_length=120,
        )
        title = cls._required_text(
            data,
            field_name="title",
            label="Deal title",
            max_length=140,
        )
        description = cls._required_text(
            data,
            field_name="description",
            label="Description",
            max_length=2000,
        )
        discount_text = cls._required_text(
            data,
            field_name="discount_text",
            label="Discount",
            max_length=80,
        )
        location_name = cls._required_text(
            data,
            field_name="location_name",
            label="Location",
            max_length=160,
        )
        redemption_instructions = cls._required_text(
            data,
            field_name="redemption_instructions",
            label="Redemption instructions",
            max_length=2000,
        )
        business_email = cls._parse_email(
            data.get("business_email")
        )
        business_url = cls._optional_url(
            data.get("business_url"),
            label="Business URL",
        )
        deal_url = cls._optional_url(
            data.get("deal_url"),
            label="Deal URL",
        )
        category = cls._parse_category(
            data.get("category")
        )
        terms = cls._optional_text(
            data.get("terms"),
            label="Terms",
            max_length=2000,
        )
        promo_code = cls._optional_text(
            data.get("promo_code"),
            label="Promo code",
            max_length=80,
        )
        starts_at = cls._optional_datetime(
            data.get("starts_at"),
            field_name="starts_at",
            label="Start date",
        )
        expires_at = cls._optional_datetime(
            data.get("expires_at"),
            field_name="expires_at",
            label="Expiration date",
        )

        if (
            starts_at is not None
            and expires_at is not None
            and expires_at <= starts_at
        ):
            raise DealValidationError(
                "Expiration date must be after the start date."
            )

        return cls(
            business_name=business_name,
            title=title,
            description=description,
            category=category,
            discount_text=discount_text,
            location_name=location_name,
            redemption_instructions=redemption_instructions,
            business_email=business_email,
            business_url=business_url,
            deal_url=deal_url,
            terms=terms,
            promo_code=promo_code,
            starts_at=starts_at,
            expires_at=expires_at,
        )

    @staticmethod
    def _required_text(
        data: dict[str, Any],
        *,
        field_name: str,
        label: str,
        max_length: int,
    ) -> str:
        value = data.get(field_name)

        if not isinstance(value, str):
            raise DealValidationError(
                f"{label} must be a string."
            )

        normalized_value = value.strip()

        if not normalized_value:
            raise DealValidationError(
                f"{label} is required."
            )

        if len(normalized_value) > max_length:
            raise DealValidationError(
                f"{label} must be {max_length} characters or fewer."
            )

        return normalized_value

    @staticmethod
    def _optional_text(
        value: Any,
        *,
        label: str,
        max_length: int,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise DealValidationError(
                f"{label} must be a string."
            )

        normalized_value = value.strip()

        if not normalized_value:
            return None

        if len(normalized_value) > max_length:
            raise DealValidationError(
                f"{label} must be {max_length} characters or fewer."
            )

        return normalized_value

    @staticmethod
    def _parse_category(value: Any) -> DealCategory:
        if not isinstance(value, str):
            raise DealValidationError(
                "Category must be a string."
            )

        normalized_value = value.strip().lower()

        try:
            return DealCategory(normalized_value)
        except ValueError as error:
            allowed_categories = ", ".join(
                category.value for category in DealCategory
            )
            raise DealValidationError(
                "Category must be one of: "
                f"{allowed_categories}."
            ) from error

    @staticmethod
    def _parse_email(value: Any) -> str:
        if not isinstance(value, str):
            raise DealValidationError(
                "Business email must be a string."
            )

        normalized_value = value.strip().lower()

        if not normalized_value:
            raise DealValidationError(
                "Business email is required."
            )

        if len(normalized_value) > 255:
            raise DealValidationError(
                "Business email must be 255 characters or fewer."
            )

        local_part, separator, domain = normalized_value.partition(
            "@"
        )

        if (
            not separator
            or not local_part
            or not domain
            or "." not in domain
            or domain.startswith(".")
            or domain.endswith(".")
        ):
            raise DealValidationError(
                "Business email must be a valid email address."
            )

        return normalized_value

    @staticmethod
    def _optional_url(
        value: Any,
        *,
        label: str,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise DealValidationError(
                f"{label} must be a string."
            )

        normalized_value = value.strip()

        if not normalized_value:
            return None

        if len(normalized_value) > 500:
            raise DealValidationError(
                f"{label} must be 500 characters or fewer."
            )

        parsed_url = urlparse(normalized_value)

        if (
            parsed_url.scheme not in {"http", "https"}
            or not parsed_url.netloc
        ):
            raise DealValidationError(
                f"{label} must be a valid HTTP or HTTPS URL."
            )

        return normalized_value

    @staticmethod
    def _optional_datetime(
        value: Any,
        *,
        field_name: str,
        label: str,
    ) -> datetime | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise DealValidationError(
                f"{label} must be an ISO 8601 date and time."
            )

        normalized_value = value.strip()

        if not normalized_value:
            return None

        if normalized_value.endswith("Z"):
            normalized_value = (
                f"{normalized_value[:-1]}+00:00"
            )

        try:
            parsed_value = datetime.fromisoformat(
                normalized_value
            )
        except ValueError as error:
            raise DealValidationError(
                f"{label} must be an ISO 8601 date and time."
            ) from error

        if parsed_value.tzinfo is None:
            raise DealValidationError(
                f"{field_name} must include a timezone."
            )

        return parsed_value
