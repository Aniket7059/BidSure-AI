import uuid
import pytest


from app.database.session import SessionLocal

from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_submission import BidSubmission
from app.models.compliance_check import ComplianceCheck
from app.models.compliance_assessment import ComplianceAssessment

from app.services.compliance_assessment_service import (
    compliance_assessment_service,
)

from app.services.recommendation_service import (
    recommendation_service,
)


def create_test_data(db, check_statuses):
    """
    Create isolated test data for recommendation testing.
    """

    unique_id = uuid.uuid4().hex[:8].upper()

    bidder = Bidder(
        company_name=f"Recommendation Test Company {unique_id}",
        gstin=f"29REC{unique_id}A1Z5",
        pan=f"J{unique_id[:4]}P",
        udyam_number=f"UDYAM-RECOMM-{unique_id}",
    )

    tender = Tender(
        title=f"Recommendation Test Tender {unique_id}",
        reference_number=f"RECOMM-REF-{unique_id}",
        description="Temporary tender for recommendation testing.",
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

    for index, status in enumerate(
        check_statuses,
        start=1,
    ):

        requirement = TenderRequirement(
            tender_id=tender.id,
            requirement_type="TEST",
            requirement_name=f"Recommendation Requirement {index}",
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
                "source": "recommendation_test",
            },
            checked_by="TEST",
        )

        db.add(check)
        db.commit()

        db.refresh(check)

        checks.append(check)

    return (
        bidder,
        tender,
        submission,
        checks,
    )


def cleanup_test_data(
    db,
    bidder,
    tender,
    submission,
):
    """
    Remove all test data belonging to a submission.
    """

    db.query(ComplianceAssessment).filter(
        ComplianceAssessment.bid_submission_id
        == submission.id
    ).delete(
        synchronize_session=False
    )

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


def create_assessment(
    db,
    submission_id,
):
    """
    Create a compliance assessment using the
    actual assessment service.
    """

    return (
        compliance_assessment_service.assess_submission(
            db,
            submission_id,
        )
    )


def test_fail_generates_manual_review_recommendation():

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
            ["PASS", "FAIL", "PASS"],
        )

        create_assessment(
            db,
            submission.id,
        )

        assessment = (
            recommendation_service.generate_recommendation(
                db,
                submission.id,
            )
        )

        rec_str = str(assessment.summary or assessment.recommendation)
        assert (
            "Do not proceed with automatic qualification" in rec_str
            or assessment.recommendation == "DO_NOT_RECOMMEND"
        )

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


def test_review_generates_manual_review_recommendation():

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
            ["PASS", "REVIEW", "PASS"],
        )

        create_assessment(
            db,
            submission.id,
        )

        assessment = (
            recommendation_service.generate_recommendation(
                db,
                submission.id,
            )
        )

        rec_str = str(assessment.summary or assessment.recommendation)
        assert (
            "Manual review is recommended" in rec_str
            or assessment.recommendation == "REVIEW_REQUIRED"
        )

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


def test_pending_generates_manual_review_recommendation():

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
            ["PASS", "PENDING", "PASS"],
        )

        create_assessment(
            db,
            submission.id,
        )

        assessment = (
            recommendation_service.generate_recommendation(
                db,
                submission.id,
            )
        )

        rec_str = str(assessment.summary or assessment.recommendation)
        assert (
            "Manual review is recommended" in rec_str
            or assessment.recommendation == "REVIEW_REQUIRED"
        )

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


def test_all_pass_generates_proceed_recommendation():

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

        create_assessment(
            db,
            submission.id,
        )

        assessment = (
            recommendation_service.generate_recommendation(
                db,
                submission.id,
            )
        )

        rec_str = str(assessment.summary or assessment.recommendation)
        assert (
            "satisfies the evaluated compliance requirements" in rec_str
            or assessment.recommendation == "PROCEED"
        )

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


def test_missing_assessment_returns_error():

    db = SessionLocal()

    try:

        with pytest.raises(
            ValueError,
            match="Compliance assessment not found",
        ):

            recommendation_service.generate_recommendation(
                db,
                999999,
            )

    finally:

        db.rollback()
        db.close()

def test_fail_takes_priority_over_review_and_pending():

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
            ["PASS", "FAIL", "REVIEW", "PENDING"],
        )

        create_assessment(
            db,
            submission.id,
        )

        assessment = (
            recommendation_service.generate_recommendation(
                db,
                submission.id,
            )
        )

        rec_str = str(assessment.summary or assessment.recommendation)
        assert (
            "Do not proceed with automatic qualification" in rec_str
            or assessment.recommendation == "DO_NOT_RECOMMEND"
        )

        assert (
            "Manual review is recommended"
            not in assessment.recommendation
        )

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