import uuid
from datetime import datetime, timezone
import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_submission import BidSubmission
from app.models.compliance_check import ComplianceCheck
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.compliance_assessment_service import compliance_assessment_service
from app.services.recommendation_service import recommendation_service
from app.services.procurement_decision_service import procurement_decision_service
from app.schemas.procurement_decision import (
    ProcurementDecisionCreate,
    ProcurementDecisionValue,
)
from app.api.dependencies import get_current_user


def create_mock_user(role="PROCUREMENT_OFFICER", user_id=1):
    return User(
        id=user_id,
        full_name="Test Officer",
        email=f"officer_{user_id}@test.com",
        hashed_password="mock_hashed_password",
        role=role,
        is_active=True,
    )


@pytest.fixture
def client_officer():
    app.dependency_overrides[get_current_user] = lambda: create_mock_user("PROCUREMENT_OFFICER", 1)
    c = TestClient(app)
    yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client_unauthorized():
    app.dependency_overrides[get_current_user] = lambda: create_mock_user("BIDDER", 2)
    c = TestClient(app)
    yield c
    app.dependency_overrides.pop(get_current_user, None)


def create_decision_test_fixture(db, check_statuses):
    uid = uuid.uuid4().hex[:8].upper()
    bidder = Bidder(
        company_name=f"Decision Co {uid}",
        gstin=f"27DEC{uid[:4]}1Z5",
        pan=f"P{uid[:8]}",
    )
    tender = Tender(
        title=f"Decision Tender {uid}",
        reference_number=f"DEC-REF-{uid}",
        status="ACTIVE",
    )
    db.add_all([bidder, tender])
    db.commit()

    submission = BidSubmission(
        tender_id=tender.id,
        bidder_id=bidder.id,
        status="SUBMITTED",
    )
    db.add(submission)
    db.commit()

    for idx, st in enumerate(check_statuses, start=1):
        req = TenderRequirement(
            tender_id=tender.id,
            requirement_type=f"REQ_{idx}",
            requirement_name=f"Requirement {idx}",
            is_required=True,
        )
        db.add(req)
        db.commit()

        check = ComplianceCheck(
            bid_submission_id=submission.id,
            tender_requirement_id=req.id,
            status=st,
            reason=f"Status: {st}",
            checked_by="TEST",
        )
        db.add(check)

    db.commit()

    compliance_assessment_service.assess_submission(db, submission.id)
    recommendation_service.client = None  # Ensure fast rule engine execution
    recommendation_service.generate_recommendation(db, submission.id)

    return bidder, tender, submission


# --------------------------------------------------
# 1 & 2. QUALIFIED & DISQUALIFIED CREATION
# --------------------------------------------------
def test_record_qualified_decision_success():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 10)
        db.merge(user)
        db.commit()

        _, _, sub = create_decision_test_fixture(db, ["PASS", "PASS"])
        decision_data = ProcurementDecisionCreate(
            decision=ProcurementDecisionValue.QUALIFIED,
            reason="All mandatory requirements verified and evidence reviewed thoroughly.",
        )

        res = procurement_decision_service.record_decision(db, user, sub.id, decision_data)

        assert res.id is not None
        assert res.bid_submission_id == sub.id
        assert res.decision == "QUALIFIED"
        assert res.decided_by == 10
        assert res.is_override is False
    finally:
        db.close()


def test_record_disqualified_decision_success():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 11)
        db.merge(user)
        db.commit()

        _, _, sub = create_decision_test_fixture(db, ["PASS", "FAIL"])
        decision_data = ProcurementDecisionCreate(
            decision=ProcurementDecisionValue.DISQUALIFIED,
            reason="Mandatory requirement failed statutory compliance verification.",
        )

        res = procurement_decision_service.record_decision(db, user, sub.id, decision_data)

        assert res.decision == "DISQUALIFIED"
        assert res.decided_by == 11
        assert res.is_override is False
    finally:
        db.close()


