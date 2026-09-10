from sqlalchemy.orm import Session

from app.providers.registry import ProviderRegistry, provider_registry
from app.providers.schemas import VerificationRequest, VerificationResult
from app.repositories.bid_document_repository import bid_document_repository
from app.repositories.bid_submission_repository import bid_submission_repository
from app.repositories.verification_result_repository import (
    verification_result_repository,
)


class VerificationService:
    """Coordinates provider execution and persistence.

    Providers retrieve/verify facts. This service connects those providers to
    BidSure's database while keeping provider implementations independent of
    SQLAlchemy and bid-specific identifiers.
    """

    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        from app.providers.register import register_providers

        register_providers()
        self.registry = registry or provider_registry

    def verify(
        self,
        db: Session,
        bid_submission_id: int,
        request: VerificationRequest,
        bid_document_id: int | None = None,
    ) -> VerificationResult:
        submission = bid_submission_repository.get_by_id(
            db,
            bid_submission_id,
        )
        if submission is None:
            raise ValueError(
                f"Bid submission not found: {bid_submission_id}"
            )

        if bid_document_id is not None:
            document = bid_document_repository.get_by_id(
                db,
                bid_document_id,
            )
            if document is None:
                raise ValueError(
                    f"Bid document not found: {bid_document_id}"
                )
            if document.bid_submission_id != bid_submission_id:
                raise ValueError(
                    "Bid document does not belong to the specified "
                    "bid submission."
                )

        provider = self.registry.get(request.verification_type)
        if provider is None:
            raise ValueError(
                "No verification provider registered for type: "
                f"{request.verification_type}"
            )

        from app.core.audit_actions import AuditAction, AuditEntityType
        from app.services.audit_log_service import audit_log_service

        audit_log_service.record_event(
            db=db,
            action=AuditAction.VERIFICATION_STARTED,
            entity_type=AuditEntityType.VERIFICATION_RESULT,
            bid_submission_id=bid_submission_id,
            new_value={
                "verification_type": request.verification_type,
                "identifier": request.identifier,
            },
            details=f"Verification started for {request.verification_type} (Identifier: {request.identifier})",
        )

        result = provider.verify(request)

        created_result = verification_result_repository.create(
            db=db,
            bid_submission_id=bid_submission_id,
            bid_document_id=bid_document_id,
            result=result,
        )

        action = (
            AuditAction.VERIFICATION_FAILED
            if result.status.upper() in ("FAILED", "ERROR")
            else AuditAction.VERIFICATION_COMPLETED
        )

        audit_log_service.record_event(
            db=db,
            action=action,
            entity_type=AuditEntityType.VERIFICATION_RESULT,
            entity_id=created_result.id,
            bid_submission_id=bid_submission_id,
            new_value={
                "provider": result.provider,
                "status": result.status,
                "verification_type": result.verification_type,
            },
            details=f"Verification {result.status} for provider '{result.provider}' (Type: {result.verification_type})",
        )

        return result

    def record_manual_verification(
        self,
        db: Session,
        user_id: int,
        manual_in: "ManualVerificationCreate",
    ) -> VerificationResult:
        submission = bid_submission_repository.get_by_id(
            db,
            manual_in.bid_submission_id,
        )
        if submission is None:
            raise ValueError(
                f"Bid submission not found: {manual_in.bid_submission_id}"
            )

        from app.providers.schemas import SourceMode, VerificationResult as ProviderVerificationResult

        result = ProviderVerificationResult(
            provider="MANUAL_OFFICER_REVIEW",
            verification_type=manual_in.requirement_type,
            identifier=manual_in.identifier,
            status=manual_in.verification_status,
            source_mode=SourceMode.MANUAL,
            verified_data={
                "manual_verifier_id": user_id,
                "reference_notes": manual_in.reference_notes,
            },
            message=manual_in.message or f"Manual verification recorded by officer #{user_id}",
        )

        created_result = verification_result_repository.create(
            db=db,
            bid_submission_id=manual_in.bid_submission_id,
            result=result,
        )

        from app.core.audit_actions import AuditAction, AuditEntityType
        from app.services.audit_log_service import audit_log_service

        audit_log_service.record_event(
            db=db,
            action=AuditAction.VERIFICATION_COMPLETED,
            entity_type=AuditEntityType.VERIFICATION_RESULT,
            entity_id=created_result.id,
            user_id=user_id,
            bid_submission_id=manual_in.bid_submission_id,
            new_value={
                "provider": "MANUAL_OFFICER_REVIEW",
                "source_mode": SourceMode.MANUAL.value,
                "status": manual_in.verification_status.value,
                "verification_type": manual_in.requirement_type,
                "reference_notes": manual_in.reference_notes,
            },
            details=f"Manual officer verification recorded ({manual_in.verification_status.value}) for {manual_in.requirement_type}",
        )

        return created_result


verification_service = VerificationService()
