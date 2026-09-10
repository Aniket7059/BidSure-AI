from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.document_extraction import DocumentExtraction
from app.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)

from .orchestrator import DocumentIntelligenceOrchestrator
from .schemas import DocumentIntelligenceResult


class DocumentProcessingService:
    """
    Coordinates document intelligence processing and persistence.

    Responsibilities:
    - Create an extraction record.
    - Run the document intelligence orchestrator.
    - Persist successful extraction results.
    - Persist failures and error information.

    This service does NOT:
    - verify government records,
    - evaluate compliance,
    - calculate compliance scores,
    - make qualification decisions.
    """

    EXTRACTOR_NAME = "BidSureDocumentIntelligence"
    EXTRACTOR_VERSION = "1.0.0"

    def __init__(
        self,
        orchestrator: DocumentIntelligenceOrchestrator | None = None,
        repository: DocumentExtractionRepository | None = None,
    ):
        self.orchestrator = (
            orchestrator
            or DocumentIntelligenceOrchestrator()
        )
        self.repository = (
            repository
            or DocumentExtractionRepository()
        )

    def process_document(
        self,
        db: Session,
        bid_document_id: int,
        file_path: str,
    ) -> DocumentExtraction:
        """
        Process one BidDocument and persist its extraction result.

        A new DocumentExtraction record is created for every
        processing attempt.
        """

        if bid_document_id <= 0:
            raise ValueError(
                "bid_document_id must be greater than zero."
            )

        if not file_path or not file_path.strip():
            raise ValueError(
                "file_path cannot be empty."
            )

        extraction = DocumentExtraction(
            bid_document_id=bid_document_id,
            extraction_status="PROCESSING",
            extractor_name=self.EXTRACTOR_NAME,
            extractor_version=self.EXTRACTOR_VERSION,
            started_at=datetime.now(timezone.utc),
        )

        extraction = self.repository.create(
            db,
            extraction,
        )

        from app.core.audit_actions import AuditAction, AuditEntityType
        from app.services.audit_log_service import audit_log_service

        # Get bid_submission_id from BidDocument if available
        bid_sub_id = None
        try:
            from app.repositories.bid_document_repository import bid_document_repository
            doc = bid_document_repository.get_by_id(db, bid_document_id)
            if doc:
                bid_sub_id = getattr(doc, "bid_submission_id", None)
        except Exception:
            pass

        audit_log_service.record_event(
            db=db,
            action=AuditAction.DOCUMENT_PROCESSING_STARTED,
            entity_type=AuditEntityType.BID_DOCUMENT,
            entity_id=bid_document_id,
            bid_submission_id=bid_sub_id,
            details=f"Document processing started for bid_document #{bid_document_id}",
        )

        try:
            result = self.orchestrator.process(
                file_path
            )

            self._apply_success(
                extraction,
                result,
            )

            db.commit()
            db.refresh(extraction)

            audit_log_service.record_event(
                db=db,
                action=AuditAction.DOCUMENT_PROCESSING_COMPLETED,
                entity_type=AuditEntityType.BID_DOCUMENT,
                entity_id=bid_document_id,
                bid_submission_id=bid_sub_id,
                new_value={
                    "document_type": result.document_type.value,
                    "confidence": result.classification_confidence,
                    "pages": result.total_pages,
                },
                details=f"Document processing completed for bid_document #{bid_document_id}",
            )

            audit_log_service.record_event(
                db=db,
                action=AuditAction.DOCUMENT_EXTRACTION_CREATED,
                entity_type=AuditEntityType.DOCUMENT_EXTRACTION,
                entity_id=extraction.id,
                bid_submission_id=bid_sub_id,
                new_value={
                    "extraction_id": extraction.id,
                    "confidence_score": extraction.confidence_score,
                },
                details=f"Document extraction #{extraction.id} created for bid_document #{bid_document_id}",
            )

            return extraction

        except Exception as exc:
            self._apply_failure(
                extraction,
                exc,
            )

            db.commit()
            db.refresh(extraction)

            audit_log_service.record_event(
                db=db,
                action=AuditAction.DOCUMENT_PROCESSING_FAILED,
                entity_type=AuditEntityType.BID_DOCUMENT,
                entity_id=bid_document_id,
                bid_submission_id=bid_sub_id,
                details=f"Document processing failed for bid_document #{bid_document_id}: {exc}",
            )

            return extraction

    @staticmethod
    def _apply_success(
        extraction: DocumentExtraction,
        result: DocumentIntelligenceResult,
    ) -> None:
        extraction.extraction_status = "COMPLETED"

        extraction.extracted_text = (
            result.extracted_text
        )

        extraction.extracted_data = {
            "document_type": (
                result.document_type.value
            ),
            "classification_confidence": (
                result.classification_confidence
            ),
            "extraction_method": (
                result.extraction_method.value
            ),
            "total_pages": result.total_pages,
            "total_characters": (
                result.total_characters
            ),
            "fields": result.fields.model_dump(
                mode="json"
            ),
        }

        extraction.confidence_score = (
            result.extraction_confidence
        )

        extraction.error_message = None

        extraction.completed_at = (
            datetime.now(timezone.utc)
        )

    @staticmethod
    def _apply_failure(
        extraction: DocumentExtraction,
        exc: Exception,
    ) -> None:
        extraction.extraction_status = "FAILED"

        extraction.error_message = str(exc)

        extraction.completed_at = (
            datetime.now(timezone.utc)
        )


document_processing_service = DocumentProcessingService()