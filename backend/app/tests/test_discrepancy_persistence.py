import uuid
import pytest
from app.database.session import SessionLocal
from app.models.discrepancy import Discrepancy, DiscrepancyStatus
from app.models.bid_submission import BidSubmission
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_document import BidDocument
from app.models.verification_result import VerificationResult

from app.repositories.discrepancy_repository import discrepancy_repository
from app.services.discrepancy_service import discrepancy_service
from app.services.cross_verification_service import cross_verification_service
from app.services.compliance_service import compliance_service
from app.services.end_to_end_verification_service import end_to_end_verification_service
from app.schemas.discrepancy import DiscrepancyCreate


@pytest.fixture
def test_setup():
    """Sets up an isolated test database environment for discrepancy persistence tests."""
    db = SessionLocal()
    unique_id = uuid.uuid4().hex[:8].upper()

    tender = Tender(
        reference_number=f"GEM/2026/B/{unique_id}",
        title=f"Procurement of Valves {unique_id}",
        description="Supply of industrial valves",
        status="ACTIVE",
    )

    db.add(tender)
    db.commit()
    db.refresh(tender)

    req_gst = TenderRequirement(
        tender_id=tender.id,
        requirement_name="GST Registration",
        requirement_type="GST",
        is_required=True,
    )
    req_epfo = TenderRequirement(
        tender_id=tender.id,
        requirement_name="EPFO Compliance",
        requirement_type="EPFO",
        is_required=True,
    )
    req_optional = TenderRequirement(
        tender_id=tender.id,
        requirement_name="Optional Certification",
        requirement_type="STARTUP_INDIA",
        is_required=False,
    )

    db.add_all([req_gst, req_epfo, req_optional])
    db.commit()
    db.refresh(req_gst)
    db.refresh(req_epfo)
    db.refresh(req_optional)

    bidder = Bidder(
        company_name=f"Apex Technologies {unique_id}",
        gstin=f"33{unique_id[:8]}A1Z5",
        pan=f"AAA{unique_id[:6]}A",
        udyam_number=f"UDYAM-TN-{unique_id}",
    )
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    submission = BidSubmission(
        tender_id=tender.id,
        bidder_id=bidder.id,
        status="SUBMITTED",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    doc_gst = BidDocument(
        bid_submission_id=submission.id,
        file_name="Gst_Cert.pdf",
        file_path="storage/documents/Gst_Cert.pdf",
        document_type="GST_CERTIFICATE",
    )
    db.add(doc_gst)
    db.commit()
    db.refresh(doc_gst)

    v_result = VerificationResult(
        bid_submission_id=submission.id,
        bid_document_id=doc_gst.id,
        provider="GstVerificationProvider",
        verification_type="GST_REGISTRATION",
        identifier=bidder.gstin,
        verification_status="VERIFIED",
        verified_data={"legal_name": bidder.company_name, "gstin": bidder.gstin},
    )
    db.add(v_result)
    db.commit()
    db.refresh(v_result)

    yield {
        "db": db,
        "tender": tender,
        "req_gst": req_gst,
        "req_epfo": req_epfo,
        "req_optional": req_optional,
        "bidder": bidder,
        "submission": submission,
        "doc_gst": doc_gst,
        "v_result": v_result,
    }

    # Teardown
    try:
        db.rollback()
        db.query(Discrepancy).filter(Discrepancy.bid_submission_id == submission.id).delete()
        db.query(VerificationResult).filter(VerificationResult.bid_submission_id == submission.id).delete()
        db.query(BidDocument).filter(BidDocument.bid_submission_id == submission.id).delete()
        db.query(BidSubmission).filter(BidSubmission.id == submission.id).delete()
        db.query(TenderRequirement).filter(TenderRequirement.tender_id == tender.id).delete()
        db.query(Tender).filter(Tender.id == tender.id).delete()
        db.query(Bidder).filter(Bidder.id == bidder.id).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def test_1_create_discrepancy(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    req = test_setup["req_gst"]

    create_data = DiscrepancyCreate(
        bid_submission_id=s.id,
        tender_requirement_id=req.id,
        type="GSTIN_MISMATCH",
        severity="HIGH",
        status="OPEN",
        title="GSTIN mismatch",
        description="Extracted GSTIN does not match portal data.",
        expected_value="33AAACA1234A1Z5",
        observed_value="33AAACA9999A1Z5",
        source="CROSS_VERIFICATION",
        evidence={"field": "gstin"},
        finding_key=f"key_123_{s.id}",
    )
    d = discrepancy_repository.create(db, create_data)
    assert d.id is not None
    assert d.bid_submission_id == s.id
    assert d.type == "GSTIN_MISMATCH"
    assert d.status == "OPEN"


def test_2_get_by_id(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    d = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        type="LEGAL_NAME_MISMATCH",
        title="Name Mismatch",
        description="Company name differs across sources.",
        finding_key=f"key_get_by_id_{s.id}",
    )
    found = discrepancy_service.get_by_id(db, d.id)
    assert found is not None
    assert found.id == d.id
    assert found.title == "Name Mismatch"


def test_3_list_for_submission(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        type="MISMATCH_1",
        title="Title 1",
        description="Desc 1",
        finding_key=f"key_list_1_{s.id}",
    )
    discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        type="MISMATCH_2",
        title="Title 2",
        description="Desc 2",
        finding_key=f"key_list_2_{s.id}",
    )
    res = discrepancy_service.get_discrepancies_for_submission(db, s.id)
    assert len(res) >= 2


def test_4_filter_open_discrepancies(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    d1 = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        type="OPEN_TYPE",
        title="Open Title",
        description="Open Desc",
        finding_key=f"key_open_1_{s.id}",
    )
    d2 = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        type="RESOLVED_TYPE",
        title="Resolved Title",
        description="Resolved Desc",
        finding_key=f"key_res_1_{s.id}",
    )
    discrepancy_service.update_discrepancy_status(db, d2.id, "RESOLVED", "Reviewed by officer")

    open_items = discrepancy_service.get_open_discrepancies_for_submission(db, s.id)
    open_ids = [d.id for d in open_items]
    assert d1.id in open_ids
    assert d2.id not in open_ids


