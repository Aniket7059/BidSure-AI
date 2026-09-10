import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.bid_document import BidDocument
from app.models.bid_submission import BidSubmission
from app.models.bidder import Bidder
from app.models.compliance_assessment import ComplianceAssessment
from app.models.compliance_check import ComplianceCheck
from app.models.discrepancy import Discrepancy
from app.models.procurement_decision import ProcurementDecision
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.repositories.audit_log_repository import audit_log_repository
from app.schemas.dashboard import (
    BidEvaluationDashboardResponse,
    DashboardAuditEventItem,
    DashboardAuditSummary,
    DashboardBidderInfo,
    DashboardBidSubmissionInfo,
    DashboardComplianceSummary,
    DashboardDecisionSummary,
    DashboardDecisionUser,
    DashboardDiscrepancyItem,
    DashboardDocumentItem,
    DashboardRecommendationSummary,
    DashboardRequirementItem,
    DashboardSummary,
    DashboardTenderInfo,
    DashboardVerificationItem,
    DiscrepancyCountBreakdown,
    DocumentCountBreakdown,
    RequirementCountBreakdown,
    TenderDashboardBidItem,
    TenderDashboardResponse,
    TenderDashboardSummary,
    VerificationCountBreakdown,
)

logger = logging.getLogger(__name__)


def mask_pan(pan: str | None) -> str | None:
    if not pan:
        return None
    pan_str = str(pan).strip()
    if len(pan_str) == 10:
        return f"{pan_str[:3]}****{pan_str[-1:]}"
    return "MASKED_PAN"


def mask_gstin(gstin: str | None) -> str | None:
    if not gstin:
        return None
    gstin_str = str(gstin).strip()
    if len(gstin_str) == 15:
        return f"{gstin_str[:5]}****{gstin_str[-2:]}"
    return "MASKED_GSTIN"


