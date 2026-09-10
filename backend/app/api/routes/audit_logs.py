from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_role
from app.database.session import get_db
from app.repositories.bid_submission_repository import bid_submission_repository
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse
from app.services.audit_log_service import audit_log_service

router = APIRouter(
    tags=["Audit Logs"],
    dependencies=[Depends(require_role("PROCUREMENT_OFFICER", "ADMIN"))],
)


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
)
def list_audit_logs(
    entity_type: str | None = None,
    entity_id: int | None = None,
    bid_submission_id: int | None = None,
    user_id: int | None = None,
    action: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Retrieve paginated audit logs with optional filtering by entity, action, user, or date range.
    """
    items, total = audit_log_service.list_logs(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        bid_submission_id=bid_submission_id,
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/audit-logs/{audit_id}",
    response_model=AuditLogResponse,
)
def get_audit_log_by_id(
    audit_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a single audit log entry by ID."""
    log_entry = audit_log_service.get_by_id(db, audit_id)
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log entry #{audit_id} not found",
        )
    return log_entry


@router.get(
    "/bid-submissions/{submission_id}/audit-logs",
    response_model=AuditLogListResponse,
)
def get_bid_submission_audit_trail(
    submission_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve complete chronological audit trail for a specific bid submission."""
    submission = bid_submission_repository.get_by_id(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid submission not found: {submission_id}",
        )

    items, total = audit_log_service.list_by_bid_submission(
        db=db,
        bid_submission_id=submission_id,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/audit-logs/entity/{entity_type}/{entity_id}",
    response_model=AuditLogListResponse,
)
def get_entity_audit_trail(
    entity_type: str,
    entity_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve audit trail for a specific entity type and ID."""
    items, total = audit_log_service.list_by_entity(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