def test_5_get_by_requirement(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    req = test_setup["req_gst"]
    d = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        tender_requirement_id=req.id,
        type="REQ_TYPE",
        title="Req Title",
        description="Req Desc",
        finding_key=f"key_req_1_{s.id}",
    )
    res = discrepancy_service.get_discrepancies_for_requirement(db, req.id)
    assert any(x.id == d.id for x in res)


def test_6_resolve_discrepancy(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    d = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        type="TEST_RESOLVE",
        title="Title",
        description="Desc",
        finding_key=f"key_resolve_{s.id}",
    )
    res = discrepancy_service.update_discrepancy_status(
        db=db, discrepancy_id=d.id, status="RESOLVED", resolution_note="Valid explanation provided"
    )
    assert res.status == "RESOLVED"
    assert res.resolution_note == "Valid explanation provided"
    assert res.resolved_at is not None


def test_7_waive_discrepancy(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    d = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        type="TEST_WAIVE",
        title="Title",
        description="Desc",
        finding_key=f"key_waive_{s.id}",
    )
    res = discrepancy_service.update_discrepancy_status(
        db=db, discrepancy_id=d.id, status="WAIVED", resolution_note="Waived by CPCL officer"
    )
    assert res.status == "WAIVED"
    assert res.resolution_note == "Waived by CPCL officer"


def test_8_invalid_status_rejected(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    d = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        type="TEST_INVALID",
        title="Title",
        description="Desc",
        finding_key=f"key_invalid_{s.id}",
    )
    with pytest.raises(ValueError, match="Invalid status"):
        discrepancy_service.update_discrepancy_status(db, d.id, "INVALID_STATUS")


def test_9_duplicate_handling_idempotency(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    key = f"stable_key_dup_{s.id}"
    d1 = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        type="DUPLICATE_TYPE",
        title="Original Title",
        description="Original Desc",
        finding_key=key,
    )
    # Record same finding again
    d2 = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        type="DUPLICATE_TYPE",
        title="Updated Title",
        description="Updated Desc",
        finding_key=key,
    )
    assert d1.id == d2.id
    assert d2.title == "Updated Title"

    all_discs = discrepancy_service.get_discrepancies_for_submission(db, s.id)
    dup_count = sum(1 for d in all_discs if d.finding_key == key)
    assert dup_count == 1


def test_10_cross_verification_persists_discrepancies(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    b = test_setup["bidder"]
    # Change bidder GSTIN to create a deliberate mismatch
    b.gstin = "99XXXXX9999X1Z9"
    db.commit()

    res = cross_verification_service.cross_verify_submission(db, s.id)
    assert res.has_discrepancies is True

    persisted = discrepancy_service.get_discrepancies_for_submission(db, s.id)
    assert len(persisted) > 0
    assert any(d.source == "CROSS_VERIFICATION" for d in persisted)


def test_11_missing_mandatory_evidence_persisted(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    req_epfo = test_setup["req_epfo"]

    checks = compliance_service.evaluate_submission(db, s.id)
    epfo_check = next((c for c in checks if c.tender_requirement_id == req_epfo.id), None)
    assert epfo_check is not None
    assert epfo_check.status == "MISSING"

    persisted = discrepancy_service.get_discrepancies_for_submission(db, s.id)
    missing_disc = next((d for d in persisted if d.type == "MISSING_EVIDENCE" and d.tender_requirement_id == req_epfo.id), None)
    assert missing_disc is not None
    assert missing_disc.severity == "HIGH"


def test_12_missing_optional_evidence_not_discrepancy(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    req_opt = test_setup["req_optional"]

    checks = compliance_service.evaluate_submission(db, s.id)
    opt_check = next((c for c in checks if c.tender_requirement_id == req_opt.id), None)
    assert opt_check is not None
    assert opt_check.status == "NOT_APPLICABLE"

    persisted = discrepancy_service.get_discrepancies_for_submission(db, s.id)
    opt_disc = next((d for d in persisted if d.tender_requirement_id == req_opt.id), None)
    assert opt_disc is None


def test_13_provider_technical_error_not_bidder_failure(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    # Register an error verification result
    v_err = VerificationResult(
        bid_submission_id=s.id,
        provider="SampleProvider",
        verification_type="EPFO",
        identifier="EPFO12345",
        verification_status="ERROR",
        error_message="Connection timeout to EPFO server",
    )
    db.add(v_err)
    db.commit()

    checks = compliance_service.evaluate_submission(db, s.id)
    epfo_check = next((c for c in checks if c.tender_requirement_id == test_setup["req_epfo"].id), None)
    assert epfo_check is not None
    # ERROR status should lead to REVIEW or MISSING, not false bidder failure
    assert epfo_check.status in ("MISSING", "REVIEW")


def test_14_multi_document_evidence(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    doc2 = BidDocument(
        bid_submission_id=s.id,
        file_name="Gst_Return_2026.pdf",
        file_path="storage/documents/Gst_Return_2026.pdf",
        document_type="GST_RETURN",
    )
    db.add(doc2)
    db.commit()

    checks = compliance_service.evaluate_submission(db, s.id)
    assert len(checks) > 0


def test_15_discrepancy_references_correct_document(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    doc = test_setup["doc_gst"]
    d = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        bid_document_id=doc.id,
        type="EXPIRED_DOCUMENT",
        title="Doc Expired",
        description="Expired doc",
        finding_key=f"key_doc_ref_{s.id}",
    )
    assert d.bid_document_id == doc.id


def test_16_discrepancy_references_correct_verification_result(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    vr = test_setup["v_result"]
    d = discrepancy_service.record_discrepancy(
        db=db,
        bid_submission_id=s.id,
        verification_result_id=vr.id,
        type="INACTIVE_REGISTRATION",
        title="Inactive GST",
        description="Inactive registration",
        finding_key=f"key_vr_ref_{s.id}",
    )
    assert d.verification_result_id == vr.id


def test_17_compliance_check_intact(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    checks = compliance_service.evaluate_submission(db, s.id)
    assert len(checks) > 0
    for c in checks:
        assert c.status in ("PASS", "FAIL", "MISSING", "REVIEW", "NOT_APPLICABLE", "PENDING")


def test_18_end_to_end_verification_persists_discrepancies(test_setup):
    db = test_setup["db"]
    s = test_setup["submission"]
    summary = end_to_end_verification_service.verify_bid_submission(db, s.id)
    assert summary.status == "COMPLETED"

    persisted = discrepancy_service.get_discrepancies_for_submission(db, s.id)
    assert isinstance(persisted, list)
