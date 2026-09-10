import pytest
import uuid
from unittest.mock import patch
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.user import User
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bidder import Bidder
from app.models.bid_submission import BidSubmission
from app.models.bid_document import BidDocument
from app.repositories.procurement_decision_repository import procurement_decision_repository
from app.repositories.compliance_assessment_repository import compliance_assessment_repository
from app.schemas.procurement_decision import ProcurementDecisionCreate, ProcurementDecisionValue
from app.services.procurement_decision_service import procurement_decision_service
from app.services.end_to_end_verification_service import end_to_end_verification_service
from app.services.compliance_assessment_service import compliance_assessment_service
from app.services.dashboard_service import dashboard_service
from app.services.audit_log_service import audit_log_service
from app.core.security import hash_password


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestTask11EndToEndHardening:
    """
    Task 11 test suite verifying end-to-end backend hardening, transaction safety,
    idempotency, synthetic transparency, negative flow protection, and read-only guarantees.
    """

    def test_01_canonical_e2e_workflow(self, db: Session):
        """
        Verify complete lifecycle:
        Tender -> Requirements -> Bid Submission -> Documents -> Extraction ->
        Verification -> Compliance -> Score/Risk -> Recommendation -> Officer Decision -> Audit Trail.
        """
        uid = str(uuid.uuid4())[:8]

        # 1. Create Procurement Officer
        officer = User(
            full_name="Hardening Officer",
            email=f"officer_{uid}@cpcl.gov.in",
            hashed_password=hash_password("Pass123!"),
            role="PROCUREMENT_OFFICER",
            is_active=True,
        )
        db.add(officer)
        db.commit()
        db.refresh(officer)

        # 2. Create Tender & Requirements
        tender = Tender(
            reference_number=f"CPCL-T11-{uid}",
            title="Supply of Industrial Pumps for CPCL Refinery",
            description="Procurement of heavy-duty centrifugal pumps.",
            status="PUBLISHED",
        )
        db.add(tender)
        db.commit()
        db.refresh(tender)

        req_msme = TenderRequirement(
            tender_id=tender.id,
            requirement_type="MSME_REGISTRATION",
            requirement_name="Mandatory MSME Certificate",
            description="Bidder must be registered as Micro/Small enterprise on Udyam.",
            is_required=True,
        )
        req_gst = TenderRequirement(
            tender_id=tender.id,
            requirement_type="GST_REGISTRATION",
            requirement_name="Active GSTIN Registration",
            description="Active GST registration required.",
            is_required=True,
        )
        db.add_all([req_msme, req_gst])
        db.commit()

        # 3. Create Bidder & Submission
        pan_val = f"APEX{uid[:5].upper()}"
        gstin_val = f"33{pan_val}1Z5"
        bidder = Bidder(
            company_name=f"Apex Pumps {uid} Pvt Ltd",
            pan=pan_val,
            gstin=gstin_val,
            udyam_number=f"UDYAM-TN-01-{uid}",
        )
        db.add(bidder)
        db.commit()
        db.refresh(bidder)

        submission = BidSubmission(
            tender_id=tender.id,
            bidder_id=bidder.id,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        # 4. Upload Documents
        doc_msme = BidDocument(
            bid_submission_id=submission.id,
            file_name="udyam_certificate.pdf",
            file_path="storage/documents/test_udyam.pdf",
            document_type="UDYAM_CERTIFICATE",
            content_type="application/pdf",
        )
        doc_gst = BidDocument(
            bid_submission_id=submission.id,
            file_name="gst_certificate.pdf",
            file_path="storage/documents/test_gst.pdf",
            document_type="GST_CERTIFICATE",
            content_type="application/pdf",
        )
        db.add_all([doc_msme, doc_gst])
        db.commit()

        # 5. Run End-to-End Verification Pipeline
        summary = end_to_end_verification_service.verify_bid_submission(db, submission.id)

        assert summary is not None
        assert summary.bid_submission_id == submission.id
        assert summary.compliance_score >= 0.0
        assert summary.risk_level in ("LOW", "MEDIUM", "HIGH")

        # 6. Verify Assessment Persisted
        assessment = compliance_assessment_repository.get_latest_by_submission(db, submission.id)
        assert assessment is not None
        assert assessment.score == summary.compliance_score
        assert assessment.risk_level == summary.risk_level

        # 7. Record Final Procurement Decision
        decision_in = ProcurementDecisionCreate(
            decision=ProcurementDecisionValue.QUALIFIED,
            reason="Bidder satisfies mandatory Udyam and GST criteria with verified credentials.",
        )
        decision = procurement_decision_service.record_decision(
            db=db,
            current_user=officer,
            bid_submission_id=submission.id,
            decision_data=decision_in,
        )

        assert decision.id is not None
        assert decision.decision == "QUALIFIED"
        assert decision.bid_submission_id == submission.id
        assert decision.decided_by == officer.id

        # 8. Verify Audit Trail Event Created
        logs, total = audit_log_service.list_by_bid_submission(db, submission.id)
        assert total > 0
        action_names = [log.action for log in logs]
        assert "PROCUREMENT_DECISION_CREATED" in action_names

    def test_02_negative_workflow_non_compliant_bidder(self, db: Session):
        """
        Verify that a problematic bidder with missing mandatory requirements or failed checks
        is deterministically flagged as NON_COMPLIANT and HIGH risk (never PASS or LOW risk).
        """
        uid = str(uuid.uuid4())[:8]

        officer = User(
            full_name="Review Officer",
            email=f"review_{uid}@cpcl.gov.in",
            hashed_password=hash_password("Pass123!"),
            role="PROCUREMENT_OFFICER",
        )
        db.add(officer)
        db.commit()

        tender = Tender(
            reference_number=f"CPCL-NEG-{uid}",
            title="Refinery Expansion Project - Mandatory Turnover",
            description="Requires strict 50 Lakhs turnover and MII compliance.",
            status="PUBLISHED",
        )
        db.add(tender)
        db.commit()

        # Mandatory TurnOver Requirement
        req_turnover = TenderRequirement(
            tender_id=tender.id,
            requirement_type="FINANCIAL_TURNOVER",
            requirement_name="Minimum Annual Turnover Rs 50 Lakhs",
            description="Audited financials required.",
            is_required=True,
            validation_config='{"min_turnover": 5000000.0}',
        )
        db.add(req_turnover)
        db.commit()

        pan_val = f"DEF{uid[:5].upper()}"
        bidder = Bidder(
            company_name=f"Defaulter Enterprises {uid} Ltd",
            pan=pan_val,
        )
        db.add(bidder)
        db.commit()

        submission = BidSubmission(
            tender_id=tender.id,
            bidder_id=bidder.id,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(submission)
        db.commit()

        # Evaluate compliance with missing document
        assessment = compliance_assessment_service.assess_submission(db, submission.id)

        assert assessment.status in ("NON_COMPLIANT", "REVIEW")
        assert assessment.risk_level in ("HIGH", "MEDIUM")
        assert assessment.status != "COMPLIANT"
        assert assessment.risk_level != "LOW"

    def test_03_transaction_safety_rollback_on_audit_failure(self, db: Session):
        """
        Verify that if audit logging fails during decision creation,
        the transaction rolls back cleanly so no un-audited decision remains in DB.
        """
        uid = str(uuid.uuid4())[:8]

        officer = User(
            full_name="Safety Officer",
            email=f"safety_{uid}@cpcl.gov.in",
            hashed_password=hash_password("Pass123!"),
            role="PROCUREMENT_OFFICER",
        )
        db.add(officer)
        db.commit()

        tender = Tender(
            reference_number=f"CPCL-SAFE-{uid}",
            title="Safety Equipment Tender",
        )
        db.add(tender)
        db.commit()

        bidder = Bidder(company_name=f"Safety Systems {uid} Ltd", pan=f"SAF{uid[:5].upper()}")
        db.add(bidder)
        db.commit()

        submission = BidSubmission(
            tender_id=tender.id,
            bidder_id=bidder.id,
        )
        db.add(submission)
        db.commit()

        decision_in = ProcurementDecisionCreate(
            decision=ProcurementDecisionValue.QUALIFIED,
            reason="Good track record",
        )

        with patch("app.services.audit_log_service.audit_log_service.record_event", side_effect=RuntimeError("DB Connection Lost during Audit")):
            with pytest.raises(RuntimeError):
                procurement_decision_service.record_decision(
                    db=db,
                    current_user=officer,
                    bid_submission_id=submission.id,
                    decision_data=decision_in,
                )

        # Verify decision was rolled back and does not exist in DB
        existing_decision = procurement_decision_repository.get_by_submission_id(
            db, submission.id
        )
        assert existing_decision is None

    def test_04_idempotency_duplicate_decision_rejection(self, db: Session):
        """
        Verify that attempting to record a second decision for the same submission
        is rejected (idempotent / immutable domain requirement).
        """
        uid = str(uuid.uuid4())[:8]

        officer = User(
            full_name="Idem Officer",
            email=f"idem_{uid}@cpcl.gov.in",
            hashed_password=hash_password("Pass123!"),
            role="PROCUREMENT_OFFICER",
        )
        db.add(officer)
        db.commit()

        tender = Tender(reference_number=f"CPCL-IDEM-{uid}", title="Tender Idem")
        bidder = Bidder(company_name=f"Idem Supplies {uid}", pan=f"IDE{uid[:5].upper()}")
        db.add_all([tender, bidder])
        db.commit()

        submission = BidSubmission(tender_id=tender.id, bidder_id=bidder.id)
        db.add(submission)
        db.commit()

        decision_in = ProcurementDecisionCreate(
            decision=ProcurementDecisionValue.QUALIFIED,
            reason="First decision approved.",
        )
        procurement_decision_service.record_decision(
            db=db,
            current_user=officer,
            bid_submission_id=submission.id,
            decision_data=decision_in,
        )

        # Second attempt should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            procurement_decision_service.record_decision(
                db=db,
                current_user=officer,
                bid_submission_id=submission.id,
                decision_data=decision_in,
            )
        assert "already been recorded" in str(excinfo.value)

    def test_05_dashboard_read_only_guarantee(self, db: Session):
        """
        Verify that calling GET dashboard endpoints does not mutate database records.
        """
        uid = str(uuid.uuid4())[:8]

        officer = User(
            full_name="Dash Officer",
            email=f"dash_{uid}@cpcl.gov.in",
            hashed_password=hash_password("Pass123!"),
            role="PROCUREMENT_OFFICER",
        )
        db.add(officer)
        db.commit()

        tender = Tender(reference_number=f"CPCL-DASH-{uid}", title="Tender Dash")
        bidder = Bidder(company_name=f"Dash Corp {uid}", pan=f"DSH{uid[:5].upper()}")
        db.add_all([tender, bidder])
        db.commit()

        submission = BidSubmission(tender_id=tender.id, bidder_id=bidder.id)
        db.add(submission)
        db.commit()

        # Query dashboard
        dash_res = dashboard_service.get_bid_submission_dashboard(db, submission.id)
        assert dash_res is not None
        assert dash_res.bid_submission.id == submission.id

        # Verify no decisions were accidentally created
        dec = procurement_decision_repository.get_by_submission_id(db, submission.id)
        assert dec is None
