from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DiscrepancyBase(BaseModel):
    bid_submission_id: int
    tender_requirement_id: int | None = None
    bid_document_id: int | None = None
    verification_result_id: int | None = None
    compliance_check_id: int | None = None
    type: str
    severity: str = "MEDIUM"
    status: str = "OPEN"
    title: str
    description: str
    expected_value: str | None = None
    observed_value: str | None = None
    source: str = "CROSS_VERIFICATION"
    evidence: dict[str, Any] | None = None
    finding_key: str | None = None


class DiscrepancyCreate(DiscrepancyBase):
    pass


class DiscrepancyUpdate(BaseModel):
    status: str | None = Field(default=None, description="OPEN, RESOLVED, or WAIVED")
    severity: str | None = None
    title: str | None = None
    description: str | None = None
    resolution_note: str | None = None
    resolved_at: datetime | None = None


class DiscrepancyResponse(DiscrepancyBase):
    id: int
    detected_at: datetime
    resolved_at: datetime | None = None
    resolution_note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
