from pydantic import BaseModel

from app.core.taxonomy import RequirementType


class ComplianceEvaluationRequest(BaseModel):
    bid_submission_id: int
    tender_requirement_id: int

    requirement_type: RequirementType
    requirement_name: str
    description: str | None = None
    is_required: bool = True
    validation_config: dict | str | None = None

    extracted_data: dict | None = None
    verification_data: dict | None = None

    all_extractions: list[dict] | None = None
    all_verifications: list[dict] | None = None


class ComplianceEvaluationResult(BaseModel):
    status: str
    reason: str
    evidence: dict