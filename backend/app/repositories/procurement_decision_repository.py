from sqlalchemy.orm import Session

from app.models.procurement_decision import ProcurementDecision
from app.schemas.procurement_decision import ProcurementDecisionCreate


class ProcurementDecisionRepository:
    """
    Repository pattern for managing ProcurementDecision database records.
    """

    def get_by_id(self, db: Session, decision_id: int) -> ProcurementDecision | None:
        return (
            db.query(ProcurementDecision)
            .filter(ProcurementDecision.id == decision_id)
            .first()
        )

    def get_by_submission_id(
        self, db: Session, bid_submission_id: int
    ) -> ProcurementDecision | None:
        return (
            db.query(ProcurementDecision)
            .filter(ProcurementDecision.bid_submission_id == bid_submission_id)
            .first()
        )

    def create(
        self,
        db: Session,
        bid_submission_id: int,
        decided_by: int,
        decision_data: ProcurementDecisionCreate,
        assessment_id: int | None = None,
        recommendation_at_decision: str | None = None,
        score_snapshot: float | None = None,
        risk_snapshot: str | None = None,
        is_override: bool = False,
        auto_commit: bool = True,
    ) -> ProcurementDecision:
        db_obj = ProcurementDecision(
            bid_submission_id=bid_submission_id,
            decision=decision_data.decision.value,
            reason=decision_data.reason,
            decided_by=decided_by,
            assessment_id=assessment_id,
            recommendation_at_decision=recommendation_at_decision,
            score_snapshot=score_snapshot,
            risk_snapshot=risk_snapshot,
            is_override=is_override,
        )
        db.add(db_obj)
        if auto_commit:
            db.commit()
            db.refresh(db_obj)
        else:
            db.flush()
        return db_obj


procurement_decision_repository = ProcurementDecisionRepository()

