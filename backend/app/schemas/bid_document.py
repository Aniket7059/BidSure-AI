from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BidDocumentCreate(BaseModel):
    document_type: str
    file_name: str
    file_path: str
    content_type: str | None = None
    file_size: int | None = None
    file_hash: str | None = None


class BidDocumentResponse(BaseModel):
    id: int
    bid_submission_id: int
    document_type: str
    file_name: str
    file_path: str
    content_type: str | None
    file_size: int | None
    file_hash: str | None = None
    status: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentExtractionResponse(BaseModel):
    """
    API response for a document extraction attempt.

    This exposes the persisted Document Intelligence result
    without exposing SQLAlchemy internals.
    """

    id: int
    bid_document_id: int
    extraction_status: str

    extracted_data: dict | None = None
    extracted_text: str | None = None

    confidence_score: float | None = None

    extractor_name: str | None = None
    extractor_version: str | None = None

    error_message: str | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)