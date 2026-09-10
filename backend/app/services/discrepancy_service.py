from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from app.models.discrepancy import Discrepancy, DiscrepancyStatus
from app.repositories.discrepancy_repository import (
    discrepancy_repository,
    DiscrepancyRepository,
)
from app.schemas.discrepancy import (
    DiscrepancyCreate,
    DiscrepancyUpdate,
)


class DiscrepancyService:
    """
    Domain service for managing structured discrepancy findings and missing evidence records.

    Ensures idempotency (no endless duplicate creation), lifecycle status transitions,
    and structured evidence retrieval.
    """

    def __init__(self, repo: DiscrepancyRepository = discrepancy_repository):
        self.repo = repo

    def record_discrepancy(
        self,
        db: Session,
        bid_submission_id: int,
        type: str,
        title: str,
        description: str,
        severity: str = "MEDIUM",
        source: str = "CROSS_VERIFICATION",
        tender_requirement_id: int | None = None,
        bid_document_id: int | None = None,
        verification_result_id: int | None = None,
        compliance_check_id: int | None = None,
        expected_value: str | None = None,
        observed_value: str | None = None,
        evidence: dict[str, Any] | None = None,
        finding_key: str | None = None,
    ) -> Discrepancy:
        """
        Records a structured discrepancy finding while checking for existing open records
        to enforce idempotency and avoid duplicate entries on rerun.
        """
        # Build stable finding key if not provided
        if not finding_key:
            req_part = f"req_{tender_requirement_id}" if tender_requirement_id else "noreq"
            doc_part = f"doc_{bid_document_id}" if bid_document_id else "nodoc"
            ver_part = f"ver_{verification_result_id}" if verification_result_id else "nover"
            finding_key = f"sub_{bid_submission_id}:{type}:{source}:{req_part}:{doc_part}:{ver_part}"

        existing = self.repo.find_existing(
            db=db,
            bid_submission_id=bid_submission_id,
            finding_key=finding_key,
            discrepancy_type=type,
            tender_requirement_id=tender_requirement_id,
            bid_document_id=bid_document_id,
            verification_result_id=verification_result_id,
        )

        if existing:
            update_data = DiscrepancyUpdate(
                title=title,
                description=description,
                severity=severity,
            )
            # Update existing fields directly if modified
            existing.title = title
            existing.description = description
            existing.severity = severity
            existing.expected_value = expected_value
            existing.observed_value = observed_value
            existing.evidence = evidence
            if compliance_check_id:
                existing.compliance_check_id = compliance_check_id

            return self.repo.update(db, db_obj=existing, obj_in=update_data)

        create_data = DiscrepancyCreate(
            bid_submission_id=bid_submission_id,
            tender_requirement_id=tender_requirement_id,
            bid_document_id=bid_document_id,
            verification_result_id=verification_result_id,
            compliance_check_id=compliance_check_id,
            type=type,
            severity=severity,
            status=DiscrepancyStatus.OPEN.value,
            title=title,
            description=description,
            expected_value=expected_value,
            observed_value=observed_value,
            source=source,
            evidence=evidence,
            finding_key=finding_key,
        )

        new_disc = self.repo.create(db, create_data)

        from app.core.audit_actions import AuditAction, AuditEntityType
        from app.services.audit_log_service import audit_log_service

        audit_log_service.record_event(
            db=db,
            action=AuditAction.DISCREPANCY_CREATED,
            entity_type=AuditEntityType.DISCREPANCY,
            entity_id=new_disc.id,
            bid_submission_id=bid_submission_id,
            new_value={
                "title": new_disc.title,
                "type": new_disc.type,
                "severity": new_disc.severity,
                "status": new_disc.status,
            },
            details=f"Discrepancy #{new_disc.id} '{title}' created",
        )

        return new_disc

    def get_by_id(self, db: Session, discrepancy_id: int) -> Discrepancy | None:
        return self.repo.get_by_id(db, discrepancy_id)

    def get_discrepancies_for_submission(
        self, db: Session, bid_submission_id: int
    ) -> list[Discrepancy]:
        return self.repo.get_by_submission_id(db, bid_submission_id)

    def get_open_discrepancies_for_submission(
        self, db: Session, bid_submission_id: int
    ) -> list[Discrepancy]:
        return self.repo.get_open_by_submission_id(db, bid_submission_id)

    def get_discrepancies_for_requirement(
        self, db: Session, tender_requirement_id: int
    ) -> list[Discrepancy]:
        return self.repo.get_by_requirement_id(db, tender_requirement_id)

    def update_discrepancy_status(
        self,
        db: Session,
        discrepancy_id: int,
        status: str,
        resolution_note: str | None = None,
        user_id: int | None = None,
    ) -> Discrepancy:
        discrepancy = self.repo.get_by_id(db, discrepancy_id)
        if not discrepancy:
            raise ValueError(f"Discrepancy not found: {discrepancy_id}")

        valid_statuses = [
            DiscrepancyStatus.OPEN.value,
            DiscrepancyStatus.RESOLVED.value,
            DiscrepancyStatus.WAIVED.value,
        ]

        normalized_status = status.upper()
        if normalized_status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
            )

        # Enforce controlled status transitions
        if discrepancy.status in (
            DiscrepancyStatus.RESOLVED.value,
            DiscrepancyStatus.WAIVED.value,
        ) and normalized_status == discrepancy.status:
            return discrepancy

        old_status = discrepancy.status

        resolved_at = (
            datetime.now(timezone.utc)
            if normalized_status in (DiscrepancyStatus.RESOLVED.value, DiscrepancyStatus.WAIVED.value)
            else None
        )

        update_data = DiscrepancyUpdate(
            status=normalized_status,
            resolution_note=resolution_note,
            resolved_at=resolved_at,
        )

        updated_disc = self.repo.update(db, db_obj=discrepancy, obj_in=update_data)

        from app.core.audit_actions import AuditAction, AuditEntityType
        from app.services.audit_log_service import audit_log_service

        action = (
            AuditAction.DISCREPANCY_RESOLVED
            if normalized_status == DiscrepancyStatus.RESOLVED.value
            else (
                AuditAction.DISCREPANCY_WAIVED
                if normalized_status == DiscrepancyStatus.WAIVED.value
                else AuditAction.DISCREPANCY_CREATED
            )
        )

        audit_log_service.record_event(
            db=db,
            action=action,
            entity_type=AuditEntityType.DISCREPANCY,
            entity_id=updated_disc.id,
            bid_submission_id=updated_disc.bid_submission_id,
            user_id=user_id,
            old_value={"status": old_status},
            new_value={"status": normalized_status, "resolution_note": resolution_note},
            details=f"Discrepancy #{updated_disc.id} status changed from {old_status} to {normalized_status}",
        )

        return updated_disc


discrepancy_service = DiscrepancyService()
