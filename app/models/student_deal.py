from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SqlEnum,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class DealCategory(str, Enum):
    """Supported student deal categories."""

    FOOD = "food"
    COFFEE = "coffee"
    SHOPPING = "shopping"
    SERVICES = "services"
    ENTERTAINMENT = "entertainment"
    WELLNESS = "wellness"
    OTHER = "other"


class DealStatus(str, Enum):
    """Moderation status for a submitted student deal."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAUSED = "paused"
    EXPIRED = "expired"


class DealSource(str, Enum):
    """Origin of a student deal listing."""

    BUSINESS = "business"
    INSTEAD = "instead"
    COMMUNITY = "community"


class StudentDeal(db.Model):
    """A student discount offered by a local business."""

    __tablename__ = "student_deals"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    business_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(140),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[DealCategory] = mapped_column(
        SqlEnum(
            DealCategory,
            name="deal_category",
            native_enum=False,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[DealStatus] = mapped_column(
        SqlEnum(
            DealStatus,
            name="deal_status",
            native_enum=False,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        nullable=False,
        default=DealStatus.PENDING,
        index=True,
    )

    source: Mapped[DealSource] = mapped_column(
        SqlEnum(
            DealSource,
            name="deal_source",
            native_enum=False,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        nullable=False,
        default=DealSource.BUSINESS,
    )

    discount_text: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    location_name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    redemption_instructions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    terms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    promo_code: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    business_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    business_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    deal_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<StudentDeal id={self.id} "
            f"business={self.business_name!r} "
            f"status={self.status.value!r}>"
        )
