from sqlalchemy.orm import Session

from app.models.compliance_check import ComplianceCheck
from app.schemas.compliance_check import (
    ComplianceCheckCreate,
    ComplianceCheckUpdate,
)


class ComplianceCheckRepository:

    def create(
        self,
        db: Session,
        check_data: ComplianceCheckCreate,
    ) -> ComplianceCheck:

        compliance_check = ComplianceCheck(
            **check_data.model_dump()
        )

        db.add(compliance_check)
        db.commit()
        db.refresh(compliance_check)

        return compliance_check

    def get_by_id(
        self,
        db: Session,
        check_id: int,
    ) -> ComplianceCheck | None:

        return (
            db.query(ComplianceCheck)
            .filter(ComplianceCheck.id == check_id)
            .first()
        )

    def get_by_submission(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> list[ComplianceCheck]:

        return (
            db.query(ComplianceCheck)
            .filter(
                ComplianceCheck.bid_submission_id
                == bid_submission_id
            )
            .order_by(ComplianceCheck.id)
            .all()
        )

    def get_by_requirement(
        self,
        db: Session,
        tender_requirement_id: int,
    ) -> list[ComplianceCheck]:

        return (
            db.query(ComplianceCheck)
            .filter(
                ComplianceCheck.tender_requirement_id
                == tender_requirement_id
            )
            .order_by(ComplianceCheck.id)
            .all()
        )

    def get_by_submission_and_requirement(
        self,
        db: Session,
        bid_submission_id: int,
        tender_requirement_id: int,
    ) -> ComplianceCheck | None:

        return (
            db.query(ComplianceCheck)
            .filter(
                ComplianceCheck.bid_submission_id == bid_submission_id,
                ComplianceCheck.tender_requirement_id == tender_requirement_id,
            )
            .first()
        )

    def update(
        self,
        db: Session,
        compliance_check: ComplianceCheck,
        check_data: ComplianceCheckUpdate,
    ) -> ComplianceCheck:

        update_data = check_data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(compliance_check, field, value)

        db.commit()
        db.refresh(compliance_check)

        return compliance_check


compliance_check_repository = ComplianceCheckRepository()