# --------------------------------------------------
# 3 & 4. REASON VALIDATION & INVALID VALUES
# --------------------------------------------------
def test_missing_or_empty_reason_rejected():
    with pytest.raises(ValueError):
        ProcurementDecisionCreate(
            decision=ProcurementDecisionValue.QUALIFIED,
            reason="",
        )

    with pytest.raises(ValueError):
        ProcurementDecisionCreate(
            decision=ProcurementDecisionValue.QUALIFIED,
            reason="   short   ",
        )


# --------------------------------------------------
# 5. IMMUTABILITY & CONCURRENCY CONFLIC (HTTP 409)
# --------------------------------------------------
def test_duplicate_decision_rejected_immutable():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 12)
        db.merge(user)
        db.commit()

        _, _, sub = create_decision_test_fixture(db, ["PASS", "PASS"])
        decision_data1 = ProcurementDecisionCreate(
            decision=ProcurementDecisionValue.QUALIFIED,
            reason="First decision recorded by officer.",
        )
        procurement_decision_service.record_decision(db, user, sub.id, decision_data1)

        decision_data2 = ProcurementDecisionCreate(
            decision=ProcurementDecisionValue.DISQUALIFIED,
            reason="Attempting second conflicting decision.",
        )

        with pytest.raises(ValueError, match="already been recorded"):
            procurement_decision_service.record_decision(db, user, sub.id, decision_data2)
    finally:
        db.close()


# --------------------------------------------------
# 8. OVERRIDE TRACKING TESTS (CASES A-E)
# --------------------------------------------------
def test_override_case_a_proceed_and_qualified():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 13)
        db.merge(user)
        db.commit()

        _, _, sub = create_decision_test_fixture(db, ["PASS", "PASS"])
        decision = procurement_decision_service.record_decision(
            db, user, sub.id, ProcurementDecisionCreate(decision=ProcurementDecisionValue.QUALIFIED, reason="Fully satisfied with bidder documentation.")
        )
        assert decision.is_override is False
    finally:
        db.close()


def test_override_case_b_proceed_and_disqualified():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 14)
        db.merge(user)
        db.commit()

        _, _, sub = create_decision_test_fixture(db, ["PASS", "PASS"])
        decision = procurement_decision_service.record_decision(
            db, user, sub.id, ProcurementDecisionCreate(decision=ProcurementDecisionValue.DISQUALIFIED, reason="Officer exercised discretion due to past performance issues.")
        )
        assert decision.is_override is True
    finally:
        db.close()


def test_override_case_c_do_not_recommend_and_qualified():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 15)
        db.merge(user)
        db.commit()

        _, _, sub = create_decision_test_fixture(db, ["FAIL"])
        decision = procurement_decision_service.record_decision(
            db, user, sub.id, ProcurementDecisionCreate(decision=ProcurementDecisionValue.QUALIFIED, reason="Officer granted exemption under tender clause 4.2.")
        )
        assert decision.is_override is True
    finally:
        db.close()


def test_override_case_d_do_not_recommend_and_disqualified():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 16)
        db.merge(user)
        db.commit()

        _, _, sub = create_decision_test_fixture(db, ["FAIL"])
        decision = procurement_decision_service.record_decision(
            db, user, sub.id, ProcurementDecisionCreate(decision=ProcurementDecisionValue.DISQUALIFIED, reason="Disqualified due to mandatory requirement failure.")
        )
        assert decision.is_override is False
    finally:
        db.close()


def test_override_case_e_review_required_and_qualified():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 17)
        db.merge(user)
        db.commit()

        _, _, sub = create_decision_test_fixture(db, ["REVIEW"])
        decision = procurement_decision_service.record_decision(
            db, user, sub.id, ProcurementDecisionCreate(decision=ProcurementDecisionValue.QUALIFIED, reason="Manually verified physical documents presented by bidder.")
        )
        assert decision.is_override is True
    finally:
        db.close()


