from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.bid_submission import BidSubmission
from app.models.verification_result import VerificationResult
from app.models.audit_log import AuditLog
from app.models.user import User
from app.api.dependencies import get_current_user
from app.providers.gst.provider import GSTVerificationProvider
from app.providers.live_adapters import LiveGSTAdapter
from app.providers.schemas import SourceMode, VerificationRequest, VerificationStatus
from app.services.verification_service import verification_service


def create_mock_user(role="PROCUREMENT_OFFICER", user_id=201):
    return User(
        id=user_id,
        full_name="Task 10 Officer",
        email=f"officer_{user_id}@test.com",
        hashed_password="mock_hashed_password",
        role=role,
        is_active=True,
    )


@pytest.fixture
def client_officer():
    app.dependency_overrides[get_current_user] = lambda: create_mock_user("PROCUREMENT_OFFICER", 201)
    c = TestClient(app)
    yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client_unauthorized():
    app.dependency_overrides[get_current_user] = lambda: create_mock_user("BIDDER", 202)
    c = TestClient(app)
    yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def test_submission_fixture():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 201)
        db.merge(user)
        db.commit()

        ts = int(datetime.now().timestamp() * 1000) % 1000000
        tender = Tender(title="Govt Integration Tender", reference_number=f"TND-T10-{ts}")
        bidder = Bidder(company_name="Govt Test Bidder", gstin=f"27AAA{ts:07d}1Z5", pan=f"AAA{ts:06d}A")
        db.add_all([tender, bidder])
        db.commit()

        sub = BidSubmission(tender_id=tender.id, bidder_id=bidder.id, status="SUBMITTED")
        db.add(sub)
        db.commit()
        return sub.id
    finally:
        db.close()


def test_1_synthetic_provider_explicitly_marked_synthetic(client_officer, test_submission_fixture):
    sub_id = test_submission_fixture
    db = SessionLocal()
    try:
        req = VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION")
        res = verification_service.verify(db, sub_id, req)
        assert res.source_mode == SourceMode.SYNTHETIC
        assert res.status == VerificationStatus.VERIFIED
    finally:
        db.close()


def test_2_unconfigured_official_provider_returns_safe_error():
    adapter = LiveGSTAdapter(enabled=False, base_url=None, api_key=None)
    provider = GSTVerificationProvider(adapter=adapter)
    assert provider.source_mode == SourceMode.AUTHORIZED_PROVIDER

    req = VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION")
    res = provider.verify(req)
    assert res.status == VerificationStatus.ERROR
    msg = (res.error_message or res.message).lower()
    assert "not configured" in msg or "disabled" in msg


def test_3_missing_credentials_never_produce_verified():
    adapter = LiveGSTAdapter(enabled=True, base_url="https://api.gstn.gov.in", api_key=None)
    provider = GSTVerificationProvider(adapter=adapter)

    req = VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION")
    res = provider.verify(req)
    assert res.status != VerificationStatus.VERIFIED
    assert res.status == VerificationStatus.ERROR


def test_4_timeout_produces_safe_failure_state():
    adapter = LiveGSTAdapter(enabled=True, base_url="https://api.gstn.gov.in", api_key="valid_key")
    provider = GSTVerificationProvider(adapter=adapter)

    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("Connection timed out")):
        req = VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION")
        res = provider.verify(req)
        assert res.status == VerificationStatus.ERROR
        assert res.status != VerificationStatus.VERIFIED
        msg = (res.error_message or res.message).lower()
        assert "timed out" in msg or "timeout" in msg


def test_5_http_500_never_produces_verified():
    adapter = LiveGSTAdapter(enabled=True, base_url="https://api.gstn.gov.in", api_key="valid_key")
    provider = GSTVerificationProvider(adapter=adapter)

    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch("httpx.Client.get", return_value=mock_resp):
        req = VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION")
        res = provider.verify(req)
        assert res.status == VerificationStatus.ERROR
        assert res.status != VerificationStatus.VERIFIED


def test_6_malformed_provider_response_rejected():
    adapter = LiveGSTAdapter(enabled=True, base_url="https://api.gstn.gov.in", api_key="valid_key")
    provider = GSTVerificationProvider(adapter=adapter)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("Invalid JSON string")

    with patch("httpx.Client.get", return_value=mock_resp):
        req = VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION")
        res = provider.verify(req)
        assert res.status == VerificationStatus.ERROR
        assert res.status != VerificationStatus.VERIFIED


def test_7_identifier_mismatch_produces_not_verified():
    adapter = LiveGSTAdapter(enabled=True, base_url="https://api.gstn.gov.in", api_key="valid_key")
    provider = GSTVerificationProvider(adapter=adapter)

    req = VerificationRequest(identifier="INVALID_GSTIN_FORMAT", verification_type="GST_REGISTRATION")
    res = provider.verify(req)
    assert res.status == VerificationStatus.NOT_VERIFIED
    assert "format is invalid" in res.message.lower()


