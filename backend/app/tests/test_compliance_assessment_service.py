import uuid

from app.database.session import SessionLocal
from app.database.session import SessionLocal

from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_submission import BidSubmission
from app.models.compliance_check import ComplianceCheck

from app.services.compliance_assessment_service import (
    compliance_assessment_service,
)


def create_test_data(db, check_statuses=None):
    """
    Create an isolated bidder, tender, requirements,
    bid submission, and optional compliance checks.
    """

    unique_id = uuid.uuid4().hex[:8].upper()

    bidder = Bidder(
        company_name=f"Assessment Test Company {unique_id}",
        gstin=f"29ASSESS{unique_id[:4]}A1Z5",
        pan=f"FGHIJ{unique_id[:4]}",
        udyam_number=f"UDYAM-ASSESS-{unique_id}",
    )

    tender = Tender(
        title=f"Assessment Test Tender {unique_id}",
        reference_number=f"ASSESS-REF-{unique_id}",
        description="Temporary tender for assessment testing.",
        status="DRAFT",
    )

    db.add_all([bidder, tender])
    db.commit()

    db.refresh(bidder)
    db.refresh(tender)

    submission = BidSubmission(
        tender_id=tender.id,
        bidder_id=bidder.id,
        status="SUBMITTED",
    )

    db.add(submission)
    db.commit()

    db.refresh(submission)

    checks = []

    if check_statuses:
        for index, status in enumerate(check_statuses, start=1):

            requirement = TenderRequirement(
                tender_id=tender.id,
                requirement_type="TEST",
                requirement_name=f"Test Requirement {index}",
                description="Temporary requirement.",
                is_required=True,
            )

            db.add(requirement)
            db.commit()
            db.refresh(requirement)

            check = ComplianceCheck(
                bid_submission_id=submission.id,
                tender_requirement_id=requirement.id,
                status=status,
                reason=f"Test result: {status}",
                evidence={
                    "source": "assessment_test",
                },
                checked_by="TEST",
            )

            db.add(check)
            db.commit()
            db.refresh(check)

            checks.append(check)

    return bidder, tender, submission, checks

def cleanup_test_data(
    db,
    bidder,
    tender,
    submission,
):
    """
    Remove all data created for a test.
    """

    db.query(ComplianceCheck).filter(
        ComplianceCheck.bid_submission_id
        == submission.id
    ).delete(
        synchronize_session=False
    )

    db.query(TenderRequirement).filter(
        TenderRequirement.tender_id
        == tender.id
    ).delete(
        synchronize_session=False
    )

    db.delete(submission)
    db.delete(tender)
    db.delete(bidder)

    db.commit()


def test_no_compliance_checks_returns_pending():

    db = SessionLocal()

    bidder = None
    tender = None
    submission = None

    try:

        (
            bidder,
            tender,
            submission,
            _,
        ) = create_test_data(db)

        assessment = (
            compliance_assessment_service.assess_submission(
                db,
                submission.id,
            )
        )

        assert assessment.bid_submission_id == submission.id

        assert assessment.status == "PENDING"

        assert assessment.score is None

        assert assessment.risk_level is None

        assert (
            "No compliance checks"
            in assessment.summary
        )

        assert assessment.assessment_metadata[
            "total_checks"
        ] == 0

        assert assessment.assessed_at is None

    finally:

        db.rollback()

        if submission:
            cleanup_test_data(
                db,
                bidder,
                tender,
                submission,
            )

        db.close()


def test_all_pass_returns_compliant_low_risk():

    db = SessionLocal()

    bidder = None
    tender = None
    submission = None

    try:

        (
            bidder,
            tender,
            submission,
            _,
        ) = create_test_data(
            db,
            ["PASS", "PASS", "PASS"],
        )

        assessment = (
            compliance_assessment_service.assess_submission(
                db,
                submission.id,
            )
        )

        assert assessment.score == 100.0

        assert assessment.risk_level == "LOW"

        assert assessment.status == "COMPLIANT"

        assert assessment.assessed_at is not None

        assert assessment.assessment_metadata[
            "total_checks"
        ] == 3

        assert assessment.assessment_metadata[
            "passed"
        ] == 3

        assert assessment.assessment_metadata[
            "failed"
        ] == 0

        assert assessment.assessment_metadata[
            "review"
        ] == 0

        assert assessment.assessment_metadata[
            "pending"
        ] == 0

    finally:

        db.rollback()

        if submission:
            db.query(
                type(assessment)
            ).filter(
                type(assessment).id
                == assessment.id
            ).delete(
                synchronize_session=False
            )

            db.commit()

            cleanup_test_data(
                db,
                bidder,
                tender,
                submission,
            )

        db.close()


def test_pass_and_review_returns_medium_risk_review():

    db = SessionLocal()

    bidder = None
    tender = None
    submission = None
    assessment = None

    try:

        (
            bidder,
            tender,
            submission,
            _,
        ) = create_test_data(
            db,
            ["PASS", "REVIEW", "PASS"],
        )

        assessment = (
            compliance_assessment_service.assess_submission(
                db,
                submission.id,
            )
        )

        assert assessment.score == 66.67

        assert assessment.risk_level == "MEDIUM"

        assert assessment.status == "REVIEW"

        assert assessment.assessment_metadata[
            "passed"
        ] == 2

        assert assessment.assessment_metadata[
            "review"
        ] == 1

    finally:

        db.rollback()

        if assessment:
            db.delete(assessment)
            db.commit()

        if submission:
            cleanup_test_data(
                db,
                bidder,
                tender,
                submission,
            )

        db.close()


def test_pass_and_fail_returns_high_risk_non_compliant():

    db = SessionLocal()

    bidder = None
    tender = None
    submission = None
    assessment = None

    try:

        (
            bidder,
            tender,
            submission,
            _,
        ) = create_test_data(
            db,
            ["PASS", "FAIL", "PASS", "PASS"],
        )

        assessment = (
            compliance_assessment_service.assess_submission(
                db,
                submission.id,
            )
        )

        assert assessment.score == 75.0

        assert assessment.risk_level == "HIGH"

        assert assessment.status == "NON_COMPLIANT"

        assert assessment.assessment_metadata[
            "passed"
        ] == 3

        assert assessment.assessment_metadata[
            "failed"
        ] == 1

    finally:

        db.rollback()

        if assessment:
            db.delete(assessment)
            db.commit()

        if submission:
            cleanup_test_data(
                db,
                bidder,
                tender,
                submission,
            )

        db.close()


def test_pending_check_returns_medium_risk_review():

    db = SessionLocal()

    bidder = None
    tender = None
    submission = None
    assessment = None

    try:

        (
            bidder,
            tender,
            submission,
            _,
        ) = create_test_data(
            db,
            ["PASS", "PENDING", "PASS"],
        )

        assessment = (
            compliance_assessment_service.assess_submission(
                db,
                submission.id,
            )
        )

        assert assessment.score == 66.67

        assert assessment.risk_level == "MEDIUM"

        assert assessment.status == "REVIEW"

        assert assessment.assessment_metadata[
            "pending"
        ] == 1

    finally:

        db.rollback()

        if assessment:
            db.delete(assessment)
            db.commit()

        if submission:
            cleanup_test_data(
                db,
                bidder,
                tender,
                submission,
            )

        db.close()