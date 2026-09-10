from datetime import datetime, timezone
import json
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate


class AuditLogRepository:
    """
    Repository handling database operations for AuditLog records.
    Audit log operations are append-only and read-only.
    """

    def create(self, db: Session, obj_in: AuditLogCreate, auto_commit: bool = True) -> AuditLog:
        # Serialize details if dictionary
        details_str = (
            json.dumps(obj_in.details)
            if isinstance(obj_in.details, dict)
            else obj_in.details
        )

        db_obj = AuditLog(
            user_id=obj_in.user_id,
            bid_submission_id=obj_in.bid_submission_id,
            action=obj_in.action,
            entity_type=obj_in.entity_type,
            entity_id=obj_in.entity_id,
            old_value=obj_in.old_value,
            new_value=obj_in.new_value,
            details=details_str,
            ip_address=obj_in.ip_address,
            created_at=datetime.now(timezone.utc),
        )
        if not hasattr(db, "add"):
            return db_obj

        db.add(db_obj)
        if auto_commit:
            db.commit()
            db.refresh(db_obj)
        else:
            db.flush()
        return db_obj

    def get_by_id(self, db: Session, audit_id: int) -> AuditLog | None:
        stmt = select(AuditLog).where(AuditLog.id == audit_id)
        return db.scalars(stmt).first()

    def list_logs(
        self,
        db: Session,
        entity_type: str | None = None,
        entity_id: int | None = None,
        bid_submission_id: int | None = None,
        user_id: int | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        stmt = select(AuditLog)

        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        if bid_submission_id is not None:
            # Match bid_submission_id column OR entity_type='BID_SUBMISSION' & entity_id=bid_submission_id
            stmt = stmt.where(
                or_(
                    AuditLog.bid_submission_id == bid_submission_id,
                    (AuditLog.entity_type == "BID_SUBMISSION") & (AuditLog.entity_id == bid_submission_id)
                )
            )
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)

        # Count query
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        # Paginated results (newest first)
        results_stmt = stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset(offset).limit(limit)
        items = list(db.scalars(results_stmt).all())

        return items, total

    def list_by_entity(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        return self.list_logs(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )

    def list_by_bid_submission(
        self,
        db: Session,
        bid_submission_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        return self.list_logs(
            db=db,
            bid_submission_id=bid_submission_id,
            limit=limit,
            offset=offset,
        )

    def list_by_user(
        self,
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        return self.list_logs(
            db=db,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    def list_recent(
        self,
        db: Session,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        return self.list_logs(
            db=db,
            limit=limit,
            offset=offset,
        )


audit_log_repository = AuditLogRepository()
