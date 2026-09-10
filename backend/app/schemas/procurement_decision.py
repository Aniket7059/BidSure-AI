from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProcurementDecisionValue(str, Enum):
    QUALIFIED = "QUALIFIED"
    DISQUALIFIED = "DISQUALIFIED"


class ProcurementDecisionCreate(BaseModel):
    decision: ProcurementDecisionValue
    reason: str = Field(
        ...,
        description="Detailed explanation and legal/procurement grounds for the final decision.",
    )

    @field_validator("reason", mode="before")
    @classmethod
    def validate_reason_non_empty(cls, v: str) -> str:
        if v is None or not str(v).strip():
            raise ValueError("Reason is required and cannot be empty or whitespace-only.")
        cleaned = str(v).strip()
        if len(cleaned) < 10:
            raise ValueError("Reason must be at least 10 characters long to provide adequate justification.")
        return cleaned


class ProcurementDecisionResponse(BaseModel):
    id: int
    bid_submission_id: int
    decision: ProcurementDecisionValue
    reason: str
    decided_by: int
    decided_at: datetime
    assessment_id: int | None = None
    recommendation_at_decision: str | None = None
    score_snapshot: float | None = None
    risk_snapshot: str | None = None
    is_override: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
