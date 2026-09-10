import uuid
import pytest

from app.database.session import SessionLocal

from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_submission import BidSubmission
from app.models.compliance_check import ComplianceCheck

from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)

from app.services.compliance_service import (
    compliance_service,
)

from app.services.evaluators.base import (
    RequirementEvaluator,
)

from app.services.evaluators.registry import (
    evaluator_registry,
)


class FakeEvaluator(RequirementEvaluator):
    """
    Test-only evaluator used to verify that the
    ComplianceService correctly uses the evaluator registry.
    """

    @property
    def requirement_type(self) -> str:
        return "OTHER"

    def evaluate(
        self,
        request: ComplianceEvaluationRequest,
    ) -> ComplianceEvaluationResult:

        return ComplianceEvaluationResult(
            status="PASS",
            reason="Fake evaluator passed.",
            evidence={
                "source": "fake_evaluator",
            },
        )


def create_test_data(db):
    """
    Create isolated test data with unique values so
    repeated pytest runs cannot violate unique constraints.
    """

    unique_id = uuid.uuid4().hex[:8].upper()

    bidder = Bidder(
        company_name=f"Test Company {unique_id}",
        gstin=f"29{unique_id}1234A1Z5",
        pan=f"ABC{unique_id[:7]}F",
        udyam_number=f"UDYAM-TEST-{unique_id}",
    )

    tender = Tender(
        title=f"Test Tender {unique_id}",
        reference_number=f"TEST-REF-{unique_id}",
        description="Temporary tender for service testing.",
        status="DRAFT",
    )

    db.add_all([bidder, tender])
    db.commit()

    db.refresh(bidder)
    db.refresh(tender)

    requirement = TenderRequirement(
        tender_id=tender.id,
        requirement_type="OTHER",
        requirement_name="Test Requirement",
        description="Temporary requirement for testing.",
        is_required=True,
    )

    submission = BidSubmission(
        tender_id=tender.id,
        bidder_id=bidder.id,
        status="SUBMITTED",
    )

    db.add_all([requirement, submission])
    db.commit()

    db.refresh(requirement)
    db.refresh(submission)

    return bidder, tender, requirement, submission

def cleanup_test_data(
    db,
    bidder,
    tender,
    requirement,
    submission,
    check=None,
):
    try:
        db.rollback()

        if check is not None:
            db.delete(check)

        if submission is not None:
            db.delete(submission)

        if requirement is not None:
            db.delete(requirement)

        if tender is not None:
            db.delete(tender)

        if bidder is not None:
            db.delete(bidder)

        db.commit()

    except Exception:
        db.rollback()
        raise

def test_missing_requirement_returns_error():

    db = SessionLocal()

    bidder = None
    tender = None
    requirement = None
    submission = None

    try:
        (
            bidder,
            tender,
            requirement,
            submission,
        ) = create_test_data(db)

        request = ComplianceEvaluationRequest(
            bid_submission_id=submission.id,
            tender_requirement_id=999999,
            requirement_type="OTHER",
            requirement_name="Test Requirement",
        )

        with pytest.raises(
            ValueError,
            match="Tender requirement not found",
        ):
            compliance_service.evaluate_requirement(
                db,
                request,
            )

    finally:
        cleanup_test_data(
            db,
            bidder,
            tender,
            requirement,
            submission,
        )

        db.close()


def test_unsupported_requirement_creates_review():

    db = SessionLocal()

    bidder = None
    tender = None
    requirement = None
    submission = None
    check = None

    try:
        (
            bidder,
            tender,
            requirement,
            submission,
        ) = create_test_data(db)

        requirement.requirement_type = (
            "DIGILOCKER"
        )

        db.commit()
        db.refresh(requirement)

        request = ComplianceEvaluationRequest(
            bid_submission_id=submission.id,
            tender_requirement_id=requirement.id,
            requirement_type=requirement.requirement_type,
            requirement_name=requirement.requirement_name,
        )

        check = (
            compliance_service.evaluate_requirement(
                db,
                request,
            )
        )

        assert isinstance(
            check,
            ComplianceCheck,
        )

        assert check.status == "REVIEW"

        assert (
            "No automated evaluator"
            in check.reason
        )

        assert (
            check.tender_requirement_id
            == requirement.id
        )

        assert (
            check.bid_submission_id
            == submission.id
        )

        assert check.checked_by == "COMPLIANCE_ENGINE"

        assert check.checked_at is not None

    finally:
        cleanup_test_data(
            db,
            bidder,
            tender,
            requirement,
            submission,
            check,
        )

        db.close()


