from sqlalchemy.orm import Session

from app.models.verification_result import VerificationResult
from app.providers.schemas import VerificationResult as ProviderVerificationResult


class VerificationResultRepository:
    """Persistence operations for provider verification results."""

    def create(
        self,
        db: Session,
        bid_submission_id: int,
        result: ProviderVerificationResult,
        bid_document_id: int | None = None,
    ) -> VerificationResult:
        mode_val = result.source_mode.value if hasattr(result.source_mode, "value") else str(result.source_mode)
        verification_result = VerificationResult(
            bid_submission_id=bid_submission_id,
            bid_document_id=bid_document_id,
            provider=result.provider,
            verification_type=result.verification_type,
            identifier=result.identifier,
            verification_status=result.status.value,
            source_mode=mode_val,
            verified_data=result.verified_data,
            message=result.message,
            error_message=result.error_message,
            checked_at=result.checked_at,
        )

        db.add(verification_result)
        db.commit()
        db.refresh(verification_result)

        return verification_result

    def get_by_id(
        self,
        db: Session,
        verification_result_id: int,
    ) -> VerificationResult | None:
        return (
            db.query(VerificationResult)
            .filter(VerificationResult.id == verification_result_id)
            .first()
        )

    def get_by_submission(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> list[VerificationResult]:
        return (
            db.query(VerificationResult)
            .filter(
                VerificationResult.bid_submission_id == bid_submission_id
            )
            .order_by(VerificationResult.id)
            .all()
        )


verification_result_repository = VerificationResultRepository()
