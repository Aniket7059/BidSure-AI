from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class RecommendationType(str, Enum):
    PROCEED = "PROCEED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HIGH_RISK_REVIEW = "HIGH_RISK_REVIEW"
    DO_NOT_RECOMMEND = "DO_NOT_RECOMMEND"


class RecommendationConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class GenerationSource(str, Enum):
    GEMINI = "GEMINI"
    RULE_ENGINE = "RULE_ENGINE"


class CriticalIssueItem(BaseModel):
    requirement_id: int | None = None
    requirement_type: str | None = None
    status: str = "FAIL"
    severity: str = "HIGH"
    reason: str
    source_reference: str | None = None


class ReviewPriorityItem(BaseModel):
    priority: int
    requirement_id: int | None = None
    requirement_type: str | None = None
    reason: str
    suggested_officer_action: str


class MissingEvidenceItem(BaseModel):
    requirement_id: int | None = None
    requirement_type: str | None = None
    description: str
    is_mandatory: bool = True
    evidence_type: str = "MISSING_DOCUMENT"  # MISSING_DOCUMENT or VERIFICATION_UNAVAILABLE


class StrengthItem(BaseModel):
    requirement_type: str | None = None
    description: str


class OfficerActionItem(BaseModel):
    action_type: str
    description: str


class RecommendationResponse(BaseModel):
    id: int | None = None
    assessment_id: int
    bid_submission_id: int
    overall_status: str
    score: float | None = None
    risk_level: str | None = None
    recommendation: RecommendationType
    confidence: RecommendationConfidence
    summary: str
    critical_issues: list[CriticalIssueItem] = Field(default_factory=list)
    review_items: list[ReviewPriorityItem] = Field(default_factory=list)
    missing_evidence: list[MissingEvidenceItem] = Field(default_factory=list)
    strengths: list[StrengthItem] = Field(default_factory=list)
    officer_actions: list[OfficerActionItem] = Field(default_factory=list)
    generated_by: GenerationSource = GenerationSource.RULE_ENGINE
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
