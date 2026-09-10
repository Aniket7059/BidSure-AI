from datetime import datetime,timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class VerificationResult(Base):
    """
    Stores the result of a verification attempt performed by
    an external verification provider.

    The actual verification logic is implemented by the
    Verification Provider module.
    """

    __tablename__ = "verification_results"

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

    bid_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("bid_documents.id"),
        nullable=True,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    verification_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    source_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SYNTHETIC",
        index=True,
    )

    verified_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False,
    )

    bid_submission = relationship(
        "BidSubmission",
        back_populates="verification_results",
    )

    bid_document = relationship(
        "BidDocument",
        back_populates="verification_results",
    )

    @property
    def source(self) -> str:
        return self.provider

    @property
    def requirement_type(self) -> str:
        from app.providers.schemas import map_to_requirement_type
        return map_to_requirement_type(self.verification_type or self.provider)

    @property
    def status(self) -> str:
        return self.verification_status