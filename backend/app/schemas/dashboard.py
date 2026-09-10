from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


# --- Section 1: Bid Submission & Tender & Bidder Metadata ---

class DashboardBidSubmissionInfo(BaseModel):
    id: int
    tender_id: int
    bidder_id: int
    status: str
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime


class DashboardTenderInfo(BaseModel):
    id: int
    reference_number: str
    title: str
    description: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    requirement_count: int = 0


class DashboardBidderInfo(BaseModel):
    id: int
    company_name: str
    gstin: str | None = None  # Masked
    pan: str | None = None    # Masked
    udyam_number: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


# --- Section 2: Count Breakdowns & Summary ---

class RequirementCountBreakdown(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int = 0
    pass_count: int = Field(0, alias="pass")
    fail_count: int = Field(0, alias="fail")
    review_count: int = Field(0, alias="review")


class DocumentCountBreakdown(BaseModel):
    submitted: int = 0
    processed: int = 0
    failed_processing: int = 0


class VerificationCountBreakdown(BaseModel):
    verified: int = 0
    failed: int = 0
    review: int = 0
    pending: int = 0
    error: int = 0


class DiscrepancyCountBreakdown(BaseModel):
    open: int = 0
    critical: int = 0
    high: int = 0


class DashboardSummary(BaseModel):
    overall_status: str | None = None
    score: float | None = None
    risk_level: str | None = None
    mandatory: RequirementCountBreakdown = Field(default_factory=RequirementCountBreakdown)
    optional: RequirementCountBreakdown = Field(default_factory=RequirementCountBreakdown)
    documents: DocumentCountBreakdown = Field(default_factory=DocumentCountBreakdown)
    verification: VerificationCountBreakdown = Field(default_factory=VerificationCountBreakdown)
    discrepancies: DiscrepancyCountBreakdown = Field(default_factory=DiscrepancyCountBreakdown)
    recommendation: str | None = None
    final_decision: str | None = None


# --- Section 3: Detailed Items ---

class DashboardRequirementItem(BaseModel):
    requirement_id: int
    requirement_type: str
    requirement_name: str
    description: str | None = None
    mandatory: bool
    status: str  # PASS, FAIL, REVIEW, PENDING
    reason: str | None = None
    verification_status: str  # VERIFIED, NOT_FOUND, MISMATCH, PENDING, NOT_APPLICABLE
    evidence_count: int = 0
    discrepancy_count: int = 0


class DashboardDocumentItem(BaseModel):
    id: int
    document_type: str
    file_name: str
    status: str
    uploaded_at: datetime
    extraction_status: str | None = None
    confidence_score: float | None = None


class DashboardVerificationItem(BaseModel):
    id: int
    verification_type: str
    provider: str
    status: str
    identifier: str
    message: str | None = None
    verified_at: datetime | None = None
    bid_document_id: int | None = None


class DashboardDiscrepancyItem(BaseModel):
    id: int
    type: str
    severity: str
    status: str
    title: str
    description: str
    requirement_id: int | None = None
    bid_document_id: int | None = None
    verification_result_id: int | None = None
    created_at: datetime
    resolved_at: datetime | None = None


class DashboardComplianceSummary(BaseModel):
    status: str
    score: float | None = None
    risk_level: str | None = None
    mandatory_pass: int = 0
    mandatory_fail: int = 0
    mandatory_review: int = 0
    optional_pass: int = 0
    optional_fail: int = 0
    optional_review: int = 0
    assessed_at: datetime | None = None


class DashboardRecommendationSummary(BaseModel):
    recommendation: str
    confidence: str | None = None
    summary: str
    critical_issues: list[dict[str, Any]] = Field(default_factory=list)
    review_items: list[dict[str, Any]] = Field(default_factory=list)
    missing_evidence: list[dict[str, Any]] = Field(default_factory=list)
    strengths: list[dict[str, Any]] = Field(default_factory=list)
    officer_actions: list[dict[str, Any]] = Field(default_factory=list)
    generated_by: str
    generated_at: datetime


class DashboardDecisionUser(BaseModel):
    id: int
    full_name: str
    role: str


class DashboardDecisionSummary(BaseModel):
    id: int
    decision: str
    reason: str
    decided_by: DashboardDecisionUser
    decided_at: datetime
    recommendation_at_decision: str | None = None
    score_at_decision: float | None = None
    risk_at_decision: str | None = None
    override: bool = False


class DashboardAuditEventItem(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: int | None = None
    actor: str | None = None
    details: str | None = None
    created_at: datetime


class DashboardAuditSummary(BaseModel):
    last_activity_at: datetime | None = None
    total_events: int = 0
    events: list[DashboardAuditEventItem] = Field(default_factory=list)


# --- Section 4: Primary & Secondary Dashboard API Payloads ---

class BidEvaluationDashboardResponse(BaseModel):
    bid_submission: DashboardBidSubmissionInfo
    tender: DashboardTenderInfo
    bidder: DashboardBidderInfo
    summary: DashboardSummary
    requirements: list[DashboardRequirementItem] = Field(default_factory=list)
    documents: list[DashboardDocumentItem] = Field(default_factory=list)
    verification: list[DashboardVerificationItem] = Field(default_factory=list)
    discrepancies: list[DashboardDiscrepancyItem] = Field(default_factory=list)
    compliance: DashboardComplianceSummary | None = None
    recommendation: DashboardRecommendationSummary | None = None
    decision: DashboardDecisionSummary | None = None
    audit: DashboardAuditSummary = Field(default_factory=DashboardAuditSummary)


class TenderDashboardSummary(BaseModel):
    total_bids: int = 0
    assessed_count: int = 0
    pending_assessment_count: int = 0
    compliant_count: int = 0
    non_compliant_count: int = 0
    review_count: int = 0
    qualified_count: int = 0
    disqualified_count: int = 0
    undecided_count: int = 0


class TenderDashboardBidItem(BaseModel):
    id: int
    bidder_id: int
    bidder_name: str
    status: str
    submitted_at: datetime
    compliance_status: str | None = None
    score: float | None = None
    risk_level: str | None = None
    recommendation: str | None = None
    final_decision: str | None = None


class TenderDashboardResponse(BaseModel):
    tender: DashboardTenderInfo
    summary: TenderDashboardSummary
    bids: list[TenderDashboardBidItem] = Field(default_factory=list)
    total_bids: int = 0
    page: int = 1
    page_size: int = 50


class GlobalActionRequiredItem(BaseModel):
    bid_submission_id: int
    tender_id: int
    tender_reference: str
    bidder_name: str
    compliance_status: str | None = None
    risk_level: str | None = None
    reason: str | None = None
    open_discrepancies: int = 0


class GlobalTenderPreviewItem(BaseModel):
    id: int
    reference_number: str
    title: str
    status: str
    bids_count: int = 0
    created_at: datetime


class GlobalDashboardOverviewResponse(BaseModel):
    active_tenders: int = 0
    bids_under_review: int = 0
    attention_required: int = 0
    awaiting_decision: int = 0
    action_required_items: list[GlobalActionRequiredItem] = Field(default_factory=list)
    active_tenders_preview: list[GlobalTenderPreviewItem] = Field(default_factory=list)
    status_distribution: dict[str, int] = Field(default_factory=dict)
