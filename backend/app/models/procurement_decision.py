from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProcurementDecision(Base):
    """
    Represents the authoritative final qualification/disqualification decision
    recorded by a Procurement Officer for a bid submission.

    The final decision is human-in-the-loop and strictly separate from automated
    compliance scoring and AI recommendations. Exactly one active final decision
    is permitted per bid submission (enforced via unique constraint on bid_submission_id).
    """

    __tablename__ = "procurement_decisions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    bid_submission_id: Mapped[int] = mapped_column(
        ForeignKey("bid_submissions.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # QUALIFIED or DISQUALIFIED

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    decided_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    decided_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False,
    )

    assessment_id: Mapped[int | None] = mapped_column(
        ForeignKey("compliance_assessments.id"),
        nullable=True,
    )

    recommendation_at_decision: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    score_snapshot: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    risk_snapshot: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    is_override: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    bid_submission = relationship(
        "BidSubmission",
        back_populates="procurement_decision",
    )

    decided_by_user = relationship(
        "User",
    )

    assessment = relationship(
        "ComplianceAssessment",
    )