# --------------------------------------------------
# 9. INDEPENDENCE FROM COMPLIANCE ENGINE
# --------------------------------------------------
def test_decision_does_not_mutate_compliance_assessment():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 18)
        db.merge(user)
        db.commit()

        _, _, sub = create_decision_test_fixture(db, ["FAIL"])
        ass_before = compliance_assessment_service.assess_submission(db, sub.id)
        assert ass_before.status == "NON_COMPLIANT"
        score_before = ass_before.score

        procurement_decision_service.record_decision(
            db, user, sub.id, ProcurementDecisionCreate(decision=ProcurementDecisionValue.QUALIFIED, reason="Officer qualification override.")
        )

        ass_after = compliance_assessment_service.assess_submission(db, sub.id)
        assert ass_after.status == "NON_COMPLIANT"
        assert ass_after.score == score_before
    finally:
        db.close()


# --------------------------------------------------
# 10. AUDIT TRAIL LOGGING
# --------------------------------------------------
def test_decision_creates_audit_log_entry():
    db = SessionLocal()
    try:
        user = create_mock_user("PROCUREMENT_OFFICER", 19)
        db.merge(user)
        db.commit()

        _, _, sub = create_decision_test_fixture(db, ["PASS"])
        decision = procurement_decision_service.record_decision(
            db, user, sub.id, ProcurementDecisionCreate(decision=ProcurementDecisionValue.QUALIFIED, reason="Audit trail test decision justification.")
        )

        audit_entry = (
            db.query(AuditLog)
            .filter(
                AuditLog.bid_submission_id == sub.id,
                AuditLog.action == "PROCUREMENT_DECISION_CREATED",
            )
            .first()
        )
        assert audit_entry is not None
        assert audit_entry.entity_id == decision.id
        assert audit_entry.user_id == user.id
        assert audit_entry.new_value["decision"] == "QUALIFIED"
    finally:
        db.close()


# --------------------------------------------------
# API ENDPOINT TESTS & RBAC
# --------------------------------------------------
def test_api_record_decision_authorized(client_officer):
    db = SessionLocal()
    try:
        _, _, sub = create_decision_test_fixture(db, ["PASS"])
        resp = client_officer.post(
            f"/bid-submissions/{sub.id}/decision",
            json={
                "decision": "QUALIFIED",
                "reason": "Official procurement officer qualification approval.",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["bid_submission_id"] == sub.id
        assert data["decision"] == "QUALIFIED"

        # Duplicate attempt fails with 409 Conflict
        resp_dup = client_officer.post(
            f"/bid-submissions/{sub.id}/decision",
            json={
                "decision": "DISQUALIFIED",
                "reason": "Duplicate attempt should be rejected.",
            },
        )
        assert resp_dup.status_code == 409
    finally:
        db.close()


def test_api_record_decision_unauthorized(client_unauthorized):
    db = SessionLocal()
    try:
        _, _, sub = create_decision_test_fixture(db, ["PASS"])
        resp = client_unauthorized.post(
            f"/bid-submissions/{sub.id}/decision",
            json={
                "decision": "QUALIFIED",
                "reason": "Bidder attempting self-qualification.",
            },
        )
        assert resp.status_code == 403
    finally:
        db.close()


def test_api_get_decision(client_officer):
    db = SessionLocal()
    try:
        _, _, sub = create_decision_test_fixture(db, ["PASS"])
        client_officer.post(
            f"/bid-submissions/{sub.id}/decision",
            json={
                "decision": "QUALIFIED",
                "reason": "Pre-retrieval decision recording.",
            },
        )

        resp = client_officer.get(f"/bid-submissions/{sub.id}/decision")
        assert resp.status_code == 200
        data = resp.json()
        assert data["bid_submission_id"] == sub.id
        assert data["decision"] == "QUALIFIED"
    finally:
        db.close()
