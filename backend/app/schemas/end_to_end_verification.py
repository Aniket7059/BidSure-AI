from typing import Any
from pydantic import BaseModel, Field


class DocumentExtractionSummaryItem(BaseModel):
    document_id: int
    file_name: str
    document_type: str | None = None
    status: str
    error: str | None = None


class ProviderVerificationSummaryItem(BaseModel):
    requirement_type: str
    identifier: str | None = None
    status: str
    source: str | None = None
    error: str | None = None


class EndToEndVerificationSummary(BaseModel):
    bid_submission_id: int
    tender_id: int
    status: str = "COMPLETED"
    documents_processed_count: int
    verifications_executed_count: int
    has_discrepancies: bool
    discrepancies_count: int
    compliance_checks_count: int
    overall_status: str
    compliance_score: float | None = None
    risk_level: str | None = None
    summary: str | None = None
    documents_summary: list[DocumentExtractionSummaryItem] = Field(default_factory=list)
    verifications_summary: list[ProviderVerificationSummaryItem] = Field(default_factory=list)
    workflow_log: list[str] = Field(default_factory=list)