def test_registered_evaluator_is_used():

    db = SessionLocal()

    bidder = None
    tender = None
    requirement = None
    submission = None
    check = None

    try:
        (
            bidder,
            tender,
            requirement,
            submission,
        ) = create_test_data(db)

        evaluator = FakeEvaluator()

        evaluator_registry.register(
            evaluator
        )

        request = ComplianceEvaluationRequest(
            bid_submission_id=submission.id,
            tender_requirement_id=requirement.id,
            requirement_type=requirement.requirement_type,
            requirement_name=requirement.requirement_name,
            extracted_data={
                "field": "value"
            },
        )

        check = (
            compliance_service.evaluate_requirement(
                db,
                request,
            )
        )

        assert isinstance(
            check,
            ComplianceCheck,
        )

        assert check.status == "PASS"

        assert (
            check.reason
            == "Fake evaluator passed."
        )

        assert (
            check.evidence["source"]
            == "fake_evaluator"
        )

        assert (
            check.bid_submission_id
            == submission.id
        )

        assert (
            check.tender_requirement_id
            == requirement.id
        )

        assert check.checked_by == "COMPLIANCE_ENGINE"

        assert check.checked_at is not None

    finally:
        cleanup_test_data(
            db,
            bidder,
            tender,
            requirement,
            submission,
            check,
        )

        db.close()

def test_missing_bid_submission_returns_error():

    db = SessionLocal()

    bidder = None
    tender = None
    requirement = None
    submission = None

    try:
        (
            bidder,
            tender,
            requirement,
            submission,
        ) = create_test_data(db)

        request = ComplianceEvaluationRequest(
            bid_submission_id=999999,
            tender_requirement_id=requirement.id,
            requirement_type=requirement.requirement_type,
            requirement_name=requirement.requirement_name,
        )

        with pytest.raises(
            ValueError,
            match="Bid submission not found",
        ):
            compliance_service.evaluate_requirement(
                db,
                request,
            )

    finally:
        cleanup_test_data(
            db,
            bidder,
            tender,
            requirement,
            submission,
        )

        db.close()


def test_requirement_must_belong_to_submission_tender():

    db = SessionLocal()

    bidder = None
    tender = None
    requirement = None
    submission = None

    other_tender = None
    other_requirement = None

    try:
        (
            bidder,
            tender,
            requirement,
            submission,
        ) = create_test_data(db)

        unique_id = uuid.uuid4().hex[:8].upper()

        other_tender = Tender(
            title=f"Other Tender {unique_id}",
            reference_number=f"OTHER-REF-{unique_id}",
            description="Temporary second tender.",
            status="DRAFT",
        )

        db.add(other_tender)
        db.commit()
        db.refresh(other_tender)

        other_requirement = TenderRequirement(
            tender_id=other_tender.id,
            requirement_type="OTHER",
            requirement_name="Other Requirement",
            description="Requirement from another tender.",
            is_required=True,
        )

        db.add(other_requirement)
        db.commit()
        db.refresh(other_requirement)

        request = ComplianceEvaluationRequest(
            bid_submission_id=submission.id,
            tender_requirement_id=other_requirement.id,
            requirement_type="OTHER",
            requirement_name="Other Requirement",
        )

        with pytest.raises(
            ValueError,
            match="does not belong to the bid submission",
        ):
            compliance_service.evaluate_requirement(
                db,
                request,
            )

    finally:
        if other_requirement is not None:
            db.delete(other_requirement)

        if other_tender is not None:
            db.delete(other_tender)

        db.commit()

        cleanup_test_data(
            db,
            bidder,
            tender,
            requirement,
            submission,
        )

        db.close()