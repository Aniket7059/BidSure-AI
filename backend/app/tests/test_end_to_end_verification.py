import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_submission import BidSubmission
from app.models.bid_document import BidDocument
from app.models.document_extraction import DocumentExtraction
from app.models.verification_result import VerificationResult
from app.providers.register import register_providers
from app.services.evaluators.register import register_evaluators
from app.services.end_to_end_verification_service import (
    end_to_end_verification_service,
)

import pytest
from app.api.dependencies import get_current_user
from app.models.user import User


def mock_get_current_user():
    return User(
        id=1,
        full_name="Test Officer",
        email="officer@test.com",
        role="PROCUREMENT_OFFICER",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app)


def setup_verification_test_data(db, gstin_override=None, include_pan_doc=True):
    """
    Creates isolated test data for end-to-end verification testing.
    """
    register_providers()
    register_evaluators()

    uid = uuid.uuid4().hex[:8].upper()
    
    # Mock providers recognize 27ABCDE1234F1Z5 (GST) and ABCDE1234F (PAN)
    # with legal_name "ABC INDUSTRIES PRIVATE LIMITED"
    gstin_val = gstin_override or "27ABCDE1234F1Z5"
    pan_val = "ABCDE1234F" if not gstin_override else f"INV{uid[:4]}X"
    company_name = "ABC INDUSTRIES PRIVATE LIMITED" if not gstin_override else f"E2E Test Company {uid}"

    bidder = Bidder(
        company_name=company_name,
        gstin=f"27ABCDE{uid[:4]}F1Z5",
        pan=f"F{uid[:4]}5678K",
        udyam_number=f"UDYAM-E2E-{uid}",
    )
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    tender = Tender(
        title=f"E2E Verification Tender {uid}",
        reference_number=f"E2E-REF-{uid}",
        description="Test tender for end-to-end verification",
        status="ACTIVE",
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)

    req_gst = TenderRequirement(
        tender_id=tender.id,
        requirement_type="GST",
        requirement_name="GST Registration Certificate",
        description="Valid GSTIN required",
        is_required=True,
    )
    req_pan = TenderRequirement(
        tender_id=tender.id,
        requirement_type="PAN",
        requirement_name="PAN Card",
        description="Valid PAN required",
        is_required=True,
    )
    db.add_all([req_gst, req_pan])
    db.commit()

    submission = BidSubmission(
        tender_id=tender.id,
        bidder_id=bidder.id,
        status="SUBMITTED",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # 1. GST Document & Extraction
    doc_gst = BidDocument(
        bid_submission_id=submission.id,
        document_type="GST_CERTIFICATE",
        file_name=f"gst_{uid}.pdf",
        file_path=f"/uploads/gst_{uid}.pdf",
        status="PROCESSED",
    )
    db.add(doc_gst)
    db.commit()
    db.refresh(doc_gst)

    ext_gst = DocumentExtraction(
        bid_document_id=doc_gst.id,
        extracted_data={
            "document_type": "GST_CERTIFICATE",
            "fields": {
                "gstin": gstin_val,
                "legal_name": bidder.company_name,
                "status": "ACTIVE",
            },
        },
        confidence_score=0.98,
        extraction_status="COMPLETED",
    )
    db.add(ext_gst)

    # 2. Optional PAN Document & Extraction
    if include_pan_doc:
        doc_pan = BidDocument(
            bid_submission_id=submission.id,
            document_type="PAN",
            file_name=f"pan_{uid}.pdf",
            file_path=f"/uploads/pan_{uid}.pdf",
            status="PROCESSED",
        )
        db.add(doc_pan)
        db.commit()
        db.refresh(doc_pan)

        ext_pan = DocumentExtraction(
            bid_document_id=doc_pan.id,
            extracted_data={
                "document_type": "PAN",
                "fields": {
                    "pan": pan_val,
                    "name": bidder.company_name,
                },
            },
            confidence_score=0.95,
            extraction_status="COMPLETED",
        )
        db.add(ext_pan)

    db.commit()
    return bidder, tender, submission, [req_gst, req_pan]


def test_successful_end_to_end_verification():
    db = SessionLocal()
    try:
        bidder, tender, submission, reqs = setup_verification_test_data(
            db, include_pan_doc=True
        )

        summary = end_to_end_verification_service.verify_bid_submission(
            db, submission.id
        )

        assert summary.bid_submission_id == submission.id
        assert summary.tender_id == tender.id
        assert summary.status == "COMPLETED"
        assert summary.documents_processed_count == 2
        assert summary.verifications_executed_count >= 2
        assert summary.compliance_checks_count == 2
        assert summary.overall_status in ("COMPLIANT", "REVIEW")
        assert summary.compliance_score is not None
        assert summary.risk_level in ("LOW", "MEDIUM")
        assert len(summary.workflow_log) >= 5
    finally:
        db.close()


def test_missing_document_handling():
    db = SessionLocal()
    try:
        # Include GST doc but omit PAN doc
        bidder, tender, submission, reqs = setup_verification_test_data(
            db, include_pan_doc=False
        )

        summary = end_to_end_verification_service.verify_bid_submission(
            db, submission.id
        )

        assert summary.status == "COMPLETED"
        assert summary.documents_processed_count == 1
        assert summary.compliance_checks_count == 2
        # Mandatory PAN missing -> overall NON_COMPLIANT / HIGH risk
        assert summary.overall_status == "NON_COMPLIANT"
        assert summary.risk_level == "HIGH"
    finally:
        db.close()


def test_verification_provider_failure_handling():
    db = SessionLocal()
    try:
        # Pass invalid GSTIN to trigger verification/provider failure
        bidder, tender, submission, reqs = setup_verification_test_data(
            db, gstin_override="27INVALID0000X1Z5", include_pan_doc=True
        )

        summary = end_to_end_verification_service.verify_bid_submission(
            db, submission.id
        )

        assert summary.status == "COMPLETED"
        # Verification failed/not found -> overall status REVIEW or NON_COMPLIANT
        assert summary.overall_status in ("REVIEW", "NON_COMPLIANT")
        gst_v = next(v for v in summary.verifications_summary if v.requirement_type == "GST")
        assert gst_v.status in ("NOT_FOUND", "NOT_VERIFIED", "ERROR")
    finally:
        db.close()


def test_verify_bid_submission_api_endpoint():
    db = SessionLocal()
    try:
        bidder, tender, submission, reqs = setup_verification_test_data(
            db, include_pan_doc=True
        )

        response = client.post(f"/bid-submissions/{submission.id}/verify")

        assert response.status_code == 200
        data = response.json()

        assert data["bid_submission_id"] == submission.id
        assert data["tender_id"] == tender.id
        assert data["status"] == "COMPLETED"
        assert "documents_summary" in data
        assert "verifications_summary" in data
        assert "overall_status" in data
        assert "compliance_score" in data
        assert "risk_level" in data
        assert "workflow_log" in data
    finally:
        db.close()
