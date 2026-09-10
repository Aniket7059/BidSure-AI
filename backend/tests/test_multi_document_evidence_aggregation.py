import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.tender import Tender
from app.models.bidder import Bidder
from app.models.bid_submission import BidSubmission
from app.models.bid_document import BidDocument
from app.models.document_extraction import DocumentExtraction
from app.models.tender_requirement import TenderRequirement
from app.providers.schemas import VerificationResult as ProviderVerificationResult, VerificationStatus
from app.repositories.verification_result_repository import verification_result_repository
from app.services.compliance_service import compliance_service
from app.services.cross_verification_service import CrossVerificationService
from app.services.end_to_end_verification_service import end_to_end_verification_service
from app.core.taxonomy import RequirementType


from app.database.session import SessionLocal


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


import uuid


def create_test_submission(db: Session) -> tuple[Tender, Bidder, BidSubmission]:
    uid = uuid.uuid4().hex[:8].upper()
    tender = Tender(
        reference_number=f"TENDER-MULTI-{uid}",
        title="Multi-Document Evidence Aggregation Test Tender",
        description="Test tender for evidence aggregation",
        status="ACTIVE",
        created_at=datetime.now(timezone.utc),
    )
    db.add(tender)
    db.flush()

    req_gst = TenderRequirement(
        tender_id=tender.id,
        requirement_type="GST",
        requirement_name="GST Compliance & Return Filing",
        is_required=True,
    )
    req_pan = TenderRequirement(
        tender_id=tender.id,
        requirement_type="PAN",
        requirement_name="PAN Card Verification",
        is_required=True,
    )
    req_itr = TenderRequirement(
        tender_id=tender.id,
        requirement_type="INCOME_TAX",
        requirement_name="Income Tax Returns",
        is_required=True,
    )
    db.add_all([req_gst, req_pan, req_itr])
    bidder = Bidder(
        company_name=f"MULTI DOC ENTERPRISE {uid} PVT LTD",
        contact_email=f"multi_{uid.lower()}@enterprise.com",
        gstin=f"27MDA{uid[:6]}1Z5",
        pan=f"MDA{uid[:6]}F",
    )
    db.add(bidder)
    db.flush()

    submission = BidSubmission(
        tender_id=tender.id,
        bidder_id=bidder.id,
        status="SUBMITTED",
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return tender, bidder, submission


def test_1_and_3_two_documents_same_requirement_both_survive_and_distinguishable(db: Session):
    _, _, submission = create_test_submission(db)

    # Doc 1: GST Certificate
    doc1 = BidDocument(
        bid_submission_id=submission.id,
        file_name="gst_certificate.pdf",
        file_path="/docs/gst_certificate.pdf",
        document_type="GST_CERTIFICATE",
        uploaded_at=datetime.now(timezone.utc),
    )
    # Doc 2: GST Return
    doc2 = BidDocument(
        bid_submission_id=submission.id,
        file_name="gstr3b_return.pdf",
        file_path="/docs/gstr3b_return.pdf",
        document_type="GST_RETURN",
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add_all([doc1, doc2])
    db.flush()

    ext1 = DocumentExtraction(
        bid_document_id=doc1.id,
        extracted_data={
            "document_type": "GST_CERTIFICATE",
            "fields": {
                "gstin": "27ABCDE1234F1Z5",
                "legal_name": "MULTI DOC ENTERPRISE PVT LTD",
                "registration_status": "ACTIVE",
            },
        },
        extraction_status="COMPLETED",
        created_at=datetime.now(timezone.utc),
    )
    ext2 = DocumentExtraction(
        bid_document_id=doc2.id,
        extracted_data={
            "document_type": "GST_RETURN",
            "fields": {
                "gstin": "27ABCDE1234F1Z5",
                "return_type": "GSTR-3B",
                "filing_status": "FILED",
            },
        },
        extraction_status="COMPLETED",
        created_at=datetime.now(timezone.utc),
    )
    db.add_all([ext1, ext2])
    db.commit()

    checks = compliance_service.evaluate_submission(db, submission.id)
    gst_check = next(c for c in checks if c.evidence.get("requirement_type") == "GST")

    assert gst_check is not None
    ev = gst_check.evidence
    all_exts = ev["all_extractions"]

    # Both documents survive aggregation
    assert len(all_exts) == 2
    doc_types = {e["document_type"] for e in all_exts}
    assert "GST_CERTIFICATE" in doc_types
    assert "GST_RETURN" in doc_types

    # Merged fields contain facts from both documents
    merged_fields = ev["merged_extracted_data"]
    assert merged_fields["gstin"] == "27ABCDE1234F1Z5"
    assert merged_fields["legal_name"] == "MULTI DOC ENTERPRISE PVT LTD"
    assert merged_fields["return_type"] == "GSTR-3B"
    assert merged_fields["filing_status"] == "FILED"


def test_2_three_documents_same_requirement_all_survive(db: Session):
    _, _, submission = create_test_submission(db)

    docs = []
    exts = []
    for i in range(1, 4):
        doc = BidDocument(
            bid_submission_id=submission.id,
            file_name=f"gst_doc_{i}.pdf",
            file_path=f"/docs/gst_doc_{i}.pdf",
            document_type="GST_CERTIFICATE",
            uploaded_at=datetime.now(timezone.utc),
        )
        db.add(doc)
        db.flush()
        docs.append(doc)

        ext = DocumentExtraction(
            bid_document_id=doc.id,
            extracted_data={
                "document_type": "GST_CERTIFICATE",
                "fields": {
                    "gstin": "27ABCDE1234F1Z5",
                    "doc_index": i,
                },
            },
            extraction_status="COMPLETED",
            created_at=datetime.now(timezone.utc),
        )
        db.add(ext)
        exts.append(ext)

    db.commit()

    checks = compliance_service.evaluate_submission(db, submission.id)
    gst_check = next(c for c in checks if c.evidence.get("requirement_type") == "GST")
    all_exts = gst_check.evidence["all_extractions"]

    assert len(all_exts) == 3


def test_4_conflicting_identifiers_preserved_without_silent_overwrite(db: Session):
    _, _, submission = create_test_submission(db)

    doc1 = BidDocument(
        bid_submission_id=submission.id,
        file_name="gst_cert_a.pdf",
        file_path="/docs/gst_cert_a.pdf",
        document_type="GST_CERTIFICATE",
    )
    doc2 = BidDocument(
        bid_submission_id=submission.id,
        file_name="gst_cert_b.pdf",
        file_path="/docs/gst_cert_b.pdf",
        document_type="GST_CERTIFICATE",
    )
    db.add_all([doc1, doc2])
    db.flush()

    ext1 = DocumentExtraction(
        bid_document_id=doc1.id,
        extracted_data={
            "fields": {"gstin": "27ABCDE1234F1Z5"}
        },
        extraction_status="COMPLETED",
    )
    ext2 = DocumentExtraction(
        bid_document_id=doc2.id,
        extracted_data={
            "fields": {"gstin": "29XYZAB9876C1Z9"}
        },
        extraction_status="COMPLETED",
    )
    db.add_all([ext1, ext2])
    db.commit()

    checks = compliance_service.evaluate_submission(db, submission.id)
    gst_check = next(c for c in checks if c.evidence.get("requirement_type") == "GST")

    ev = gst_check.evidence
    merged = ev["merged_extracted_data"]

    # Conflict is detected and preserved explicitly
    assert ev["has_conflicts"] is True
    assert merged.get("_has_conflicts") is True
    assert "gstin" in merged["_conflicting_fields"]
    assert "27ABCDE1234F1Z5" in merged["_conflicting_fields"]["gstin"]
    assert "29XYZAB9876C1Z9" in merged["_conflicting_fields"]["gstin"]


def test_5_same_fields_different_documents_both_retained(db: Session):
    _, _, submission = create_test_submission(db)

    doc1 = BidDocument(
        bid_submission_id=submission.id,
        file_name="copy1.pdf",
        file_path="/docs/copy1.pdf",
        document_type="GST_CERTIFICATE",
    )
    doc2 = BidDocument(
        bid_submission_id=submission.id,
        file_name="copy2.pdf",
        file_path="/docs/copy2.pdf",
        document_type="GST_CERTIFICATE",
    )
    db.add_all([doc1, doc2])
    db.flush()

    ext1 = DocumentExtraction(
        bid_document_id=doc1.id,
        extracted_data={"fields": {"gstin": "27ABCDE1234F1Z5"}},
    )
    ext2 = DocumentExtraction(
        bid_document_id=doc2.id,
        extracted_data={"fields": {"gstin": "27ABCDE1234F1Z5"}},
    )
    db.add_all([ext1, ext2])
    db.commit()

    checks = compliance_service.evaluate_submission(db, submission.id)
    gst_check = next(c for c in checks if c.evidence.get("requirement_type") == "GST")

    all_exts = gst_check.evidence["all_extractions"]
    assert len(all_exts) == 2
    assert all_exts[0]["file_name"] == "copy1.pdf"
    assert all_exts[1]["file_name"] == "copy2.pdf"


def test_6_duplicate_extraction_records_deduplicated(db: Session):
    _, _, submission = create_test_submission(db)

    doc = BidDocument(
        bid_submission_id=submission.id,
        file_name="gst_cert.pdf",
        file_path="/docs/gst_cert.pdf",
        document_type="GST_CERTIFICATE",
    )
    db.add(doc)
    db.flush()

    ext = DocumentExtraction(
        bid_document_id=doc.id,
        extracted_data={"fields": {"gstin": "27ABCDE1234F1Z5"}},
    )
    db.add(ext)
    db.commit()

    checks = compliance_service.evaluate_submission(db, submission.id)
    gst_check = next(c for c in checks if c.evidence.get("requirement_type") == "GST")

    all_exts = gst_check.evidence["all_extractions"]
    assert len(all_exts) == 1


def test_7_multiple_provider_results_preserved(db: Session):
    _, _, submission = create_test_submission(db)

    res1 = ProviderVerificationResult(
        provider="GST",
        verification_type="GST_REGISTRATION",
        identifier="27ABCDE1234F1Z5",
        status=VerificationStatus.VERIFIED,
        verified_data={"legal_name": "MULTI DOC ENTERPRISE PVT LTD", "registration_status": "ACTIVE"},
        message="Registration active",
    )
    res2 = ProviderVerificationResult(
        provider="GST_RETURN",
        verification_type="GST_RETURN_FILING",
        identifier="27ABCDE1234F1Z5",
        status=VerificationStatus.VERIFIED,
        verified_data={"gstin": "27ABCDE1234F1Z5", "filing_status": "FILED"},
        message="Return filed",
    )

    verification_result_repository.create(db, submission.id, res1)
    verification_result_repository.create(db, submission.id, res2)

    checks = compliance_service.evaluate_submission(db, submission.id)
    gst_check = next(c for c in checks if c.evidence.get("requirement_type") == "GST")

    all_vers = gst_check.evidence["all_verifications"]
    assert len(all_vers) == 2
    providers = {v["provider"] for v in all_vers}
    assert "GST" in providers
    assert "GST_RETURN" in providers


def test_8_pan_and_income_tax_evidence_remain_separate(db: Session):
    _, _, submission = create_test_submission(db)

    doc_pan = BidDocument(
        bid_submission_id=submission.id,
        file_name="pan_card.pdf",
        file_path="/docs/pan_card.pdf",
        document_type="PAN",
    )
    doc_itr = BidDocument(
        bid_submission_id=submission.id,
        file_name="itr_acknowledgement.pdf",
        file_path="/docs/itr_acknowledgement.pdf",
        document_type="INCOME_TAX",
    )
    db.add_all([doc_pan, doc_itr])
    db.flush()

    ext_pan = DocumentExtraction(
        bid_document_id=doc_pan.id,
        extracted_data={"fields": {"pan_number": "ABCDE1234F", "name": "MULTI DOC ENTERPRISE PVT LTD"}},
    )
    ext_itr = DocumentExtraction(
        bid_document_id=doc_itr.id,
        extracted_data={"fields": {"pan_number": "ABCDE1234F", "assessment_year": "2023-24", "itr_filed": True}},
    )
    db.add_all([ext_pan, ext_itr])
    db.commit()

    checks = compliance_service.evaluate_submission(db, submission.id)

    pan_check = next(c for c in checks if c.evidence.get("requirement_type") == "PAN")
    itr_check = next(c for c in checks if c.evidence.get("requirement_type") == "INCOME_TAX")

    assert pan_check.evidence["all_extractions"][0]["document_type"] == "PAN"
    assert itr_check.evidence["all_extractions"][0]["document_type"] == "INCOME_TAX"


def test_9_full_e2e_multiple_documents_flow(db: Session):
    _, _, submission = create_test_submission(db)

    doc1 = BidDocument(
        bid_submission_id=submission.id,
        file_name="gst_cert.pdf",
        file_path="/docs/gst_cert.pdf",
        document_type="GST_CERTIFICATE",
    )
    doc2 = BidDocument(
        bid_submission_id=submission.id,
        file_name="gst_return.pdf",
        file_path="/docs/gst_return.pdf",
        document_type="GST_RETURN",
    )
    db.add_all([doc1, doc2])
    db.flush()

    ext1 = DocumentExtraction(
        bid_document_id=doc1.id,
        extracted_data={"fields": {"gstin": "27ABCDE1234F1Z5"}},
    )
    ext2 = DocumentExtraction(
        bid_document_id=doc2.id,
        extracted_data={"fields": {"gstin": "27ABCDE1234F1Z5", "filing_status": "FILED"}},
    )
    db.add_all([ext1, ext2])
    db.commit()

    res = end_to_end_verification_service.verify_bid_submission(db, submission.id)
    assert res is not None
    assert res.overall_status in ("COMPLIANT", "NON_COMPLIANT", "PARTIALLY_COMPLIANT", "NEEDS_REVIEW", "REVIEW")


def test_11_cross_verification_sees_all_extractions(db: Session):
    _, _, submission = create_test_submission(db)

    doc1 = BidDocument(
        bid_submission_id=submission.id,
        file_name="gst_cert.pdf",
        file_path="/docs/gst_cert.pdf",
        document_type="GST_CERTIFICATE",
    )
    doc2 = BidDocument(
        bid_submission_id=submission.id,
        file_name="pan_card.pdf",
        file_path="/docs/pan_card.pdf",
        document_type="PAN",
    )
    db.add_all([doc1, doc2])
    db.flush()

    ext1 = DocumentExtraction(
        bid_document_id=doc1.id,
        extracted_data={"fields": {"legal_name": "COMPANY NAME A"}},
    )
    ext2 = DocumentExtraction(
        bid_document_id=doc2.id,
        extracted_data={"fields": {"name": "DIFFERENT COMPANY NAME B"}},
    )
    db.add_all([ext1, ext2])
    db.commit()

    service = CrossVerificationService()
    res = service.cross_verify_submission(db, submission.id)

    assert res.has_discrepancies is True
    assert any(d.discrepancy_type == "LEGAL_NAME_MISMATCH" for d in res.discrepancies)
