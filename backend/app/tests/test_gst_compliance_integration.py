import uuid
from app.database.session import SessionLocal
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_submission import BidSubmission
from app.models.compliance_check import ComplianceCheck

from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
)

from app.services.compliance_service import (
    compliance_service,
)

from app.services.evaluators.gst_evaluator import (
    GSTEvaluator,
)

from app.services.evaluators.registry import (
    evaluator_registry,
)


def create_test_data(db):
    unique_id = uuid.uuid4().hex[:8].upper()

    bidder = Bidder(
        company_name=f"GST Integration Test Company {unique_id}",
        gstin="29ABCDE1234F1Z5",
        pan=f"F{unique_id[:4]}5678K",
        udyam_number=f"UDYAM-GST-{unique_id}",
    )

    tender = Tender(
        title=f"GST Integration Test Tender {unique_id}",
        reference_number=f"GST-INT-{unique_id}",
        description="Temporary tender for GST integration testing.",
        status="DRAFT",
    )

    db.add_all([bidder, tender])
    db.commit()

    db.refresh(bidder)
    db.refresh(tender)

    requirement = TenderRequirement(
        tender_id=tender.id,
        requirement_type="GST",
        requirement_name="GST Registration and Return Filing",
        description="GST registration and return filing compliance.",
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


def test_real_gst_evaluator_works_through_compliance_service():

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

        # Make sure the real GST evaluator is registered.
        if evaluator_registry.get("GST") is None:
            evaluator_registry.register(
                GSTEvaluator()
            )

        request = ComplianceEvaluationRequest(
            bid_submission_id=submission.id,
            tender_requirement_id=requirement.id,
            requirement_type="GST",
            requirement_name=(
                "GST Registration and Return Filing"
            ),
            extracted_data={
                "gstin": "29ABCDE1234F1Z5",
            },
            verification_data={
                "status": "VERIFIED",
                "gstin": "29ABCDE1234F1Z5",
                "return_filing_status": "COMPLIANT",
            },
        )

        check = compliance_service.evaluate_requirement(
            db,
            request,
        )

        assert isinstance(
            check,
            ComplianceCheck,
        )

        assert check.status == "PASS"

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

        assert (
            check.evidence["gstin"]
            == "29ABCDE1234F1Z5"
        )

        assert (
            check.evidence["verification_status"]
            == "VERIFIED"
        )

        assert (
            check.evidence["return_filing_status"]
            == "COMPLIANT"
        )

        registered_evaluator = (
            evaluator_registry.get("GST")
        )

        assert isinstance(
            registered_evaluator,
            GSTEvaluator,
        )

    finally:
        db.rollback()

        if check is not None:
            existing_check = db.query(
                ComplianceCheck
            ).filter(
                ComplianceCheck.id == check.id
            ).first()

            if existing_check:
                db.delete(existing_check)

        if submission is not None:
            existing_submission = db.query(
                BidSubmission
            ).filter(
                BidSubmission.id == submission.id
            ).first()

            if existing_submission:
                db.delete(existing_submission)

        if requirement is not None:
            existing_requirement = db.query(
                TenderRequirement
            ).filter(
                TenderRequirement.id == requirement.id
            ).first()

            if existing_requirement:
                db.delete(existing_requirement)

        if tender is not None:
            existing_tender = db.query(
                Tender
            ).filter(
                Tender.id == tender.id
            ).first()

            if existing_tender:
                db.delete(existing_tender)

        if bidder is not None:
            existing_bidder = db.query(
                Bidder
            ).filter(
                Bidder.id == bidder.id
            ).first()

            if existing_bidder:
                db.delete(existing_bidder)

        db.commit()
        db.close()