from datetime import datetime, timezone

from sqlalchemy import or_, select

from app.extensions import db
from app.models.student_deal import (
    DealSource,
    DealStatus,
    StudentDeal,
)
from app.schemas.student_deal import StudentDealSubmission


class StudentDealService:
    """Manage student deal submissions and discovery."""

    def submit_business_deal(
        self,
        submission: StudentDealSubmission,
    ) -> StudentDeal:
        """Save a new business-submitted deal for moderation."""

        deal = StudentDeal(
            business_name=submission.business_name,
            title=submission.title,
            description=submission.description,
            category=submission.category,
            discount_text=submission.discount_text,
            location_name=submission.location_name,
            redemption_instructions=(
                submission.redemption_instructions
            ),
            business_email=submission.business_email,
            terms=submission.terms,
            promo_code=submission.promo_code,
            starts_at=submission.starts_at,
            expires_at=submission.expires_at,
            source=DealSource.BUSINESS,
            status=DealStatus.PENDING,
            is_featured=False,
        )

        db.session.add(deal)
        db.session.commit()

        return deal

    def list_active_deals(
        self,
        *,
        now: datetime | None = None,
    ) -> list[StudentDeal]:
        """Return approved deals active at the requested time."""

        reference_time = now or datetime.now(timezone.utc)

        if reference_time.tzinfo is None:
            raise ValueError(
                "Reference time must include a timezone."
            )

        statement = (
            select(StudentDeal)
            .where(
                StudentDeal.status == DealStatus.APPROVED,
                or_(
                    StudentDeal.starts_at.is_(None),
                    StudentDeal.starts_at <= reference_time,
                ),
                or_(
                    StudentDeal.expires_at.is_(None),
                    StudentDeal.expires_at > reference_time,
                ),
            )
            .order_by(
                StudentDeal.is_featured.desc(),
                StudentDeal.created_at.desc(),
                StudentDeal.id.desc(),
            )
        )

        return list(
            db.session.scalars(statement).all()
        )