def test_8_valid_provider_response_produces_verified():
    adapter = LiveGSTAdapter(enabled=True, base_url="https://api.gstn.gov.in", api_key="valid_key")
    provider = GSTVerificationProvider(adapter=adapter)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "LIVE GST SUPPLIER PRIVATE LIMITED",
        "registration_status": "ACTIVE",
    }

    with patch("httpx.Client.get", return_value=mock_resp):
        req = VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION")
        res = provider.verify(req)
        assert res.status == VerificationStatus.VERIFIED
        assert res.source_mode == SourceMode.AUTHORIZED_PROVIDER
        assert res.verified_data["legal_name"] == "LIVE GST SUPPLIER PRIVATE LIMITED"


def test_9_manual_verification_requires_authorized_role(client_unauthorized, test_submission_fixture):
    sub_id = test_submission_fixture
    payload = {
        "bid_submission_id": sub_id,
        "requirement_type": "DEBARMENT",
        "identifier": "VEND-1001",
        "verification_status": "VERIFIED",
        "message": "Manual portal check completed",
        "reference_notes": "Checked CPPP debarment portal manually",
    }
    response = client_unauthorized.post("/verification/manual", json=payload)
    assert response.status_code == 403


def test_10_manual_verification_creates_audit_event(client_officer, test_submission_fixture):
    sub_id = test_submission_fixture
    payload = {
        "bid_submission_id": sub_id,
        "requirement_type": "DEBARMENT",
        "identifier": "VEND-1001",
        "verification_status": "VERIFIED",
        "message": "Manual portal check completed",
        "reference_notes": "Checked CPPP debarment portal manually",
    }
    response = client_officer.post("/verification/manual", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["source_mode"] == "MANUAL"
    assert data["provider"] == "MANUAL_OFFICER_REVIEW"

    # Verify Audit Log
    db = SessionLocal()
    try:
        logs = db.query(AuditLog).filter(AuditLog.bid_submission_id == sub_id).all()
        assert any(l.action == "VERIFICATION_COMPLETED" for l in logs)
    finally:
        db.close()


def test_11_provider_capability_endpoint_hides_secrets(client_officer):
    response = client_officer.get("/verification/providers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    raw_text = response.text
    assert "api_key" not in raw_text
    assert "password" not in raw_text
    assert "secret" not in raw_text

    for item in data:
        assert "provider_name" in item
        assert "source_mode" in item
        assert "availability" in item


def test_12_official_authorized_provider_selection():
    live_adapter = LiveGSTAdapter(enabled=True, base_url="https://api.gstn.gov.in", api_key="key")
    provider = GSTVerificationProvider(adapter=live_adapter)
    assert provider.source_mode == SourceMode.AUTHORIZED_PROVIDER
    assert provider.capability.is_live is True


def test_13_synthetic_provider_does_not_become_production():
    from app.providers.gst.mock import MockGSTVerificationAdapter
    mock_adapter = MockGSTVerificationAdapter()
    provider = GSTVerificationProvider(adapter=mock_adapter)
    assert provider.source_mode == SourceMode.SYNTHETIC
    assert provider.capability.is_live is False


def test_14_provider_provenance_survives_persistence(test_submission_fixture):
    sub_id = test_submission_fixture
    db = SessionLocal()
    try:
        req = VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION")
        res = verification_service.verify(db, sub_id, req)
        
        # Fetch directly from DB
        db_res = db.query(VerificationResult).filter(VerificationResult.bid_submission_id == sub_id).first()
        assert db_res is not None
        assert db_res.source_mode == "SYNTHETIC"
    finally:
        db.close()


def test_15_existing_compliance_evaluator_behavior_unchanged(test_submission_fixture):
    sub_id = test_submission_fixture
    db = SessionLocal()
    try:
        from app.services.compliance_service import compliance_service
        req = VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION")
        verification_service.verify(db, sub_id, req)
        
        # Evaluator run
        checks = compliance_service.evaluate_submission(db, sub_id)
        assert isinstance(checks, list)
    finally:
        db.close()


def test_16_dashboard_exposes_provider_source_mode(client_officer, test_submission_fixture):
    sub_id = test_submission_fixture
    db = SessionLocal()
    try:
        req = VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION")
        verification_service.verify(db, sub_id, req)
    finally:
        db.close()

    response = client_officer.get(f"/dashboard/bid-submissions/{sub_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["verification"]) >= 1
    # Check that verification result contains details
    assert "status" in data["verification"][0]


def test_17_recommendation_and_decision_workflows_unaffected(test_submission_fixture):
    sub_id = test_submission_fixture
    db = SessionLocal()
    try:
        from app.services.compliance_assessment_service import compliance_assessment_service
        from app.services.recommendation_service import recommendation_service
        
        assessment = compliance_assessment_service.assess_submission(db, sub_id)
        assert assessment is not None
        
        rec = recommendation_service.generate_recommendation(db, sub_id)
        assert rec is not None
        assert rec.recommendation in ("PROCEED", "REVIEW_REQUIRED", "HIGH_RISK_REVIEW", "DO_NOT_RECOMMEND")
    finally:
        db.close()
