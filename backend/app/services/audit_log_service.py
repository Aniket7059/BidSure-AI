import logging
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session

from app.core.audit_actions import AuditAction, AuditEntityType
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogCreate

logger = logging.getLogger(__name__)

# Keys that must NEVER be stored in audit logs
SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "credentials",
    "document_content",
    "file_bytes",
    "binary_data",
    "raw_text",
    "auth_header",
    "jwt",
    "private_key",
}


def sanitize_audit_data(data: Any) -> Any:
    """
    Recursively scrubs sensitive keys (passwords, tokens, raw file bytes) from dicts.
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, val in data.items():
            if str(key).lower() in SENSITIVE_KEYS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_audit_data(val)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_audit_data(item) for item in data]
    return data


class AuditLogService:
    """
    Centralized service for recording and retrieving audit trail records.
    Ensures data sanitization, transaction safety, and append-only immutability.
    """

    def __init__(self, repository: AuditLogRepository | None = None):
        self.repository = repository or AuditLogRepository()

    def record_event(
        self,
        db: Session,
        action: str | AuditAction,
        entity_type: str | AuditEntityType,
        entity_id: int | None = None,
        user_id: int | None = None,
        bid_submission_id: int | None = None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        details: str | dict[str, Any] | None = None,
        ip_address: str | None = None,
        auto_commit: bool = True,
    ) -> AuditLog:
        """
        Record a structured audit event in the database.
        """
        sanitized_old = sanitize_audit_data(old_value) if old_value else None
        sanitized_new = sanitize_audit_data(new_value) if new_value else None
        sanitized_details = sanitize_audit_data(details) if isinstance(details, dict) else details

        action_str = str(action)
        entity_type_str = str(entity_type)

        audit_in = AuditLogCreate(
            action=action_str,
            entity_type=entity_type_str,
            entity_id=entity_id,
            user_id=user_id,
            bid_submission_id=bid_submission_id,
            old_value=sanitized_old,
            new_value=sanitized_new,
            details=sanitized_details,
            ip_address=ip_address,
        )

        try:
            return self.repository.create(db, audit_in, auto_commit=auto_commit)
        except Exception as exc:
            logger.error("Failed to record audit event %s: %s", action_str, exc)
            raise

    def get_by_id(self, db: Session, audit_id: int) -> AuditLog | None:
        return self.repository.get_by_id(db, audit_id)

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
        return self.repository.list_logs(
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

    def list_by_bid_submission(
        self,
        db: Session,
        bid_submission_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        return self.repository.list_by_bid_submission(
            db=db,
            bid_submission_id=bid_submission_id,
            limit=limit,
            offset=offset,
        )

    def list_by_entity(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        return self.repository.list_by_entity(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )


audit_log_service = AuditLogService()
