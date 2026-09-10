from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_role
from app.database.session import get_db
from app.repositories.bid_submission_repository import bid_submission_repository
from app.schemas.discrepancy import (
    DiscrepancyResponse,
    DiscrepancyUpdate,
)
from app.services.discrepancy_service import discrepancy_service

router = APIRouter(
    prefix="/bid-submissions",
    tags=["Discrepancies"],
    dependencies=[Depends(require_role("PROCUREMENT_OFFICER", "ADMIN"))],
)


@router.get(
    "/{submission_id}/discrepancies",
    response_model=list[DiscrepancyResponse],
)
def get_bid_submission_discrepancies(
    submission_id: int,
    db: Session = Depends(get_db),
):
    """Return all persisted discrepancies and missing evidence findings for a submission."""
    submission = bid_submission_repository.get_by_id(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid submission not found: {submission_id}",
        )

    return discrepancy_service.get_discrepancies_for_submission(db, submission_id)


@router.get(
    "/{submission_id}/discrepancies/open",
    response_model=list[DiscrepancyResponse],
)
def get_bid_submission_open_discrepancies(
    submission_id: int,
    db: Session = Depends(get_db),
):
    """Return all OPEN discrepancies for a submission."""
    submission = bid_submission_repository.get_by_id(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid submission not found: {submission_id}",
        )

    return discrepancy_service.get_open_discrepancies_for_submission(db, submission_id)


@router.get(
    "/{submission_id}/discrepancies/{discrepancy_id}",
    response_model=DiscrepancyResponse,
)
def get_discrepancy_by_id(
    submission_id: int,
    discrepancy_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific discrepancy finding by ID."""
    discrepancy = discrepancy_service.get_by_id(db, discrepancy_id)
    if not discrepancy or discrepancy.bid_submission_id != submission_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discrepancy #{discrepancy_id} not found for submission #{submission_id}",
        )

    return discrepancy


from app.api.dependencies import get_current_user, require_role
from app.models.user import User

@router.patch(
    "/{submission_id}/discrepancies/{discrepancy_id}",
    response_model=DiscrepancyResponse,
)
def update_discrepancy_status(
    submission_id: int,
    discrepancy_id: int,
    update_data: DiscrepancyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update discrepancy lifecycle status (e.g. OPEN -> RESOLVED / WAIVED) with officer resolution note.
    """
    discrepancy = discrepancy_service.get_by_id(db, discrepancy_id)
    if not discrepancy or discrepancy.bid_submission_id != submission_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discrepancy #{discrepancy_id} not found for submission #{submission_id}",
        )

    if not update_data.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'status' is required for discrepancy update.",
        )

    try:
        updated = discrepancy_service.update_discrepancy_status(
            db=db,
            discrepancy_id=discrepancy_id,
            status=update_data.status,
            resolution_note=update_data.resolution_note,
            user_id=current_user.id,
        )
        return updated
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
