from typing import BinaryIO
from sqlalchemy.orm import Session

from app.models.bid_document import BidDocument
from app.repositories.bid_document_repository import bid_document_repository
from app.repositories.bid_submission_repository import bid_submission_repository
from app.schemas.bid_document import BidDocumentCreate
from app.services.storage_service import document_storage_service, DocumentStorageService


class DocumentUploadService:
    """
    Orchestrates the secure document upload workflow:
    - Validates submission existence.
    - Stores file on disk via DocumentStorageService.
    - Creates database BidDocument record from server-derived metadata.
    - Handles transaction failure cleanup (deletes stored file on DB failure).
    """

    def __init__(self, storage_service: DocumentStorageService | None = None) -> None:
        self.storage_service = storage_service or document_storage_service

    def upload_document(
        self,
        db: Session,
        bid_submission_id: int,
        file_obj: BinaryIO,
        original_filename: str,
        document_type: str,
        content_type: str | None = None,
    ) -> BidDocument:
        submission = bid_submission_repository.get_by_id(db, bid_submission_id)
        if not submission:
            raise ValueError(f"Bid submission not found: {bid_submission_id}")

        if not document_type or not document_type.strip():
            raise ValueError("Document type is required.")

        # Save file securely to server storage
        (
            rel_path,
            server_filename,
            file_size,
            file_hash,
            display_name,
            mime_type,
        ) = self.storage_service.save_upload(
            file_obj=file_obj,
            bid_submission_id=bid_submission_id,
            original_filename=original_filename,
            content_type=content_type,
        )

        doc_create = BidDocumentCreate(
            document_type=document_type.upper().strip(),
            file_name=display_name,
            file_path=rel_path,
            content_type=mime_type,
            file_size=file_size,
            file_hash=file_hash,
        )

        try:
            document = bid_document_repository.create(
                db=db,
                bid_submission_id=bid_submission_id,
                document_data=doc_create,
            )

            from app.core.audit_actions import AuditAction, AuditEntityType
            from app.services.audit_log_service import audit_log_service

            audit_log_service.record_event(
                db=db,
                action=AuditAction.DOCUMENT_UPLOADED,
                entity_type=AuditEntityType.BID_DOCUMENT,
                entity_id=document.id,
                bid_submission_id=bid_submission_id,
                new_value={
                    "document_type": document.document_type,
                    "file_name": display_name,
                    "file_size": file_size,
                    "file_hash": file_hash,
                },
                details=f"Uploaded document '{display_name}' ({document.document_type}) for submission #{bid_submission_id}",
            )

            return document
        except Exception as exc:
            # Orphan cleanup if database insertion fails
            self.storage_service.delete_file(rel_path)
            raise exc


document_upload_service = DocumentUploadService()
