from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.bidder_repository import bidder_repository
from app.schemas.bidder import BidderCreate, BidderResponse


from app.api.dependencies import require_role

router = APIRouter(
    prefix="/bidders",
    tags=["Bidders"],
    dependencies=[Depends(require_role("PROCUREMENT_OFFICER", "ADMIN"))],
)


@router.post(
    "",
    response_model=BidderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bidder(
    bidder_data: BidderCreate,
    db: Session = Depends(get_db),
):
    existing_bidder = None

    if bidder_data.gstin:
        existing_bidder = bidder_repository.get_by_gstin(
            db,
            bidder_data.gstin,
        )

    if existing_bidder:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A bidder with this GSTIN already exists.",
        )

    return bidder_repository.create(
        db,
        bidder_data,
    )


@router.get(
    "",
    response_model=list[BidderResponse],
)
def get_all_bidders(
    db: Session = Depends(get_db),
):
    return bidder_repository.get_all(db)


@router.get(
    "/{bidder_id}",
    response_model=BidderResponse,
)
def get_bidder(
    bidder_id: int,
    db: Session = Depends(get_db),
):
    bidder = bidder_repository.get_by_id(
        db,
        bidder_id,
    )

    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bidder not found.",
        )

    return bidder