class DashboardService:
    """
    Read-only Aggregation Service for the Procurement Officer Dashboard.

    Aggregates existing backend state across Tenders, Requirements, Bidders, Submissions,
    Documents, Verification Results, Discrepancies, Compliance Assessments,
    AI Recommendations, Procurement Officer Final Decisions, and Audit Trail.

    Guarantees:
    - Pure read model (zero side effects, no evaluator execution, no Gemini calls, no decision creation).
    - Preserves system distinction between Automated Assessment, AI Recommendation, and Officer Final Decision.
    """

    def get_bid_submission_dashboard(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> BidEvaluationDashboardResponse:
        # Step 1: Eager load BidSubmission and related entities
        stmt = (
            select(BidSubmission)
            .where(BidSubmission.id == bid_submission_id)
            .options(
                selectinload(BidSubmission.tender),
                selectinload(BidSubmission.bidder),
                selectinload(BidSubmission.documents).selectinload(
                    BidDocument.extractions
                ),
                selectinload(BidSubmission.verification_results),
                selectinload(BidSubmission.compliance_checks).selectinload(
                    ComplianceCheck.tender_requirement
                ),
                selectinload(BidSubmission.compliance_assessments),
                selectinload(BidSubmission.discrepancies),
                selectinload(BidSubmission.procurement_decision).selectinload(
                    ProcurementDecision.decided_by_user
                ),
            )
        )
        submission = db.scalars(stmt).first()
        if not submission:
            raise ValueError(f"Bid submission #{bid_submission_id} not found")

        tender = submission.tender
        bidder = submission.bidder

        # Load all TenderRequirements for requirement matrix completeness
        req_stmt = select(TenderRequirement).where(
            TenderRequirement.tender_id == submission.tender_id
        )
        tender_requirements = list(db.scalars(req_stmt).all())

        # Step 2: Format Header Metadata
        bid_info = DashboardBidSubmissionInfo(
            id=submission.id,
            tender_id=submission.tender_id,
            bidder_id=submission.bidder_id,
            status=submission.status,
            submitted_at=submission.submitted_at,
            created_at=submission.created_at,
            updated_at=submission.updated_at,
        )

        tender_info = DashboardTenderInfo(
            id=tender.id if tender else submission.tender_id,
            reference_number=tender.reference_number if tender else "N/A",
            title=tender.title if tender else "N/A",
            description=tender.description if tender else None,
            status=tender.status if tender else "UNKNOWN",
            created_at=tender.created_at if tender else submission.created_at,
            updated_at=tender.updated_at if tender else submission.updated_at,
            requirement_count=len(tender_requirements),
        )

        bidder_info = DashboardBidderInfo(
            id=bidder.id if bidder else submission.bidder_id,
            company_name=bidder.company_name if bidder else "N/A",
            gstin=mask_gstin(bidder.gstin) if bidder else None,
            pan=mask_pan(bidder.pan) if bidder else None,
            udyam_number=bidder.udyam_number if bidder else None,
            contact_email=bidder.contact_email if bidder else None,
            contact_phone=bidder.contact_phone if bidder else None,
        )

        # Step 3: Latest Compliance Assessment
        latest_assessment: ComplianceAssessment | None = None
        if submission.compliance_assessments:
            # Pick latest by assessed_at or id
            latest_assessment = max(
                submission.compliance_assessments,
                key=lambda a: (a.assessed_at or a.created_at, a.id),
            )

        # Step 4: Format Requirements Matrix
        # Map checks and discrepancies by requirement_id
        check_by_req: dict[int, ComplianceCheck] = {
            c.tender_requirement_id: c for c in submission.compliance_checks
        }
        verifications_list = list(submission.verification_results or [])

        # Discrepancies by requirement_id
        disc_by_req: dict[int, list[Discrepancy]] = {}
        for d in submission.discrepancies or []:
            if d.tender_requirement_id:
                disc_by_req.setdefault(d.tender_requirement_id, []).append(d)

        req_items: list[DashboardRequirementItem] = []
        mandatory_breakdown = {"total": 0, "pass": 0, "fail": 0, "review": 0}
        optional_breakdown = {"total": 0, "pass": 0, "fail": 0, "review": 0}

        for req in tender_requirements:
            check = check_by_req.get(req.id)
            status_val = check.status if check else "PENDING"
            reason_val = check.reason if check else None

            # Determine verification status for requirement
            related_verifs = [
                v
                for v in verifications_list
                if v.requirement_type == req.requirement_type
            ]
            if related_verifs:
                verif_status = related_verifs[0].verification_status
            else:
                verif_status = "PENDING" if check else "NOT_APPLICABLE"

            # Evidence count from check.evidence dictionary if present
            ev_count = 0
            if check and check.evidence:
                if isinstance(check.evidence, dict):
                    ev_count = len(check.evidence.get("extracted_fields", {})) or len(check.evidence)
                elif isinstance(check.evidence, list):
                    ev_count = len(check.evidence)

            discs = disc_by_req.get(req.id, [])

            req_item = DashboardRequirementItem(
                requirement_id=req.id,
                requirement_type=req.requirement_type,
                requirement_name=req.requirement_name,
                description=req.description,
                mandatory=req.is_required,
                status=status_val,
                reason=reason_val,
                verification_status=verif_status,
                evidence_count=ev_count,
                discrepancy_count=len(discs),
            )
            req_items.append(req_item)

            # Update count breakdowns
            target_breakdown = (
                mandatory_breakdown if req.is_required else optional_breakdown
            )
            target_breakdown["total"] += 1
            if status_val == "PASS":
                target_breakdown["pass"] += 1
            elif status_val == "FAIL":
                target_breakdown["fail"] += 1
            elif status_val == "REVIEW":
                target_breakdown["review"] += 1

        # Step 5: Format Documents Section
        doc_items: list[DashboardDocumentItem] = []
        doc_submitted_count = len(submission.documents or [])
        doc_processed_count = 0
        doc_failed_count = 0

        for doc in submission.documents or []:
            latest_ext = None
            if doc.extractions:
                latest_ext = max(doc.extractions, key=lambda e: e.id)

            ext_status = latest_ext.extraction_status if latest_ext else None
            conf_score = latest_ext.confidence_score if latest_ext else None

            if doc.status in ("PROCESSED", "EXTRACTED", "VERIFIED"):
                doc_processed_count += 1
            elif doc.status in ("FAILED", "ERROR"):
                doc_failed_count += 1

            doc_items.append(
                DashboardDocumentItem(
                    id=doc.id,
                    document_type=doc.document_type,
                    file_name=doc.file_name,
                    status=doc.status,
                    uploaded_at=doc.uploaded_at,
                    extraction_status=ext_status,
                    confidence_score=conf_score,
                )
            )

        # Step 6: Format Verification Section
        verif_items: list[DashboardVerificationItem] = []
        verif_counts = {
            "verified": 0,
            "failed": 0,
            "review": 0,
            "pending": 0,
            "error": 0,
        }

        for v in submission.verification_results or []:
            v_status = v.verification_status
            if v_status == "VERIFIED":
                verif_counts["verified"] += 1
            elif v_status in ("FAILED", "MISMATCH"):
                verif_counts["failed"] += 1
            elif v_status == "REVIEW":
                verif_counts["review"] += 1
            elif v_status in ("PENDING", "NOT_VERIFIED"):
                verif_counts["pending"] += 1
            elif v_status in ("ERROR", "EXCEPTION"):
                verif_counts["error"] += 1

            verif_items.append(
                DashboardVerificationItem(
                    id=v.id,
                    verification_type=v.verification_type,
                    provider=v.provider,
                    status=v.verification_status,
                    identifier=v.identifier,
                    message=v.message,
                    verified_at=v.checked_at,
                    bid_document_id=v.bid_document_id,
                )
            )

        # Step 7: Format Discrepancies Section (Sorted critical/high first, open first)
        disc_items: list[DashboardDiscrepancyItem] = []
        severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        status_rank = {"OPEN": 0, "WAIVED": 1, "RESOLVED": 2}

        sorted_discrepancies = sorted(
            submission.discrepancies or [],
            key=lambda d: (
                status_rank.get(d.status, 9),
                severity_rank.get(d.severity, 9),
                d.created_at,
            ),
        )

        open_disc_count = 0
        critical_disc_count = 0
        high_disc_count = 0

        for d in sorted_discrepancies:
            if d.status == "OPEN":
                open_disc_count += 1
                if d.severity == "CRITICAL":
                    critical_disc_count += 1
                elif d.severity == "HIGH":
                    high_disc_count += 1

            disc_items.append(
                DashboardDiscrepancyItem(
                    id=d.id,
                    type=d.type,
                    severity=d.severity,
                    status=d.status,
                    title=d.title,
                    description=d.description,
                    requirement_id=d.tender_requirement_id,
                    bid_document_id=d.bid_document_id,
                    verification_result_id=d.verification_result_id,
                    created_at=d.created_at,
                    resolved_at=d.resolved_at,
                )
            )

        # Step 8: Format Compliance Assessment Section
        compliance_summary: DashboardComplianceSummary | None = None
        if latest_assessment:
            meta = latest_assessment.assessment_metadata or {}
            compliance_summary = DashboardComplianceSummary(
                status=latest_assessment.status,
                score=latest_assessment.score,
                risk_level=latest_assessment.risk_level,
                mandatory_pass=meta.get("mandatory_pass", mandatory_breakdown["pass"]),
                mandatory_fail=meta.get("mandatory_fail", mandatory_breakdown["fail"]),
                mandatory_review=meta.get("mandatory_review", mandatory_breakdown["review"]),
                optional_pass=meta.get("optional_pass", optional_breakdown["pass"]),
                optional_fail=meta.get("optional_fail", optional_breakdown["fail"]),
                optional_review=meta.get("optional_review", optional_breakdown["review"]),
                assessed_at=latest_assessment.assessed_at,
            )

        # Step 9: Format AI Recommendation Section (Pure Read from stored metadata)
        recommendation_summary: DashboardRecommendationSummary | None = None
        if latest_assessment and latest_assessment.assessment_metadata:
            detail = latest_assessment.assessment_metadata.get("recommendation_detail")
            if detail and isinstance(detail, dict):
                try:
                    recommendation_summary = DashboardRecommendationSummary(
                        recommendation=detail.get("recommendation", "REVIEW_REQUIRED"),
                        confidence=detail.get("confidence"),
                        summary=detail.get("summary", ""),
                        critical_issues=detail.get("critical_issues", []),
                        review_items=detail.get("review_items", []),
                        missing_evidence=detail.get("missing_evidence", []),
                        strengths=detail.get("strengths", []),
                        officer_actions=detail.get("officer_actions", []),
                        generated_by=detail.get("generated_by", "RULE_ENGINE"),
                        generated_at=detail.get("generated_at") or latest_assessment.created_at,
                    )
                except Exception as exc:
                    logger.warning(f"Error parsing recommendation_detail for submission #{bid_submission_id}: {exc}")

        # Step 10: Format Procurement Officer Decision Section
        decision_summary: DashboardDecisionSummary | None = None
        if submission.procurement_decision:
            pd = submission.procurement_decision
            decided_by_user = pd.decided_by_user
            decision_user = DashboardDecisionUser(
                id=pd.decided_by,
                full_name=decided_by_user.full_name if decided_by_user else f"Officer #{pd.decided_by}",
                role=decided_by_user.role if decided_by_user else "PROCUREMENT_OFFICER",
            )
            decision_summary = DashboardDecisionSummary(
                id=pd.id,
                decision=pd.decision,
                reason=pd.reason,
                decided_by=decision_user,
                decided_at=pd.decided_at,
                recommendation_at_decision=pd.recommendation_at_decision,
                score_at_decision=pd.score_snapshot,
                risk_at_decision=pd.risk_snapshot,
                override=pd.is_override,
            )

        # Step 11: Format Audit Summary Section
        audit_logs, audit_total = audit_log_repository.list_by_bid_submission(
            db, bid_submission_id, limit=10, offset=0
        )
        audit_events: list[DashboardAuditEventItem] = []
        for al in audit_logs:
            audit_events.append(
                DashboardAuditEventItem(
                    id=al.id,
                    action=al.action,
                    entity_type=al.entity_type,
                    entity_id=al.entity_id,
                    actor=f"User #{al.user_id}" if al.user_id else "SYSTEM",
                    details=al.details,
                    created_at=al.created_at,
                )
            )

        last_act = audit_events[0].created_at if audit_events else submission.updated_at
        audit_summary = DashboardAuditSummary(
            last_activity_at=last_act,
            total_events=audit_total,
            events=audit_events,
        )

        # Step 12: Assemble Overall Summary Block
        dashboard_summary = DashboardSummary(
            overall_status=latest_assessment.status if latest_assessment else submission.status,
            score=latest_assessment.score if latest_assessment else None,
            risk_level=latest_assessment.risk_level if latest_assessment else None,
            mandatory=RequirementCountBreakdown(**mandatory_breakdown),
            optional=RequirementCountBreakdown(**optional_breakdown),
            documents=DocumentCountBreakdown(
                submitted=doc_submitted_count,
                processed=doc_processed_count,
                failed_processing=doc_failed_count,
            ),
            verification=VerificationCountBreakdown(**verif_counts),
            discrepancies=DiscrepancyCountBreakdown(
                open=open_disc_count,
                critical=critical_disc_count,
                high=high_disc_count,
            ),
            recommendation=recommendation_summary.recommendation if recommendation_summary else None,
            final_decision=decision_summary.decision if decision_summary else None,
        )

        return BidEvaluationDashboardResponse(
            bid_submission=bid_info,
            tender=tender_info,
            bidder=bidder_info,
            summary=dashboard_summary,
            requirements=req_items,
            documents=doc_items,
            verification=verif_items,
            discrepancies=disc_items,
            compliance=compliance_summary,
            recommendation=recommendation_summary,
            decision=decision_summary,
            audit=audit_summary,
        )

    def get_tender_dashboard(
        self,
        db: Session,
        tender_id: int,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TenderDashboardResponse:
        # Load Tender
        tender_stmt = (
            select(Tender)
            .where(Tender.id == tender_id)
            .options(selectinload(Tender.requirements))
        )
        tender = db.scalars(tender_stmt).first()
        if not tender:
            raise ValueError(f"Tender #{tender_id} not found")

        # Load all BidSubmissions for Tender
        bids_stmt = (
            select(BidSubmission)
            .where(BidSubmission.tender_id == tender_id)
            .options(
                selectinload(BidSubmission.bidder),
                selectinload(BidSubmission.compliance_assessments),
                selectinload(BidSubmission.procurement_decision),
            )
        )
        all_submissions = list(db.scalars(bids_stmt).all())

        # Calculate Tender Dashboard Summary Metrics across all bids
        total_bids = len(all_submissions)
        assessed_count = 0
        pending_assessment_count = 0
        compliant_count = 0
        non_compliant_count = 0
        review_count = 0
        qualified_count = 0
        disqualified_count = 0
        undecided_count = 0

        bid_items: list[TenderDashboardBidItem] = []

        for sub in all_submissions:
            latest_ass: ComplianceAssessment | None = None
            if sub.compliance_assessments:
                latest_ass = max(
                    sub.compliance_assessments,
                    key=lambda a: (a.assessed_at or a.created_at, a.id),
                )

            if latest_ass:
                assessed_count += 1
                c_status = latest_ass.status
                if c_status == "COMPLIANT":
                    compliant_count += 1
                elif c_status == "NON_COMPLIANT":
                    non_compliant_count += 1
                elif c_status == "REVIEW":
                    review_count += 1
            else:
                pending_assessment_count += 1

            dec = sub.procurement_decision
            if dec:
                if dec.decision == "QUALIFIED":
                    qualified_count += 1
                elif dec.decision == "DISQUALIFIED":
                    disqualified_count += 1
            else:
                undecided_count += 1

            # Check status filter
            c_status_val = latest_ass.status if latest_ass else None
            dec_val = dec.decision if dec else None
            rec_val = (
                latest_ass.assessment_metadata.get("recommendation_detail", {}).get("recommendation")
                if latest_ass and latest_ass.assessment_metadata
                else None
            )

            if status_filter:
                sf = status_filter.upper()
                if sf not in (
                    (c_status_val or "").upper(),
                    (dec_val or "").upper(),
                    (rec_val or "").upper(),
                    sub.status.upper(),
                ):
                    continue

            bid_items.append(
                TenderDashboardBidItem(
                    id=sub.id,
                    bidder_id=sub.bidder_id,
                    bidder_name=sub.bidder.company_name if sub.bidder else f"Bidder #{sub.bidder_id}",
                    status=sub.status,
                    submitted_at=sub.submitted_at,
                    compliance_status=c_status_val,
                    score=latest_ass.score if latest_ass else None,
                    risk_level=latest_ass.risk_level if latest_ass else None,
                    recommendation=rec_val,
                    final_decision=dec_val,
                )
            )

        # Sort bids by submission id DESC and apply pagination
        bid_items.sort(key=lambda b: b.id, reverse=True)
        paginated_bids = bid_items[offset : offset + limit]

        tender_info = DashboardTenderInfo(
            id=tender.id,
            reference_number=tender.reference_number,
            title=tender.title,
            description=tender.description,
            status=tender.status,
            created_at=tender.created_at,
            updated_at=tender.updated_at,
            requirement_count=len(tender.requirements or []),
        )

        tender_summary = TenderDashboardSummary(
            total_bids=total_bids,
            assessed_count=assessed_count,
            pending_assessment_count=pending_assessment_count,
            compliant_count=compliant_count,
            non_compliant_count=non_compliant_count,
            review_count=review_count,
            qualified_count=qualified_count,
            disqualified_count=disqualified_count,
            undecided_count=undecided_count,
        )

        page_num = (offset // limit) + 1 if limit > 0 else 1

        return TenderDashboardResponse(
            tender=tender_info,
            summary=tender_summary,
            bids=paginated_bids,
            total_bids=len(bid_items),
            page=page_num,
            page_size=limit,
        )


dashboard_service = DashboardService()
