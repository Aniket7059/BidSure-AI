from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.compliance_assessment import ComplianceAssessment
from app.repositories.compliance_assessment_repository import (
    compliance_assessment_repository,
)
from app.repositories.compliance_check_repository import (
    compliance_check_repository,
)
from app.repositories.tender_requirement_repository import (
    tender_requirement_repository,
)
from app.schemas.compliance_assessment import (
    ComplianceAssessmentCreate,
    ComplianceAssessmentUpdate,
)
from app.services.compliance_service import (
    compliance_service,
)


class ComplianceAssessmentService:
    """
    Generates an overall compliance assessment for a bid submission.

    Task 8 Implementation:
    - Triggers evaluation of ALL tender requirements for the submission.
    - Summarizes PASS, FAIL, MISSING, NOT_APPLICABLE, and REVIEW checks.
    - Ensures mandatory requirement failures/missing evidence drive NON_COMPLIANT status & HIGH risk.
    - Ensures optional requirements (NOT_APPLICABLE) do not incorrectly cause disqualification.
    """

    def assess_submission(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> ComplianceAssessment:

        # --------------------------------------------------
        # 1. Evaluate all tender requirements for submission
        # --------------------------------------------------

        compliance_service.evaluate_submission(
            db,
            bid_submission_id,
        )

        # --------------------------------------------------
        # 2. Retrieve resulting compliance checks
        # --------------------------------------------------

        checks = (
            compliance_check_repository.get_by_submission(
                db,
                bid_submission_id,
            )
        )

        # --------------------------------------------------
        # 3. Handle no compliance checks
        # --------------------------------------------------

        if not checks:

            assessment_data = ComplianceAssessmentCreate(
                bid_submission_id=bid_submission_id,
                score=None,
                risk_level=None,
                recommendation=None,
                status="PENDING",
                summary=(
                    "No compliance checks are available "
                    "for this bid submission."
                ),
                assessment_metadata={
                    "total_checks": 0,
                    "passed": 0,
                    "failed": 0,
                    "missing": 0,
                    "not_applicable": 0,
                    "review": 0,
                    "pending": 0,
                },
                assessed_at=None,
            )

            latest_assessment = (
                compliance_assessment_repository.get_latest_by_submission(
                    db, bid_submission_id
                )
            )
            if latest_assessment:
                update_data = ComplianceAssessmentUpdate(
                    score=None,
                    risk_level=None,
                    status="PENDING",
                    summary=assessment_data.summary,
                    assessment_metadata=assessment_data.assessment_metadata,
                    assessed_at=None,
                )
                return compliance_assessment_repository.update(
                    db, latest_assessment, update_data
                )

            return compliance_assessment_repository.create(
                db,
                assessment_data,
            )

        # --------------------------------------------------
        # 4. Count compliance check statuses & mandatory vs optional breakdown
        # --------------------------------------------------

        total_checks = len(checks)

        mandatory_pass_count = 0
        mandatory_fail_count = 0
        mandatory_missing_count = 0
        mandatory_review_count = 0

        optional_pass_count = 0
        optional_fail_count = 0
        optional_missing_count = 0
        optional_review_count = 0

        missing_count = 0
        pending_count = 0
        review_count = 0
        passed_count = 0
        failed_count = 0
        not_applicable_count = 0

        for check in checks:
            req = getattr(check, "tender_requirement", None)
            if not req and check.tender_requirement_id:
                req = tender_requirement_repository.get_by_id(
                    db, check.tender_requirement_id
                )

            is_req = req.is_required if req is not None else True
            st = check.status.upper()

            if st == "PASS":
                passed_count += 1
            elif st in ("FAIL", "INVALID", "DEBARRED"):
                failed_count += 1
            elif st == "MISSING":
                missing_count += 1
            elif st == "PENDING":
                pending_count += 1
            elif st == "REVIEW":
                review_count += 1
            elif st == "NOT_APPLICABLE":
                not_applicable_count += 1

            if st == "NOT_APPLICABLE":
                pass
            elif is_req:
                if st == "PASS":
                    mandatory_pass_count += 1
                elif st in ("FAIL", "INVALID", "DEBARRED"):
                    mandatory_fail_count += 1
                elif st == "MISSING":
                    mandatory_missing_count += 1
                else:  # REVIEW, PENDING
                    mandatory_review_count += 1
            else:  # Optional requirement
                if st == "PASS":
                    optional_pass_count += 1
                elif st in ("FAIL", "INVALID"):
                    optional_fail_count += 1
                elif st == "MISSING":
                    optional_missing_count += 1
                else:  # REVIEW, PENDING
                    optional_review_count += 1

        total_mandatory = (
            mandatory_pass_count
            + mandatory_fail_count
            + mandatory_missing_count
            + mandatory_review_count
        )

        # --------------------------------------------------
        # 5. Calculate deterministic compliance score (0.0 .. 100.0)
        # --------------------------------------------------

        scorable_total = total_checks - not_applicable_count
        scorable_earned = mandatory_pass_count + optional_pass_count

        if scorable_total > 0:
            raw_score = (scorable_earned / scorable_total) * 100.0
            score = round(max(0.0, min(100.0, raw_score)), 2)
        else:
            score = 0.0

        # --------------------------------------------------
        # 6. Check unresolved discrepancies for risk assessment
        # --------------------------------------------------

        from app.repositories.discrepancy_repository import discrepancy_repository

        discrepancies = discrepancy_repository.get_by_submission_id(
            db, bid_submission_id
        )
        unresolved_disc = [
            d for d in discrepancies
            if str(getattr(d, "status", "OPEN")).upper() in ("OPEN", "UNRESOLVED")
        ]
        has_critical_discrepancy = any(
            str(getattr(d, "severity", "")).upper() == "CRITICAL"
            or str(getattr(d, "type", "")).upper() in ("DEBARRED_VENDOR", "FRAUD_SUSPECTED")
            for d in unresolved_disc
        )

        # --------------------------------------------------
        # 7. Determine overall compliance status
        # --------------------------------------------------

        if mandatory_fail_count > 0 or mandatory_missing_count > 0:
            status = "NON_COMPLIANT"
        elif mandatory_review_count > 0:
            status = "REVIEW"
        elif total_mandatory > 0 and mandatory_pass_count == total_mandatory:
            status = "COMPLIANT"
        else:
            status = "REVIEW"

        # --------------------------------------------------
        # 8. Determine conservative risk level
        # --------------------------------------------------

        if mandatory_fail_count > 0 or mandatory_missing_count > 0 or has_critical_discrepancy:
            risk_level = "HIGH"
        elif mandatory_review_count > 0 or len(unresolved_disc) > 0:
            risk_level = "MEDIUM"
        elif status == "COMPLIANT":
            risk_level = "LOW"
        else:
            risk_level = "MEDIUM"

        # --------------------------------------------------
        # 9. Generate summary & metadata
        # --------------------------------------------------

        summary = (
            f"Compliance assessment completed for {total_checks} requirement(s): "
            f"{passed_count} passed ({mandatory_pass_count} mandatory), "
            f"{failed_count} failed ({mandatory_fail_count} mandatory), "
            f"{missing_count} missing ({mandatory_missing_count} mandatory), "
            f"{review_count + pending_count} under review ({mandatory_review_count} mandatory), "
            f"{not_applicable_count} not applicable."
        )

        assessment_metadata = {
            "total_checks": total_checks,
            "passed": passed_count,
            "failed": failed_count,
            "missing": missing_count,
            "pending": pending_count,
            "review": review_count,
            "not_applicable": not_applicable_count,
            "mandatory_pass_count": mandatory_pass_count,
            "mandatory_fail_count": mandatory_fail_count,
            "mandatory_missing_count": mandatory_missing_count,
            "mandatory_review_count": mandatory_review_count,
            "optional_pass_count": optional_pass_count,
            "optional_fail_count": optional_fail_count,
            "optional_missing_count": optional_missing_count,
            "optional_review_count": optional_review_count,
            "unresolved_discrepancies_count": len(unresolved_disc),
        }

        # --------------------------------------------------
        # 10. Persist or Update assessment
        # --------------------------------------------------

        latest_assessment = (
            compliance_assessment_repository.get_latest_by_submission(
                db, bid_submission_id
            )
        )

        from app.core.audit_actions import AuditAction, AuditEntityType
        from app.services.audit_log_service import audit_log_service

        if latest_assessment:
            old_snap = {
                "score": latest_assessment.score,
                "risk_level": latest_assessment.risk_level,
                "status": latest_assessment.status,
            }
            update_data = ComplianceAssessmentUpdate(
                score=score,
                risk_level=risk_level,
                status=status,
                summary=summary,
                assessment_metadata=assessment_metadata,
                assessed_at=datetime.now(timezone.utc),
            )
            updated_ass = compliance_assessment_repository.update(
                db, latest_assessment, update_data
            )
            audit_log_service.record_event(
                db=db,
                action=AuditAction.ASSESSMENT_UPDATED,
                entity_type=AuditEntityType.COMPLIANCE_ASSESSMENT,
                entity_id=updated_ass.id,
                bid_submission_id=bid_submission_id,
                old_value=old_snap,
                new_value={"score": score, "risk_level": risk_level, "status": status},
                details=f"Compliance assessment #{updated_ass.id} updated (Score: {score:.1f}, Risk: {risk_level})",
            )
            return updated_ass

        assessment_data = ComplianceAssessmentCreate(
            bid_submission_id=bid_submission_id,
            score=score,
            risk_level=risk_level,
            recommendation=None,
            status=status,
            summary=summary,
            assessment_metadata=assessment_metadata,
            assessed_at=datetime.now(timezone.utc),
        )

        created_ass = compliance_assessment_repository.create(
            db,
            assessment_data,
        )

        audit_log_service.record_event(
            db=db,
            action=AuditAction.ASSESSMENT_CREATED,
            entity_type=AuditEntityType.COMPLIANCE_ASSESSMENT,
            entity_id=created_ass.id,
            bid_submission_id=bid_submission_id,
            new_value={"score": score, "risk_level": risk_level, "status": status},
            details=f"Compliance assessment #{created_ass.id} created (Score: {score:.1f}, Risk: {risk_level})",
        )

        return created_ass


compliance_assessment_service = ComplianceAssessmentService()