import uuid
from datetime import datetime, timezone

from app.database.session import SessionLocal
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_submission import BidSubmission
from app.models.bid_document import BidDocument
from app.models.document_extraction import DocumentExtraction
from app.models.verification_result import VerificationResult
from app.repositories.compliance_check_repository import compliance_check_repository
from app.services.compliance_service import compliance_service
from app.services.compliance_assessment_service import compliance_assessment_service


def create_task8_test_fixture(db):
    """
    Creates a test environment with a bidder, tender, requirements,
    documents, and verification records matching Task 8 specifications.
    """
    uid = uuid.uuid4().hex[:8].upper()

    bidder = Bidder(
        company_name=f"Task8 Test Company {uid}",
        gstin=f"27ABCDE{uid[:4]}F1Z5",
        pan=f"ABCDE{uid[:4]}F",
        udyam_number=f"UDYAM-KR-{uid}",
    )
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    tender = Tender(
        title=f"Task 8 Tender {uid}",
        reference_number=f"T8-REF-{uid}",
        description="Comprehensive evaluation test tender",
        status="ACTIVE",
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)

    # 5 Requirements matching prompt example:
    # 1. GST (Mandatory) -> PASS
    # 2. UDYAM (Mandatory) -> PASS
    # 3. PAN (Mandatory) -> MISSING
    # 4. EPFO (Mandatory) -> FAIL
    # 5. OEM (Optional) -> NOT_APPLICABLE
    req_gst = TenderRequirement(
        tender_id=tender.id,
        requirement_type="GST",
        requirement_name="GST Registration Certificate",
        description="Valid GSTIN required",
        is_required=True,
    )
    req_udyam = TenderRequirement(
        tender_id=tender.id,
        requirement_type="UDYAM",
        requirement_name="Udyam MSME Certificate",
        description="Valid MSME enterprise registration",
        is_required=True,
    )
    req_pan = TenderRequirement(
        tender_id=tender.id,
        requirement_type="PAN",
        requirement_name="PAN Card",
        description="Permanent Account Number details",
        is_required=True,
    )
    req_epfo = TenderRequirement(
        tender_id=tender.id,
        requirement_type="EPFO",
        requirement_name="EPFO Compliance Certificate",
        description="Active EPFO establishment code",
        is_required=True,
    )
    req_oem = TenderRequirement(
        tender_id=tender.id,
        requirement_type="OEM_AUTHORIZATION",
        requirement_name="OEM Authorization Letter",
        description="Optional OEM authorization",
        is_required=False,
    )

    db.add_all([req_gst, req_udyam, req_pan, req_epfo, req_oem])
    db.commit()

    submission = BidSubmission(
        tender_id=tender.id,
        bidder_id=bidder.id,
        status="SUBMITTED",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # 1. GST evidence -> PASS
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
                "gstin": bidder.gstin,
                "legal_name": bidder.company_name,
                "status": "ACTIVE",
            },
        },
        confidence_score=0.98,
    )
    ver_gst = VerificationResult(
        bid_submission_id=submission.id,
        provider="GST_PORTAL",
        verification_type="GST",
        identifier=bidder.gstin,
        verification_status="VERIFIED",
        verified_data={
            "gstin": bidder.gstin,
            "legal_name": bidder.company_name,
            "registration_status": "ACTIVE",
        },
        checked_at=datetime.now(timezone.utc),
    )
    db.add_all([ext_gst, ver_gst])

    # 2. UDYAM evidence -> PASS
    doc_udyam = BidDocument(
        bid_submission_id=submission.id,
        document_type="UDYAM_CERTIFICATE",
        file_name=f"udyam_{uid}.pdf",
        file_path=f"/uploads/udyam_{uid}.pdf",
        status="PROCESSED",
    )
    db.add(doc_udyam)
    db.commit()
    db.refresh(doc_udyam)

    ext_udyam = DocumentExtraction(
        bid_document_id=doc_udyam.id,
        extracted_data={
            "document_type": "UDYAM_CERTIFICATE",
            "fields": {
                "udyam_number": bidder.udyam_number,
                "enterprise_name": bidder.company_name,
            },
        },
        confidence_score=0.95,
    )
    ver_udyam = VerificationResult(
        bid_submission_id=submission.id,
        provider="MSME_PORTAL",
        verification_type="UDYAM",
        identifier=bidder.udyam_number,
        verification_status="VERIFIED",
        verified_data={
            "udyam_number": bidder.udyam_number,
            "enterprise_name": bidder.company_name,
            "enterprise_status": "ACTIVE",
        },
        checked_at=datetime.now(timezone.utc),
    )
    db.add_all([ext_udyam, ver_udyam])

    # 3. PAN -> No doc, no verification (MISSING)

    # 4. EPFO evidence -> FAIL (Invalid/Inactive code)
    doc_epfo = BidDocument(
        bid_submission_id=submission.id,
        document_type="EPFO",
        file_name=f"epfo_{uid}.pdf",
        file_path=f"/uploads/epfo_{uid}.pdf",
        status="PROCESSED",
    )
    db.add(doc_epfo)
    db.commit()
    db.refresh(doc_epfo)

    ext_epfo = DocumentExtraction(
        bid_document_id=doc_epfo.id,
        extracted_data={
            "document_type": "EPFO",
            "fields": {
                "est_code": "INVALID_CODE_123",
                "est_name": "Different Company",
            },
        },
        confidence_score=0.90,
    )
    ver_epfo = VerificationResult(
        bid_submission_id=submission.id,
        provider="EPFO_PORTAL",
        verification_type="EPFO",
        identifier="INVALID_CODE_123",
        verification_status="FAILED",
        verified_data={
            "est_code": "INVALID_CODE_123",
            "est_status": "CANCELLED",
        },
        checked_at=datetime.now(timezone.utc),
    )
    db.add_all([ext_epfo, ver_epfo])

    # 5. OEM -> Optional, no doc (NOT_APPLICABLE)

    db.commit()
    return bidder, tender, submission, [req_gst, req_udyam, req_pan, req_epfo, req_oem]


