from datetime import datetime, timezone

from sqlalchemy import or_, select

from app.extensions import db
from app.models.student_deal import (
    DealSource,
    DealStatus,
    StudentDeal,
)
from app.schemas.student_deal import StudentDealSubmission


class StudentDealNotFoundError(LookupError):
    """Raised when a student deal cannot be found."""


class InvalidDealStatusTransitionError(ValueError):
    """Raised when a deal cannot move to the requested status."""


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
            business_url=submission.business_url,
            deal_url=submission.deal_url,
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

    def list_pending_deals(
        self,
    ) -> list[StudentDeal]:
        """Return pending submissions in review order."""

        statement = (
            select(StudentDeal)
            .where(
                StudentDeal.status == DealStatus.PENDING
            )
            .order_by(
                StudentDeal.created_at.asc(),
                StudentDeal.id.asc(),
            )
        )

        return list(
            db.session.scalars(statement).all()
        )

    def approve_deal(
        self,
        deal_id: int,
    ) -> StudentDeal:
        """Approve a pending student deal."""

        deal = self._get_pending_deal(deal_id)

        deal.status = DealStatus.APPROVED

        db.session.commit()

        return deal

    def reject_deal(
        self,
        deal_id: int,
    ) -> StudentDeal:
        """Reject a pending student deal."""

        deal = self._get_pending_deal(deal_id)

        deal.status = DealStatus.REJECTED

        db.session.commit()

        return deal

    @staticmethod
    def _get_pending_deal(
        deal_id: int,
    ) -> StudentDeal:
        deal = db.session.get(
            StudentDeal,
            deal_id,
        )

        if deal is None:
            raise StudentDealNotFoundError(
                f"Student deal {deal_id} was not found."
            )

        if deal.status is not DealStatus.PENDING:
            raise InvalidDealStatusTransitionError(
                "Only pending deals can be reviewed."
            )

        return deal
