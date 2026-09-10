from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DiscrepancyType(str, Enum):
    MISMATCH = "MISMATCH"
    LEGAL_NAME_MISMATCH = "LEGAL_NAME_MISMATCH"
    GSTIN_MISMATCH = "GSTIN_MISMATCH"
    PAN_MISMATCH = "PAN_MISMATCH"
    PAN_GSTIN_EMBEDDED_MISMATCH = "PAN_GSTIN_EMBEDDED_MISMATCH"
    UDYAM_MISMATCH = "UDYAM_MISMATCH"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    MISSING_PORTAL_VERIFICATION = "MISSING_PORTAL_VERIFICATION"
    INACTIVE_REGISTRATION = "INACTIVE_REGISTRATION"
    EXPIRED_DOCUMENT = "EXPIRED_DOCUMENT"
    DEBARRED_VENDOR = "DEBARRED_VENDOR"
    CROSS_SOURCE_CONFLICT = "CROSS_SOURCE_CONFLICT"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"
    UNSUPPORTED_VERIFICATION = "UNSUPPORTED_VERIFICATION"
    OTHER = "OTHER"


class DiscrepancySeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DiscrepancyStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    WAIVED = "WAIVED"


class DiscrepancySource(str, Enum):
    DOCUMENT = "DOCUMENT"
    PROVIDER = "PROVIDER"
    CROSS_VERIFICATION = "CROSS_VERIFICATION"
    COMPLIANCE = "COMPLIANCE"


class Discrepancy(Base):
    """
    Represents a durable finding produced when expected evidence does not align with
    available evidence (e.g. data mismatches, missing mandatory evidence, inactive registrations).
    """

    __tablename__ = "discrepancies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    bid_submission_id: Mapped[int] = mapped_column(
        ForeignKey("bid_submissions.id"),
        nullable=False,
        index=True,
    )

    tender_requirement_id: Mapped[int | None] = mapped_column(
        ForeignKey("tender_requirements.id"),
        nullable=True,
        index=True,
    )

    bid_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("bid_documents.id"),
        nullable=True,
        index=True,
    )

    verification_result_id: Mapped[int | None] = mapped_column(
        ForeignKey("verification_results.id"),
        nullable=True,
        index=True,
    )

    compliance_check_id: Mapped[int | None] = mapped_column(
        ForeignKey("compliance_checks.id"),
        nullable=True,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MEDIUM",
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    expected_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    observed_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="CROSS_VERIFICATION",
    )

    evidence: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    finding_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    resolution_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    bid_submission = relationship(
        "BidSubmission",
        back_populates="discrepancies",
    )

    tender_requirement = relationship(
        "TenderRequirement",
    )

    bid_document = relationship(
        "BidDocument",
    )

    verification_result = relationship(
        "VerificationResult",
    )

    compliance_check = relationship(
        "ComplianceCheck",
    )
