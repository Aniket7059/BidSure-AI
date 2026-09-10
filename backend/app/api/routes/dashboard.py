from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_role
from app.database.session import get_db
from app.schemas.dashboard import (
    BidEvaluationDashboardResponse,
    TenderDashboardResponse,
)
from app.services.dashboard_service import dashboard_service

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(require_role("PROCUREMENT_OFFICER", "ADMIN"))],
)


@router.get(
    "/bid-submissions/{bid_submission_id}",
    response_model=BidEvaluationDashboardResponse,
    status_code=status.HTTP_200_OK,
)
def get_bid_submission_dashboard(
    bid_submission_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns the comprehensive, read-only Procurement Officer Dashboard view
    for a single bid submission.

    Aggregates Tender, Requirements, Bidder, Documents, Verification Results,
    Discrepancies, Compliance Assessment, AI Recommendation, Procurement Officer Final Decision,
    and Audit Trail events in a single optimized payload.
    """
    try:
        return dashboard_service.get_bid_submission_dashboard(
            db,
            bid_submission_id,
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


@router.get(
    "/tenders/{tender_id}",
    response_model=TenderDashboardResponse,
    status_code=status.HTTP_200_OK,
)
def get_tender_dashboard(
    tender_id: int,
    status_filter: str | None = Query(None, description="Optional status filter"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """
    Returns the tender-level overview dashboard, summarizing bid submission counts,
    compliance distribution, risk distribution, decision counts, and a paginated list of bids.
    """
    try:
        return dashboard_service.get_tender_dashboard(
            db,
            tender_id,
            status_filter=status_filter,
            limit=limit,
            offset=offset,
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
