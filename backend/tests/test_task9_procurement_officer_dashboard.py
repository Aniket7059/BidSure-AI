from datetime import datetime, timezone
from unittest.mock import patch
import pytest
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
from app.models.compliance_check import ComplianceCheck
from app.models.compliance_assessment import ComplianceAssessment
from app.models.discrepancy import Discrepancy
from app.models.procurement_decision import ProcurementDecision
from app.models.audit_log import AuditLog
from app.models.user import User
from app.api.dependencies import get_current_user


def create_mock_user(role="PROCUREMENT_OFFICER", user_id=101):
    return User(
        id=user_id,
        full_name="Dashboard Officer",
        email=f"officer_{user_id}@test.com",
        hashed_password="mock_hashed_password",
        role=role,
        is_active=True,
    )


@pytest.fixture
def client_officer():
    app.dependency_overrides[get_current_user] = lambda: create_mock_user("PROCUREMENT_OFFICER", 101)
    c = TestClient(app)
    yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client_unauthorized():
    app.dependency_overrides[get_current_user] = lambda: create_mock_user("BIDDER", 102)
    c = TestClient(app)
    yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def complete_bid_fixture():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 101)
        db.merge(user)
        db.commit()

        # 1. Tender
        tender = Tender(
            title="Supply of High Precision Valves",
            reference_number=f"TND-DASH-{datetime.now().timestamp()}",
            description="Procurement of industrial valves",
            status="PUBLISHED",
        )
        db.add(tender)
        db.commit()
        db.refresh(tender)

        # 2. Requirements
        req1 = TenderRequirement(
            tender_id=tender.id,
            requirement_type="GST",
            requirement_name="GST Registration",
            description="Active GSTIN required",
            is_required=True,
        )
        req2 = TenderRequirement(
            tender_id=tender.id,
            requirement_type="PAN",
            requirement_name="PAN Card Verification",
            description="Valid PAN required",
            is_required=True,
        )
        req3 = TenderRequirement(
            tender_id=tender.id,
            requirement_type="ISO_CERTIFICATE",
            requirement_name="ISO 9001 Certificate",
            description="Optional quality certificate",
            is_required=False,
        )
        db.add_all([req1, req2, req3])
        db.commit()
        db.refresh(req1)
        db.refresh(req2)
        db.refresh(req3)

        ts = int(datetime.now().timestamp() * 1000) % 1000000
        # 3. Bidder
        bidder = Bidder(
            company_name="Apex Valve Industries Private Limited",
            gstin=f"27AAA{ts:07d}1Z5",
            pan=f"AAA{ts:06d}A",
            udyam_number=f"UDYAM-MH-12-{ts:06d}",
            contact_email="bids@apexvalves.com",
            contact_phone="+919876543210",
        )
        db.add(bidder)
        db.commit()
        db.refresh(bidder)

        # 4. Bid Submission
        submission = BidSubmission(
            tender_id=tender.id,
            bidder_id=bidder.id,
            status="SUBMITTED",
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        # 5. Documents
        doc1 = BidDocument(
            bid_submission_id=submission.id,
            document_type="GST_CERTIFICATE",
            file_name="gst_cert.pdf",
            file_path="/storage/bids/gst_cert.pdf",
            status="PROCESSED",
        )
        db.add(doc1)
        db.commit()
        db.refresh(doc1)

        ext1 = DocumentExtraction(
            bid_document_id=doc1.id,
            extraction_status="COMPLETED",
            extracted_data={"gstin": "27AAACA12341Z5"},
            confidence_score=0.98,
        )
        db.add(ext1)

        # 6. Verification Results
        verif1 = VerificationResult(
            bid_submission_id=submission.id,
            bid_document_id=doc1.id,
            provider="GSTN_PORTAL",
            verification_type="GST",
            identifier="27AAACA12341Z5",
            verification_status="VERIFIED",
            message="GSTIN active and verified",
        )
        db.add(verif1)

        # 7. Compliance Checks
        chk1 = ComplianceCheck(
            bid_submission_id=submission.id,
            tender_requirement_id=req1.id,
            status="PASS",
            reason="GSTIN verified active on portal",
            evidence={"gstin": "27AAACA12341Z5"},
        )
        chk2 = ComplianceCheck(
            bid_submission_id=submission.id,
            tender_requirement_id=req2.id,
            status="PASS",
            reason="PAN details matched",
            evidence={"pan": "AAACA1234A"},
        )
        chk3 = ComplianceCheck(
            bid_submission_id=submission.id,
            tender_requirement_id=req3.id,
            status="REVIEW",
            reason="ISO certificate requires verification",
            evidence={},
        )
        db.add_all([chk1, chk2, chk3])

        # 8. Discrepancies
        disc1 = Discrepancy(
            bid_submission_id=submission.id,
            tender_requirement_id=req3.id,
            type="UNSUPPORTED_VERIFICATION",
            severity="MEDIUM",
            status="OPEN",
            title="ISO Certificate Manual Verification Needed",
            description="ISO certification portal not automated",
        )
        db.add(disc1)

        # 9. Compliance Assessment with AI Recommendation Detail
        rec_detail = {
            "assessment_id": 1,
            "bid_submission_id": submission.id,
            "overall_status": "REVIEW",
            "score": 88.0,
            "risk_level": "LOW",
            "recommendation": "REVIEW_REQUIRED",
            "confidence": "HIGH",
            "summary": "Mandatory requirements passed. Review optional ISO certificate.",
            "critical_issues": [],
            "review_items": [{"requirement": "ISO 9001 Certificate", "reason": "Manual review needed"}],
            "missing_evidence": [],
            "strengths": [{"point": "GST and PAN fully verified"}],
            "officer_actions": [{"action": "Verify ISO certificate manually"}],
            "generated_by": "GEMINI",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        assessment = ComplianceAssessment(
            bid_submission_id=submission.id,
            score=88.0,
            risk_level="LOW",
            status="REVIEW",
            summary="Assessment completes with review requirement",
            assessment_metadata={"recommendation_detail": rec_detail, "mandatory_pass": 2, "mandatory_fail": 0, "mandatory_review": 0, "optional_pass": 0, "optional_fail": 0, "optional_review": 1},
            assessed_at=datetime.now(timezone.utc),
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        # 10. Procurement Officer Decision
        decision = ProcurementDecision(
            bid_submission_id=submission.id,
            decision="QUALIFIED",
            reason="All statutory mandatory requirements met cleanly; optional ISO waived.",
            decided_by=user.id,
            assessment_id=assessment.id,
            recommendation_at_decision="REVIEW_REQUIRED",
            score_snapshot=88.0,
            risk_snapshot="LOW",
            is_override=False,
        )
        db.add(decision)

        # 11. Audit Log
        audit = AuditLog(
            user_id=user.id,
            bid_submission_id=submission.id,
            action="PROCUREMENT_DECISION_CREATED",
            entity_type="PROCUREMENT_DECISION",
            entity_id=decision.id,
            details="Officer recorded QUALIFIED decision",
        )
        db.add(audit)

        db.commit()
        db.refresh(submission)
        return submission.id, tender.id
    finally:
        db.close()


def test_get_bid_submission_dashboard_success_complete_state(client_officer, complete_bid_fixture):
    submission_id, tender_id = complete_bid_fixture
    response = client_officer.get(f"/dashboard/bid-submissions/{submission_id}")
    assert response.status_code == 200
    data = response.json()

    # 1. Bid Submission Section
    assert data["bid_submission"]["id"] == submission_id
    assert data["bid_submission"]["tender_id"] == tender_id

    # 2. Tender Section
    assert data["tender"]["id"] == tender_id
    assert data["tender"]["requirement_count"] == 3

    # 3. Bidder Section & PII Masking
    assert data["bidder"]["company_name"] == "Apex Valve Industries Private Limited"
    assert data["bidder"]["gstin"].startswith("27AAA") and "****" in data["bidder"]["gstin"]
    assert data["bidder"]["pan"].startswith("AAA") and "****" in data["bidder"]["pan"]

    # 4. Summary Section
    assert data["summary"]["score"] == 88.0
    assert data["summary"]["risk_level"] == "LOW"
    assert data["summary"]["recommendation"] == "REVIEW_REQUIRED"
    assert data["summary"]["final_decision"] == "QUALIFIED"
    assert data["summary"]["mandatory"]["total"] == 2
    assert data["summary"]["mandatory"]["pass"] == 2
    assert data["summary"]["optional"]["total"] == 1
    assert data["summary"]["optional"]["review"] == 1

    # 5. Requirements Section
    assert len(data["requirements"]) == 3
    req_types = [r["requirement_type"] for r in data["requirements"]]
    assert "GST" in req_types
    assert "PAN" in req_types
    assert "ISO_CERTIFICATE" in req_types

    # 6. Documents Section
    assert len(data["documents"]) == 1
    assert data["documents"][0]["file_name"] == "gst_cert.pdf"
    assert data["documents"][0]["extraction_status"] == "COMPLETED"

    # 7. Verification Section
    assert len(data["verification"]) == 1
    assert data["verification"][0]["provider"] == "GSTN_PORTAL"
    assert data["verification"][0]["status"] == "VERIFIED"

    # 8. Discrepancies Section
    assert len(data["discrepancies"]) == 1
    assert data["discrepancies"][0]["type"] == "UNSUPPORTED_VERIFICATION"

    # 9. Compliance Section
    assert data["compliance"]["status"] == "REVIEW"
    assert data["compliance"]["score"] == 88.0

    # 10. Recommendation Section
    assert data["recommendation"]["recommendation"] == "REVIEW_REQUIRED"
    assert data["recommendation"]["generated_by"] == "GEMINI"

    # 11. Decision Section
    assert data["decision"]["decision"] == "QUALIFIED"
    assert data["decision"]["decided_by"]["full_name"] == "Dashboard Officer"
    assert data["decision"]["override"] is False

    # 12. Audit Section
    assert data["audit"]["total_events"] >= 1
    assert data["audit"]["events"][0]["action"] == "PROCUREMENT_DECISION_CREATED"


def test_get_bid_submission_dashboard_partial_lifecycle_states(client_officer):
    db = SessionLocal()
    try:
        tender = Tender(
            title="Empty Test Tender",
            reference_number=f"TND-PART-{datetime.now().timestamp()}",
            status="DRAFT",
        )
        bidder = Bidder(company_name="New Bidder Inc")
        db.add_all([tender, bidder])
        db.commit()

        submission = BidSubmission(
            tender_id=tender.id,
            bidder_id=bidder.id,
            status="SUBMITTED",
        )
        db.add(submission)
        db.commit()
        sub_id = submission.id
    finally:
        db.close()

    response = client_officer.get(f"/dashboard/bid-submissions/{sub_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["bid_submission"]["id"] == sub_id
    assert data["compliance"] is None
    assert data["recommendation"] is None
    assert data["decision"] is None
    assert data["summary"]["score"] is None
    assert data["summary"]["risk_level"] is None
    assert data["summary"]["recommendation"] is None
    assert data["summary"]["final_decision"] is None
    assert data["requirements"] == []
    assert data["documents"] == []
    assert data["discrepancies"] == []


def test_get_bid_submission_dashboard_404_not_found(client_officer):
    response = client_officer.get("/dashboard/bid-submissions/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_bid_submission_dashboard_unauthorized_role(client_unauthorized, complete_bid_fixture):
    submission_id, _ = complete_bid_fixture
    response = client_unauthorized.get(f"/dashboard/bid-submissions/{submission_id}")
    assert response.status_code == 403


def test_get_bid_submission_dashboard_read_only_guarantee(client_officer, complete_bid_fixture):
    submission_id, _ = complete_bid_fixture

    with patch("app.services.recommendation_service.recommendation_service.generate_recommendation") as mock_gen, \
         patch("app.services.compliance_assessment_service.compliance_assessment_service.assess_submission") as mock_assess:

        response = client_officer.get(f"/dashboard/bid-submissions/{submission_id}")
        assert response.status_code == 200

        # Assert no write/evaluation logic was invoked during dashboard GET
        mock_gen.assert_not_called()
        mock_assess.assert_not_called()


def test_get_bid_submission_dashboard_discrepancy_sorting(client_officer):
    db = SessionLocal()
    try:
        tender = Tender(title="Disc Test Tender", reference_number=f"TND-DISC-{datetime.now().timestamp()}")
        bidder = Bidder(company_name="Disc Bidder")
        db.add_all([tender, bidder])
        db.commit()

        sub = BidSubmission(tender_id=tender.id, bidder_id=bidder.id)
        db.add(sub)
        db.commit()

        d1 = Discrepancy(bid_submission_id=sub.id, type="MISMATCH", severity="LOW", status="RESOLVED", title="Low Resolved", description="desc")
        d2 = Discrepancy(bid_submission_id=sub.id, type="MISMATCH", severity="CRITICAL", status="OPEN", title="Critical Open", description="desc")
        d3 = Discrepancy(bid_submission_id=sub.id, type="MISMATCH", severity="HIGH", status="OPEN", title="High Open", description="desc")
        db.add_all([d1, d2, d3])
        db.commit()
        sub_id = sub.id
    finally:
        db.close()

    response = client_officer.get(f"/dashboard/bid-submissions/{sub_id}")
    assert response.status_code == 200
    disc_items = response.json()["discrepancies"]
    assert len(disc_items) == 3
    # Open Critical first, Open High second, Resolved Low last
    assert disc_items[0]["severity"] == "CRITICAL"
    assert disc_items[0]["status"] == "OPEN"
    assert disc_items[1]["severity"] == "HIGH"
    assert disc_items[1]["status"] == "OPEN"
    assert disc_items[2]["status"] == "RESOLVED"


def test_get_bid_submission_dashboard_no_sensitive_leakage(client_officer, complete_bid_fixture):
    submission_id, _ = complete_bid_fixture
    response = client_officer.get(f"/dashboard/bid-submissions/{submission_id}")
    assert response.status_code == 200
    raw_text = response.text

    # Assert sensitive internals/storage paths/hashed passwords do not leak in response
    assert "hashed_password" not in raw_text
    assert "file_path" not in raw_text
    assert "secret" not in raw_text
    assert "api_key" not in raw_text


def test_get_tender_dashboard_success(client_officer, complete_bid_fixture):
    _, tender_id = complete_bid_fixture
    response = client_officer.get(f"/dashboard/tenders/{tender_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["tender"]["id"] == tender_id
    assert data["summary"]["total_bids"] >= 1
    assert data["summary"]["qualified_count"] >= 1
    assert len(data["bids"]) >= 1
    assert data["bids"][0]["final_decision"] == "QUALIFIED"


def test_get_tender_dashboard_404_not_found(client_officer):
    response = client_officer.get("/dashboard/tenders/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