def test_compliance_engine_evaluates_all_five_requirements():
    db = SessionLocal()
    try:
        bidder, tender, submission, reqs = create_task8_test_fixture(db)

        checks = compliance_service.evaluate_submission(db, submission.id)

        assert len(checks) == 5

        checks_by_type = {
            c.tender_requirement.requirement_type: c.status.upper()
            for c in checks
        }

        assert checks_by_type["GST"] == "PASS"
        assert checks_by_type["UDYAM"] == "PASS"
        assert checks_by_type["PAN"] == "MISSING"
        assert checks_by_type["EPFO"] == "FAIL"
        assert checks_by_type["OEM_AUTHORIZATION"] == "NOT_APPLICABLE"

        assessment = compliance_assessment_service.assess_submission(
            db, submission.id
        )

        assert assessment.status == "NON_COMPLIANT"
        assert assessment.risk_level == "HIGH"
        assert assessment.assessment_metadata["total_checks"] == 5
        assert assessment.assessment_metadata["passed"] == 2
        assert assessment.assessment_metadata["failed"] == 1
        assert assessment.assessment_metadata["missing"] == 1
        assert assessment.assessment_metadata["not_applicable"] == 1
    finally:
        db.close()


def test_optional_requirement_not_submitted_does_not_cause_disqualification():
    db = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:8].upper()
        bidder = Bidder(company_name=f"Opt Co {uid}", gstin=f"29OPT{uid[:4]}A1Z5")
        tender = Tender(title=f"Opt Tender {uid}", reference_number=f"OPT-{uid}")
        db.add_all([bidder, tender])
        db.commit()

        req_gst = TenderRequirement(
            tender_id=tender.id,
            requirement_type="GST",
            requirement_name="GST Cert",
            is_required=True,
        )
        req_oem = TenderRequirement(
            tender_id=tender.id,
            requirement_type="OEM_AUTHORIZATION",
            requirement_name="OEM Auth",
            is_required=False,
        )
        db.add_all([req_gst, req_oem])
        db.commit()

        submission = BidSubmission(tender_id=tender.id, bidder_id=bidder.id)
        db.add(submission)
        db.commit()

        doc_gst = BidDocument(
            bid_submission_id=submission.id,
            document_type="GST_CERTIFICATE",
            file_name="gst.pdf",
            file_path="/tmp/gst.pdf",
        )
        db.add(doc_gst)
        db.commit()

        ext_gst = DocumentExtraction(
            bid_document_id=doc_gst.id,
            extracted_data={
                "document_type": "GST_CERTIFICATE",
                "fields": {"gstin": bidder.gstin, "status": "ACTIVE"},
            },
        )
        ver_gst = VerificationResult(
            bid_submission_id=submission.id,
            provider="GST_PORTAL",
            verification_type="GST",
            identifier=bidder.gstin,
            verification_status="VERIFIED",
            verified_data={"gstin": bidder.gstin, "registration_status": "ACTIVE"},
        )
        db.add_all([ext_gst, ver_gst])
        db.commit()

        checks = compliance_service.evaluate_submission(db, submission.id)
        checks_by_type = {
            c.tender_requirement.requirement_type: c.status.upper()
            for c in checks
        }

        assert checks_by_type["GST"] == "PASS"
        assert checks_by_type["OEM_AUTHORIZATION"] == "NOT_APPLICABLE"

        assessment = compliance_assessment_service.assess_submission(
            db, submission.id
        )

        assert assessment.status == "COMPLIANT"
        assert assessment.risk_level == "LOW"
        assert assessment.score == 100.0
    finally:
        db.close()


def test_no_duplicate_compliance_check_records_on_reevaluation():
    db = SessionLocal()
    try:
        bidder, tender, submission, reqs = create_task8_test_fixture(db)

        checks1 = compliance_service.evaluate_submission(db, submission.id)
        assert len(checks1) == 5

        checks2 = compliance_service.evaluate_submission(db, submission.id)
        assert len(checks2) == 5

        all_checks = compliance_check_repository.get_by_submission(
            db, submission.id
        )
        assert len(all_checks) == 5
    finally:
        db.close()
