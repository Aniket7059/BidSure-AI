from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.bid_submission_repository import (
    bid_submission_repository,
)
from app.repositories.bidder_repository import bidder_repository
from app.repositories.tender_repository import tender_repository
from app.schemas.bid_submission import (
    BidSubmissionCreate,
    BidSubmissionResponse,
)


from app.api.dependencies import require_role

router = APIRouter(
    prefix="/bid-submissions",
    tags=["Bid Submissions"],
    dependencies=[Depends(require_role("PROCUREMENT_OFFICER", "ADMIN"))],
)


@router.post(
    "",
    response_model=BidSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bid_submission(
    submission_data: BidSubmissionCreate,
    db: Session = Depends(get_db),
):
    tender = tender_repository.get_by_id(
        db,
        submission_data.tender_id,
    )

    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found.",
        )

    bidder = bidder_repository.get_by_id(
        db,
        submission_data.bidder_id,
    )

    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bidder not found.",
        )

    try:
        return bid_submission_repository.create(
            db,
            submission_data,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This bidder already has a submission "
                "for this tender."
            ),
        )


@router.get(
    "/{submission_id}",
    response_model=BidSubmissionResponse,
)
def get_bid_submission(
    submission_id: int,
    db: Session = Depends(get_db),
):
    submission = bid_submission_repository.get_by_id(
        db,
        submission_id,
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid submission not found.",
        )

    return submission


from app.schemas.end_to_end_verification import EndToEndVerificationSummary
from app.services.end_to_end_verification_service import (
    end_to_end_verification_service,
)


@router.post(
    "/{submission_id}/verify",
    response_model=EndToEndVerificationSummary,
    status_code=status.HTTP_200_OK,
)
def verify_bid_submission(
    submission_id: int,
    db: Session = Depends(get_db),
):
    try:
        return end_to_end_verification_service.verify_bid_submission(
            db,
            submission_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


from app.api.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.procurement_decision import (
    ProcurementDecisionCreate,
    ProcurementDecisionResponse,
)
from app.services.procurement_decision_service import (
    procurement_decision_service,
)


@router.post(
    "/{submission_id}/decision",
    response_model=ProcurementDecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_procurement_decision(
    submission_id: int,
    decision_data: ProcurementDecisionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return procurement_decision_service.record_decision(
            db=db,
            current_user=current_user,
            bid_submission_id=submission_id,
            decision_data=decision_data,
        )
    except ValueError as exc:
        err_msg = str(exc)
        if "already been recorded" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=err_msg,
            )
        if "not found" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg,
        )


@router.get(
    "/{submission_id}/decision",
    response_model=ProcurementDecisionResponse,
    status_code=status.HTTP_200_OK,
)
def get_procurement_decision(
    submission_id: int,
    db: Session = Depends(get_db),
):
    try:
        return procurement_decision_service.get_decision(
            db=db,
            bid_submission_id=submission_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )