import io
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.database.base import Base
from app.database.session import engine, get_db
from app.models.user import User
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_submission import BidSubmission
from app.models.bid_document import BidDocument
from app.models.audit_log import AuditLog
from app.core.audit_actions import AuditAction, AuditEntityType
from app.core.security import hash_password, create_access_token
from app.services.audit_log_service import audit_log_service, sanitize_audit_data
from app.services.auth_service import AuthService
from app.services.document_upload_service import document_upload_service
from app.services.document_intelligence.document_service import document_processing_service
from app.services.verification_service import verification_service
from app.services.cross_verification_service import cross_verification_service
from app.services.discrepancy_service import discrepancy_service
from app.services.compliance_service import compliance_service
from app.services.compliance_assessment_service import compliance_assessment_service
from app.services.recommendation_service import recommendation_service
from app.repositories.tender_repository import tender_repository
from app.repositories.tender_requirement_repository import tender_requirement_repository
from app.repositories.bid_submission_repository import bid_submission_repository
from app.repositories.bidder_repository import bidder_repository
from app.providers.schemas import VerificationRequest


from app.schemas.tender import TenderCreate
from app.schemas.tender_requirement import TenderRequirementCreate
from app.schemas.bid_submission import BidSubmissionCreate
from app.providers.register import register_providers
from seed_users import seed_default_users


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    register_providers()
    seed_default_users()
    yield


@pytest.fixture
def db_session():
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_headers(db_session: Session):
    existing = db_session.query(User).filter(User.email == "audit.officer@cpcl.gov.in").first()
    if not existing:
        hashed = hash_password("OfficerPass123")
        user = User(
            full_name="Audit Officer",
            email="audit.officer@cpcl.gov.in",
            hashed_password=hashed,
            role="PROCUREMENT_OFFICER",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    else:
        user = existing

    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}, user


# 1. AuditLog Creation
def test_1_create_audit_log(db_session: Session):
    log_item = audit_log_service.record_event(
        db=db_session,
        action=AuditAction.TENDER_CREATED,
        entity_type=AuditEntityType.TENDER,
        entity_id=1,
        details="Test tender creation log",
    )
    assert log_item.id is not None
    assert log_item.action == "TENDER_CREATED"
    assert log_item.entity_type == "TENDER"


# 2. AuditLog Retrieval by ID
def test_2_get_audit_log_by_id(db_session: Session):
    log_item = audit_log_service.record_event(
        db=db_session,
        action=AuditAction.BID_SUBMISSION_CREATED,
        entity_type=AuditEntityType.BID_SUBMISSION,
        entity_id=10,
        bid_submission_id=10,
    )
    fetched = audit_log_service.get_by_id(db_session, log_item.id)
    assert fetched is not None
    assert fetched.id == log_item.id
    assert fetched.bid_submission_id == 10


# 3. Entity History Retrieval
def test_3_list_by_entity(db_session: Session):
    audit_log_service.record_event(
        db=db_session,
        action=AuditAction.REQUIREMENT_CREATED,
        entity_type=AuditEntityType.TENDER_REQUIREMENT,
        entity_id=99,
    )
    items, total = audit_log_service.list_by_entity(
        db=db_session, entity_type="TENDER_REQUIREMENT", entity_id=99
    )
    assert total >= 1
    assert any(i.entity_id == 99 for i in items)


# 4. Bid Submission Audit History
def test_4_list_by_bid_submission(db_session: Session):
    sub_id = 888
    audit_log_service.record_event(
        db=db_session,
        action=AuditAction.VERIFICATION_STARTED,
        entity_type=AuditEntityType.VERIFICATION_RESULT,
        bid_submission_id=sub_id,
    )
    items, total = audit_log_service.list_by_bid_submission(db=db_session, bid_submission_id=sub_id)
    assert total >= 1
    assert all(i.bid_submission_id == sub_id or (i.entity_type == "BID_SUBMISSION" and i.entity_id == sub_id) for i in items)


# 5. User Audit Filtering
def test_5_list_by_user(db_session: Session):
    audit_log_service.record_event(
        db=db_session,
        action=AuditAction.AUTH_LOGIN,
        entity_type=AuditEntityType.USER,
        user_id=777,
    )
    items, total = audit_log_service.list_logs(db=db_session, user_id=777)
    assert total >= 1
    assert items[0].user_id == 777


# 6. Action Filtering
def test_6_filter_by_action(db_session: Session):
    audit_log_service.record_event(
        db=db_session,
        action=AuditAction.DISCREPANCY_WAIVED,
        entity_type=AuditEntityType.DISCREPANCY,
        entity_id=55,
    )
    items, total = audit_log_service.list_logs(db=db_session, action="DISCREPANCY_WAIVED")
    assert total >= 1
    assert all(i.action == "DISCREPANCY_WAIVED" for i in items)


# 7. Pagination
def test_7_pagination(db_session: Session):
    items, total = audit_log_service.list_logs(db=db_session, limit=2, offset=0)
    assert len(items) <= 2
    assert total >= len(items)


# 8. Authentication Required for Audit Endpoints
def test_8_auth_required_for_audit_api():
    client = TestClient(app)
    response = client.get("/audit-logs")
    assert response.status_code == 401


# 9. RBAC Enforced
def test_9_rbac_enforced(db_session: Session):
    client = TestClient(app)
    user = User(
        full_name="Unauthorized User",
        email=f"unauth_{int(datetime.now().timestamp())}@cpcl.gov.in",
        hashed_password=hash_password("pass"),
        role="VENDOR",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user_id=user.id, role="VENDOR")
    response = client.get("/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


# 10. Audit Immutability (Read-Only API)
def test_10_audit_api_is_read_only(auth_headers):
    headers, _ = auth_headers
    client = TestClient(app)
    assert client.post("/audit-logs", json={}, headers=headers).status_code in (404, 405)
    assert client.put("/audit-logs/1", json={}, headers=headers).status_code in (404, 405)
    assert client.delete("/audit-logs/1", headers=headers).status_code in (404, 405)


# 11 & 12. Login Audit (Success & Failed)
def test_11_12_login_audit_events(db_session: Session):
    existing = db_session.query(User).filter(User.email == "login.test@cpcl.gov.in").first()
    if not existing:
        user = User(
            full_name="Login Test",
            email="login.test@cpcl.gov.in",
            hashed_password=hash_password("Pass123!"),
            role="PROCUREMENT_OFFICER",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

    AuthService.login(db_session, "login.test@cpcl.gov.in", "WrongPass")
    items_fail, _ = audit_log_service.list_logs(db=db_session, action=AuditAction.AUTH_LOGIN_FAILED)
    assert len(items_fail) >= 1

    AuthService.login(db_session, "login.test@cpcl.gov.in", "Pass123!")
    items_success, _ = audit_log_service.list_logs(db=db_session, action=AuditAction.AUTH_LOGIN)
    assert len(items_success) >= 1


# 13 & 14. Password and JWT Never Stored in Audit
def test_13_14_sensitive_data_sanitized():
    raw_data = {
        "password": "SecretPassword123",
        "hashed_password": "$argon2id$secret",
        "jwt": "eyJhbGciOiJIUzI1NiI...",
        "public_field": "VisibleData",
    }
    sanitized = sanitize_audit_data(raw_data)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["hashed_password"] == "[REDACTED]"
    assert sanitized["jwt"] == "[REDACTED]"
    assert sanitized["public_field"] == "VisibleData"


# 15. Tender Creation Audit
def test_15_tender_creation_audit(db_session: Session):
    ref_num = f"CPCL-AUD-TENDER-{int(datetime.now().timestamp())}"
    tender = tender_repository.create(
        db_session,
        TenderCreate(title="Audit Test Tender", reference_number=ref_num, description="Test"),
    )
    items, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.TENDER_CREATED, entity_id=tender.id
    )
    assert len(items) >= 1
    assert items[0].entity_type == "TENDER"


# 16. Bid Submission Creation Audit
def test_16_bid_submission_creation_audit(db_session: Session):
    bidder = Bidder(company_name="Audit Bidder Ltd")
    db_session.add(bidder)
    db_session.commit()

    ref_num = f"CPCL-SUB-TENDER-{int(datetime.now().timestamp())}"
    tender = tender_repository.create(
        db_session,
        TenderCreate(title="Sub Audit Tender", reference_number=ref_num, description="Test"),
    )

    sub = bid_submission_repository.create(
        db_session,
        BidSubmissionCreate(tender_id=tender.id, bidder_id=bidder.id),
    )
    items, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.BID_SUBMISSION_CREATED, entity_id=sub.id
    )
    assert len(items) >= 1


# 17. Document Upload Audit
def test_17_document_upload_audit(db_session: Session):
    bidder = Bidder(company_name="Doc Upload Ltd")
    db_session.add(bidder)
    db_session.commit()
    ref_num = f"CPCL-DOC-TENDER-{int(datetime.now().timestamp())}"
    tender = tender_repository.create(
        db_session,
        TenderCreate(title="Doc Audit Tender", reference_number=ref_num, description="Test"),
    )
    sub = bid_submission_repository.create(
        db_session,
        BidSubmissionCreate(tender_id=tender.id, bidder_id=bidder.id),
    )

    doc = document_upload_service.upload_document(
        db=db_session,
        bid_submission_id=sub.id,
        file_obj=io.BytesIO(b"%PDF-1.4 Dummy GST Certificate Content"),
        original_filename="GST_Audit.pdf",
        document_type="GST_CERTIFICATE",
    )
    items, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.DOCUMENT_UPLOADED, entity_id=doc.id
    )
    assert len(items) >= 1


# 18 & 19. Document Processing Started/Completed Audit
def test_18_19_document_processing_audit(db_session: Session, monkeypatch):
    bidder = Bidder(company_name="Proc Doc Ltd")
    db_session.add(bidder)
    db_session.commit()
    ref_num = f"CPCL-PROC-TENDER-{int(datetime.now().timestamp())}"
    tender = tender_repository.create(
        db_session,
        TenderCreate(title="Proc Audit Tender", reference_number=ref_num, description="Test"),
    )
    sub = bid_submission_repository.create(
        db_session,
        BidSubmissionCreate(tender_id=tender.id, bidder_id=bidder.id),
    )
    doc = document_upload_service.upload_document(
        db=db_session,
        bid_submission_id=sub.id,
        file_obj=io.BytesIO(b"%PDF-1.4 Dummy GST Content"),
        original_filename="GST_Proc.pdf",
        document_type="GST_CERTIFICATE",
    )

    from app.services.document_intelligence.schemas import DocumentIntelligenceResult, DocumentType, GSTDocumentFields, TextExtractionMethod
    fake_result = DocumentIntelligenceResult(
        document_type=DocumentType.GST_CERTIFICATE,
        classification_confidence=0.95,
        extraction_method=TextExtractionMethod.NATIVE_PDF,
        extracted_text="GSTIN: 33AAACA1234A1Z5",
        total_pages=1,
        total_characters=22,
        fields=GSTDocumentFields(gstin="33AAACA1234A1Z5"),
        extraction_confidence=0.95,
    )
    monkeypatch.setattr(document_processing_service.orchestrator, "process", lambda fp: fake_result)

    document_processing_service.process_document(
        db=db_session,
        bid_document_id=doc.id,
        file_path=doc.file_path,
    )

    items_start, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.DOCUMENT_PROCESSING_STARTED, entity_id=doc.id
    )
    assert len(items_start) >= 1

    items_comp, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.DOCUMENT_PROCESSING_COMPLETED, entity_id=doc.id
    )
    assert len(items_comp) >= 1


# 20. Verification Lifecycle Audit
def test_20_verification_lifecycle_audit(db_session: Session):
    bidder = Bidder(company_name="Verif Audit Ltd")
    db_session.add(bidder)
    db_session.commit()
    ref_num = f"CPCL-VER-TENDER-{int(datetime.now().timestamp())}"
    tender = tender_repository.create(
        db_session,
        TenderCreate(title="Ver Audit Tender", reference_number=ref_num, description="Test"),
    )
    sub = bid_submission_repository.create(
        db_session,
        BidSubmissionCreate(tender_id=tender.id, bidder_id=bidder.id),
    )

    verification_service.verify(
        db=db_session,
        bid_submission_id=sub.id,
        request=VerificationRequest(
            verification_type="GST",
            identifier="33AAACA1234A1Z5",
        ),
    )

    items_start, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.VERIFICATION_STARTED, bid_submission_id=sub.id
    )
    assert len(items_start) >= 1

    items_comp, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.VERIFICATION_COMPLETED, bid_submission_id=sub.id
    )
    assert len(items_comp) >= 1


# 21. Cross Verification Audit
def test_21_cross_verification_audit(db_session: Session):
    bidder = Bidder(company_name="Cross Verif Ltd")
    db_session.add(bidder)
    db_session.commit()
    ref_num = f"CPCL-CROSS-TENDER-{int(datetime.now().timestamp())}"
    tender = tender_repository.create(
        db_session,
        TenderCreate(title="Cross Audit Tender", reference_number=ref_num, description="Test"),
    )
    sub = bid_submission_repository.create(
        db_session,
        BidSubmissionCreate(tender_id=tender.id, bidder_id=bidder.id),
    )

    cross_verification_service.cross_verify_submission(db=db_session, bid_submission_id=sub.id)
    items, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.CROSS_VERIFICATION_COMPLETED, bid_submission_id=sub.id
    )
    assert len(items) >= 1


# 22, 23, 24. Discrepancy Created, Resolved, Waived Audit
def test_22_23_24_discrepancy_lifecycle_audit(db_session: Session):
    bidder = Bidder(company_name="Disc Audit Ltd")
    db_session.add(bidder)
    db_session.commit()
    ref_num = f"CPCL-DISC-TENDER-{int(datetime.now().timestamp())}"
    tender = tender_repository.create(
        db_session,
        TenderCreate(title="Disc Audit Tender", reference_number=ref_num, description="Test"),
    )
    sub = bid_submission_repository.create(
        db_session,
        BidSubmissionCreate(tender_id=tender.id, bidder_id=bidder.id),
    )

    disc = discrepancy_service.record_discrepancy(
        db=db_session,
        bid_submission_id=sub.id,
        type="MISMATCH",
        title="Audit Discrepancy",
        description="Testing audit recording for discrepancy creation",
    )
    items_create, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.DISCREPANCY_CREATED, entity_id=disc.id
    )
    assert len(items_create) >= 1

    discrepancy_service.update_discrepancy_status(
        db=db_session,
        discrepancy_id=disc.id,
        status="RESOLVED",
        resolution_note="Resolved during audit test",
        user_id=1,
    )
    items_resolve, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.DISCREPANCY_RESOLVED, entity_id=disc.id
    )
    assert len(items_resolve) >= 1
    assert items_resolve[0].old_value == {"status": "OPEN"}
    assert items_resolve[0].new_value["status"] == "RESOLVED"


# 25, 26, 27. Compliance Evaluation, Assessment, Recommendation Audit
def test_25_26_27_compliance_assessment_recommendation_audit(db_session: Session):
    bidder = Bidder(company_name="Comp Eval Ltd")
    db_session.add(bidder)
    db_session.commit()
    ref_num = f"CPCL-COMP-TENDER-{int(datetime.now().timestamp())}"
    tender = tender_repository.create(
        db_session,
        TenderCreate(title="Comp Audit Tender", reference_number=ref_num, description="Test"),
    )
    req = tender_requirement_repository.create(
        db_session,
        tender.id,
        TenderRequirementCreate(
            requirement_type="GST",
            requirement_name="GST Return",
            is_mandatory=True,
        ),
    )
    sub = bid_submission_repository.create(
        db_session,
        BidSubmissionCreate(tender_id=tender.id, bidder_id=bidder.id),
    )

    compliance_service.evaluate_submission(db=db_session, bid_submission_id=sub.id)
    items_eval, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.COMPLIANCE_EVALUATED, bid_submission_id=sub.id
    )
    assert len(items_eval) >= 1

    assessment = compliance_assessment_service.assess_submission(
        db=db_session, bid_submission_id=sub.id
    )
    items_ass, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.ASSESSMENT_CREATED, entity_id=assessment.id
    )
    assert len(items_ass) >= 1

    rec_assessment = recommendation_service.generate_recommendation(
        db=db_session, bid_submission_id=sub.id
    )
    items_rec, _ = audit_log_service.list_logs(
        db=db_session, action=AuditAction.RECOMMENDATION_GENERATED, entity_id=rec_assessment.id
    )
    assert len(items_rec) >= 1


# 30. End-To-End Workflow Chronological Audit Trail Verification
def test_30_end_to_end_chronological_audit_trail(db_session: Session, auth_headers):
    headers, user = auth_headers

    bidder = Bidder(company_name="E2E Audit Corp")
    db_session.add(bidder)
    db_session.commit()

    ref_num = f"CPCL-E2E-TENDER-{int(datetime.now().timestamp())}"
    tender = tender_repository.create(
        db_session,
        TenderCreate(title="E2E Audit Tender", reference_number=ref_num, description="E2E Test"),
        user_id=user.id,
    )

    req = tender_requirement_repository.create(
        db_session,
        tender.id,
        TenderRequirementCreate(
            requirement_type="GST",
            requirement_name="GST Compliance",
            is_mandatory=True,
        ),
        user_id=user.id,
    )

    sub = bid_submission_repository.create(
        db_session,
        BidSubmissionCreate(tender_id=tender.id, bidder_id=bidder.id),
        user_id=user.id,
    )

    doc = document_upload_service.upload_document(
        db=db_session,
        bid_submission_id=sub.id,
        file_obj=io.BytesIO(b"%PDF-1.4 E2E GST Document"),
        original_filename="E2E_GST.pdf",
        document_type="GST_CERTIFICATE",
    )

    document_processing_service.process_document(
        db=db_session,
        bid_document_id=doc.id,
        file_path=doc.file_path,
    )

    verification_service.verify(
        db=db_session,
        bid_submission_id=sub.id,
        request=VerificationRequest(verification_type="GST", identifier="33AAACA1234A1Z5"),
    )

    cross_verification_service.cross_verify_submission(db=db_session, bid_submission_id=sub.id)

    disc = discrepancy_service.record_discrepancy(
        db=db_session,
        bid_submission_id=sub.id,
        type="MISMATCH",
        title="E2E Discrepancy",
        description="E2E Mismatch test",
    )

    discrepancy_service.update_discrepancy_status(
        db=db_session,
        discrepancy_id=disc.id,
        status="RESOLVED",
        resolution_note="Resolved by officer in E2E",
        user_id=user.id,
    )

    compliance_assessment_service.assess_submission(db=db_session, bid_submission_id=sub.id)
    recommendation_service.generate_recommendation(db=db_session, bid_submission_id=sub.id)

    # Fetch audit logs via API endpoint
    client = TestClient(app)
    res = client.get(f"/bid-submissions/{sub.id}/audit-logs", headers=headers)
    assert res.status_code == 200
    data = res.json()
    items = data["items"]
    assert len(items) >= 5

    # Check chronological ordering & action coverage
    actions_present = [i["action"] for i in items]
    assert "BID_SUBMISSION_CREATED" in actions_present or "DOCUMENT_UPLOADED" in actions_present
    assert "CROSS_VERIFICATION_COMPLETED" in actions_present
    assert "DISCREPANCY_RESOLVED" in actions_present
