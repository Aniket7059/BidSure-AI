from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.bid_document_repository import (
    bid_document_repository,
)
from app.repositories.bid_submission_repository import (
    bid_submission_repository,
)
from app.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)
from app.schemas.bid_document import (
    BidDocumentCreate,
    BidDocumentResponse,
    DocumentExtractionResponse,
)
from app.services.document_intelligence.document_service import (
    document_processing_service,
)


from app.api.dependencies import require_role

router = APIRouter(
    prefix="/bid-submissions",
    tags=["Bid Documents"],
    dependencies=[Depends(require_role("PROCUREMENT_OFFICER", "ADMIN"))],
)


from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status

from app.services.document_upload_service import document_upload_service


@router.post(
    "/{bid_submission_id}/documents",
    response_model=BidDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bid_document(
    bid_submission_id: int,
    file: UploadFile | None = File(None),
    document_type: str | None = Form(None),
    document_data: BidDocumentCreate | None = Body(None),
    db: Session = Depends(get_db),
):
    submission = bid_submission_repository.get_by_id(
        db,
        bid_submission_id,
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid submission not found.",
        )

    # 1. Primary path: Multipart file upload
    if file is not None:
        if not document_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Form parameter 'document_type' is required for file uploads.",
            )
        try:
            return document_upload_service.upload_document(
                db=db,
                bid_submission_id=bid_submission_id,
                file_obj=file.file,
                original_filename=file.filename or "unnamed_document.pdf",
                document_type=document_type,
                content_type=file.content_type,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )

    # 2. Fallback path for internal test fixtures / legacy creation
    if document_data is not None:
        return bid_document_repository.create(
            db,
            bid_submission_id,
            document_data,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either a file upload (multipart/form-data) or document metadata (JSON) must be provided.",
    )


@router.get(
    "/{bid_submission_id}/documents",
    response_model=list[BidDocumentResponse],
)
def get_bid_documents(
    bid_submission_id: int,
    db: Session = Depends(get_db),
):
    submission = bid_submission_repository.get_by_id(
        db,
        bid_submission_id,
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid submission not found.",
        )

    return bid_document_repository.get_by_submission_id(
        db,
        bid_submission_id,
    )


@router.post(
    "/documents/{bid_document_id}/process",
    response_model=DocumentExtractionResponse,
)
def process_document(
    bid_document_id: int,
    db: Session = Depends(get_db),
):
    """
    Run Document Intelligence on a previously registered BidDocument.

    The endpoint:
    1. Finds the BidDocument.
    2. Passes its file path to DocumentProcessingService.
    3. Persists the extraction attempt.
    4. Returns the resulting extraction record.

    This endpoint does not perform compliance verification.
    """

    document = bid_document_repository.get_by_id(
        db,
        bid_document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid document not found.",
        )

    extraction = document_processing_service.process_document(
        db=db,
        bid_document_id=document.id,
        file_path=document.file_path,
    )

    return extraction


@router.get(
    "/documents/{bid_document_id}/extraction",
    response_model=DocumentExtractionResponse,
)
def get_document_extraction(
    bid_document_id: int,
    db: Session = Depends(get_db),
):
    """
    Return the latest Document Intelligence extraction
    for a BidDocument.
    """

    document = bid_document_repository.get_by_id(
        db,
        bid_document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid document not found.",
        )

    extraction_repository = DocumentExtractionRepository()

    extraction = (
        extraction_repository.get_latest_by_document_id(
            db,
            bid_document_id,
        )
    )

    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No extraction found for this document.",
        )

    return extraction