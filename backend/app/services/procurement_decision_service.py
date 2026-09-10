from sqlalchemy.orm import Session

from app.models.procurement_decision import ProcurementDecision
from app.models.user import User
from app.repositories.bid_submission_repository import (
    bid_submission_repository,
)
from app.repositories.compliance_assessment_repository import (
    compliance_assessment_repository,
)
from app.repositories.procurement_decision_repository import (
    procurement_decision_repository,
)
from app.schemas.procurement_decision import (
    ProcurementDecisionCreate,
    ProcurementDecisionValue,
)


class ProcurementDecisionService:
    """
    Handles human-in-the-loop final procurement decision workflow.

    The Procurement Officer's decision (QUALIFIED / DISQUALIFIED) is authoritative,
    auditable, immutable, and strictly separate from automated compliance scoring
    and AI recommendations.
    """

    def record_decision(
        self,
        db: Session,
        current_user: User,
        bid_submission_id: int,
        decision_data: ProcurementDecisionCreate,
    ) -> ProcurementDecision:
        submission = bid_submission_repository.get_by_id(db, bid_submission_id)
        if submission is None:
            raise ValueError(f"Bid submission not found: {bid_submission_id}")

        existing_decision = procurement_decision_repository.get_by_submission_id(
            db, bid_submission_id
        )
        if existing_decision is not None:
            raise ValueError(
                f"A final procurement decision has already been recorded for bid submission #{bid_submission_id}."
            )

        assessment = compliance_assessment_repository.get_latest_by_submission(
            db, bid_submission_id
        )

        assessment_id = assessment.id if assessment else None
        score_snapshot = assessment.score if assessment else None
        risk_snapshot = assessment.risk_level if assessment else None

        rec_detail = (assessment.assessment_metadata or {}).get("recommendation_detail") if assessment else None
        if rec_detail and isinstance(rec_detail, dict):
            rec_at_decision = rec_detail.get("recommendation") or assessment.recommendation
        else:
            rec_at_decision = assessment.recommendation if assessment else None

        # Override calculation
        is_override = False
        decision_val = decision_data.decision
        rec_str = str(rec_at_decision or "").upper()

        if decision_val == ProcurementDecisionValue.QUALIFIED:
            if rec_str in ("DO_NOT_RECOMMEND", "HIGH_RISK_REVIEW", "REVIEW_REQUIRED"):
                is_override = True
            elif "DO NOT PROCEED" in rec_str or "MANUAL REVIEW" in rec_str or "FURTHER COMPLIANCE REVIEW" in rec_str:
                is_override = True
        elif decision_val == ProcurementDecisionValue.DISQUALIFIED:
            if rec_str in ("PROCEED",) or "SATISFIES THE EVALUATED COMPLIANCE" in rec_str:
                is_override = True

        from sqlalchemy.exc import IntegrityError

        try:
            created_decision = procurement_decision_repository.create(
                db=db,
                bid_submission_id=bid_submission_id,
                decided_by=current_user.id,
                decision_data=decision_data,
                assessment_id=assessment_id,
                recommendation_at_decision=rec_at_decision,
                score_snapshot=score_snapshot,
                risk_snapshot=risk_snapshot,
                is_override=is_override,
                auto_commit=False,
            )

            # Audit trail integration (Task 5)
            from app.core.audit_actions import AuditAction, AuditEntityType
            from app.services.audit_log_service import audit_log_service

            audit_log_service.record_event(
                db=db,
                action=AuditAction.PROCUREMENT_DECISION_CREATED,
                entity_type=AuditEntityType.PROCUREMENT_DECISION,
                entity_id=created_decision.id,
                user_id=current_user.id,
                bid_submission_id=bid_submission_id,
                new_value={
                    "decision": created_decision.decision,
                    "reason": created_decision.reason,
                    "is_override": is_override,
                    "recommendation_at_decision": rec_at_decision,
                    "score_snapshot": score_snapshot,
                    "risk_snapshot": risk_snapshot,
                },
                details=(
                    f"Procurement Officer #{current_user.id} recorded final decision '{created_decision.decision}' "
                    f"for submission #{bid_submission_id} (Override: {is_override})"
                ),
                auto_commit=False,
            )

            db.commit()
            db.refresh(created_decision)
            return created_decision
        except IntegrityError:
            db.rollback()
            raise ValueError(
                f"A final procurement decision has already been recorded for bid submission #{bid_submission_id}."
            )
        except Exception:
            db.rollback()
            raise

    def get_decision(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> ProcurementDecision:
        submission = bid_submission_repository.get_by_id(db, bid_submission_id)
        if submission is None:
            raise ValueError(f"Bid submission not found: {bid_submission_id}")

        decision = procurement_decision_repository.get_by_submission_id(
            db, bid_submission_id
        )
        if decision is None:
            raise ValueError(
                f"No final procurement decision has been recorded for bid submission #{bid_submission_id}."
            )

        return decision


procurement_decision_service = ProcurementDecisionService()
