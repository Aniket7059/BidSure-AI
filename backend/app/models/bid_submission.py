from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class BidSubmission(Base):
    """
    Represents a bidder's submission for a specific tender.
    """

    __tablename__ = "bid_submissions"

    __table_args__ = (
        UniqueConstraint(
            "tender_id",
            "bidder_id",
            name="uq_bid_submission_tender_bidder",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    tender_id: Mapped[int] = mapped_column(
        ForeignKey("tenders.id"),
        nullable=False,
        index=True,
    )

    bidder_id: Mapped[int] = mapped_column(
        ForeignKey("bidders.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SUBMITTED",
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
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

    tender = relationship(
        "Tender",
        back_populates="bid_submissions",
    )

    bidder = relationship(
        "Bidder",
        back_populates="bid_submissions",
    )

    documents = relationship(
        "BidDocument",
        back_populates="bid_submission",
        cascade="all, delete-orphan",
    )

    verification_results = relationship(
        "VerificationResult",
        back_populates="bid_submission",
        cascade="all, delete-orphan",
    )

    compliance_checks = relationship(
        "ComplianceCheck",
        back_populates="bid_submission",
        cascade="all, delete-orphan",
    )

    compliance_assessments = relationship(
        "ComplianceAssessment",
        back_populates="bid_submission",
        cascade="all, delete-orphan",
    )

    discrepancies = relationship(
        "Discrepancy",
        back_populates="bid_submission",
        cascade="all, delete-orphan",
    )

    procurement_decision = relationship(
        "ProcurementDecision",
        back_populates="bid_submission",
        uselist=False,
        cascade="all, delete-orphan",
    )