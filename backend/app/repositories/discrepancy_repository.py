from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discrepancy import Discrepancy
from app.schemas.discrepancy import DiscrepancyCreate, DiscrepancyUpdate


class DiscrepancyRepository:
    """
    Repository handling database operations for Discrepancy records.
    """

    def create(self, db: Session, obj_in: DiscrepancyCreate) -> Discrepancy:
        db_obj = Discrepancy(
            bid_submission_id=obj_in.bid_submission_id,
            tender_requirement_id=obj_in.tender_requirement_id,
            bid_document_id=obj_in.bid_document_id,
            verification_result_id=obj_in.verification_result_id,
            compliance_check_id=obj_in.compliance_check_id,
            type=obj_in.type,
            severity=obj_in.severity,
            status=obj_in.status,
            title=obj_in.title,
            description=obj_in.description,
            expected_value=obj_in.expected_value,
            observed_value=obj_in.observed_value,
            source=obj_in.source,
            evidence=obj_in.evidence,
            finding_key=obj_in.finding_key,
            detected_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_id(self, db: Session, discrepancy_id: int) -> Discrepancy | None:
        stmt = select(Discrepancy).where(Discrepancy.id == discrepancy_id)
        return db.scalars(stmt).first()

    def get_by_submission_id(
        self, db: Session, bid_submission_id: int
    ) -> list[Discrepancy]:
        stmt = (
            select(Discrepancy)
            .where(Discrepancy.bid_submission_id == bid_submission_id)
            .order_by(Discrepancy.id.asc())
        )
        return list(db.scalars(stmt).all())

    def get_open_by_submission_id(
        self, db: Session, bid_submission_id: int
    ) -> list[Discrepancy]:
        stmt = (
            select(Discrepancy)
            .where(
                Discrepancy.bid_submission_id == bid_submission_id,
                Discrepancy.status == "OPEN",
            )
            .order_by(Discrepancy.id.asc())
        )
        return list(db.scalars(stmt).all())

    def get_by_requirement_id(
        self, db: Session, tender_requirement_id: int
    ) -> list[Discrepancy]:
        stmt = (
            select(Discrepancy)
            .where(Discrepancy.tender_requirement_id == tender_requirement_id)
            .order_by(Discrepancy.id.asc())
        )
        return list(db.scalars(stmt).all())

    def find_existing(
        self,
        db: Session,
        bid_submission_id: int,
        finding_key: str | None = None,
        discrepancy_type: str | None = None,
        tender_requirement_id: int | None = None,
        bid_document_id: int | None = None,
        verification_result_id: int | None = None,
    ) -> Discrepancy | None:
        """
        Locates an existing OPEN discrepancy matching stable identifying keys to prevent duplicates.
        """
        stmt = select(Discrepancy).where(
            Discrepancy.bid_submission_id == bid_submission_id,
            Discrepancy.status == "OPEN",
        )

        if finding_key:
            stmt = stmt.where(Discrepancy.finding_key == finding_key)
        else:
            if discrepancy_type:
                stmt = stmt.where(Discrepancy.type == discrepancy_type)
            if tender_requirement_id:
                stmt = stmt.where(
                    Discrepancy.tender_requirement_id == tender_requirement_id
                )
            if bid_document_id:
                stmt = stmt.where(Discrepancy.bid_document_id == bid_document_id)
            if verification_result_id:
                stmt = stmt.where(
                    Discrepancy.verification_result_id == verification_result_id
                )

        return db.scalars(stmt).first()

    def update(
        self,
        db: Session,
        db_obj: Discrepancy,
        obj_in: DiscrepancyUpdate,
    ) -> Discrepancy:
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


discrepancy_repository = DiscrepancyRepository()
