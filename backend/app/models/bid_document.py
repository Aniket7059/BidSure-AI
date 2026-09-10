from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class BidDocument(Base):
    """
    Represents a document submitted as part of a bid submission.

    This model stores document metadata only.
    Document processing and AI extraction are handled separately.
    """

    __tablename__ = "bid_documents"

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

    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    file_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    file_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UPLOADED",
    )

    uploaded_at: Mapped[datetime] = mapped_column(
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

    bid_submission = relationship(
        "BidSubmission",
        back_populates="documents",
    )

    extractions = relationship(
        "DocumentExtraction",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    verification_results = relationship(
        "VerificationResult",
        back_populates="bid_document",
    )