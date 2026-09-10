from sqlalchemy.orm import Session

from app.models.bid_submission import BidSubmission
from app.schemas.bid_submission import BidSubmissionCreate


class BidSubmissionRepository:

    def create(
        self,
        db: Session,
        submission_data: BidSubmissionCreate,
        user_id: int | None = None,
    ) -> BidSubmission:

        submission = BidSubmission(
            **submission_data.model_dump()
        )

        db.add(submission)
        db.commit()
        db.refresh(submission)

        from app.core.audit_actions import AuditAction, AuditEntityType
        from app.services.audit_log_service import audit_log_service

        audit_log_service.record_event(
            db=db,
            action=AuditAction.BID_SUBMISSION_CREATED,
            entity_type=AuditEntityType.BID_SUBMISSION,
            entity_id=submission.id,
            bid_submission_id=submission.id,
            user_id=user_id,
            new_value={
                "tender_id": submission.tender_id,
                "bidder_id": submission.bidder_id,
            },
            details=f"Bid submission #{submission.id} created for tender #{submission.tender_id}",
        )

        return submission

    def get_by_id(
        self,
        db: Session,
        submission_id: int,
    ) -> BidSubmission | None:

        return (
            db.query(BidSubmission)
            .filter(
                BidSubmission.id == submission_id
            )
            .first()
        )

    def get_by_tender_id(
        self,
        db: Session,
        tender_id: int,
    ) -> list[BidSubmission]:

        return (
            db.query(BidSubmission)
            .filter(
                BidSubmission.tender_id == tender_id
            )
            .all()
        )

    def get_by_bidder_id(
        self,
        db: Session,
        bidder_id: int,
    ) -> list[BidSubmission]:

        return (
            db.query(BidSubmission)
            .filter(
                BidSubmission.bidder_id == bidder_id
            )
            .all()
        )


bid_submission_repository = BidSubmissionRepository()