import pytest
from unittest.mock import Mock

from app.services.cross_verification_service import (
    CrossVerificationService,
    normalize_name,
)


def test_normalize_name_utility():
    assert normalize_name("ABC Industries Pvt Ltd") == "ABCINDUSTRIES"
    assert normalize_name("ABC Industries Limited") == "ABCINDUSTRIES"
    assert normalize_name("Demo Engineering Corporation") == "DEMOENGINEERINGCORPORATION"


def test_cross_verification_detects_legal_name_mismatch():
    doc_repo = Mock()
    doc1 = Mock(id=1, file_name="gst.pdf", document_type="GST_CERTIFICATE")
    doc2 = Mock(id=2, file_name="udyam.pdf", document_type="UDYAM_CERTIFICATE")
    doc_repo.get_by_submission_id.return_value = [doc1, doc2]

    extraction_repo = Mock()
    ext1 = Mock(extracted_data={"legal_name": "ABC Industries Pvt Ltd"})
    ext2 = Mock(extracted_data={"enterprise_name": "XYZ Solutions Pvt Ltd"})

    def get_latest(db, doc_id):
        if doc_id == 1:
            return ext1
        return ext2

    extraction_repo.get_latest_by_document_id.side_effect = get_latest

    verification_repo = Mock()
    verification_repo.get_by_submission.return_value = []

    db = Mock()
    service = CrossVerificationService(
        doc_repo=doc_repo,
        extraction_repo=extraction_repo,
        verification_repo=verification_repo,
    )

    result = service.cross_verify_submission(db, bid_submission_id=10)

    assert result.has_discrepancies is True
    assert result.discrepancies_count >= 1
    assert result.discrepancies[0].discrepancy_type == "LEGAL_NAME_MISMATCH"


def test_cross_verification_detects_gstin_mismatch():
    doc_repo = Mock()
    doc = Mock(id=1, file_name="gst.pdf", document_type="GST_CERTIFICATE")
    doc_repo.get_by_submission_id.return_value = [doc]

    extraction_repo = Mock()
    ext = Mock(extracted_data={"gstin": "27ABCDE1234F1Z5"})
    extraction_repo.get_latest_by_document_id.return_value = ext

    verification_repo = Mock()
    verif = Mock(provider="GST", identifier="29DIFFERENT1234F")
    verification_repo.get_by_submission.return_value = [verif]

    db = Mock()
    service = CrossVerificationService(
        doc_repo=doc_repo,
        extraction_repo=extraction_repo,
        verification_repo=verification_repo,
    )

    result = service.cross_verify_submission(db, bid_submission_id=10)

    assert result.has_discrepancies is True
    assert any(d.discrepancy_type == "GSTIN_MISMATCH" for d in result.discrepancies)


def test_cross_verification_detects_embedded_pan_gstin_mismatch():
    submission_repo = Mock()
    bidder = Mock(company_name="Acme Inc", gstin="27ABCDE1234F1Z5", pan="XYZDE1234F", udyam_number=None)
    submission_repo.get_by_id.return_value = Mock(bidder=bidder)

    doc_repo = Mock()
    doc_repo.get_by_submission_id.return_value = []

    extraction_repo = Mock()
    verification_repo = Mock()
    verification_repo.get_by_submission.return_value = []

    db = Mock()
    service = CrossVerificationService(
        doc_repo=doc_repo,
        extraction_repo=extraction_repo,
        verification_repo=verification_repo,
        submission_repo=submission_repo,
    )

    result = service.cross_verify_submission(db, bid_submission_id=10)

    assert result.has_discrepancies is True
    assert any(d.discrepancy_type == "PAN_GSTIN_EMBEDDED_MISMATCH" for d in result.discrepancies)


def test_cross_verification_detects_inactive_registration_status():
    submission_repo = Mock()
    submission_repo.get_by_id.return_value = None

    doc_repo = Mock()
    doc_repo.get_by_submission_id.return_value = []

    extraction_repo = Mock()
    verification_repo = Mock()
    v_gst = Mock(source="GST", provider="GST", identifier="27ABCDE1234F1Z5", status="VERIFIED", verified_data={"registration_status": "CANCELLED"})
    v_mca = Mock(source="MCA21", provider="MCA21", identifier="U12345MH2020PTC123456", status="VERIFIED", verified_data={"company_status": "STRUCK_OFF"})
    verification_repo.get_by_submission.return_value = [v_gst, v_mca]

    db = Mock()
    service = CrossVerificationService(
        doc_repo=doc_repo,
        extraction_repo=extraction_repo,
        verification_repo=verification_repo,
        submission_repo=submission_repo,
    )

    result = service.cross_verify_submission(db, bid_submission_id=10)

    assert result.has_discrepancies is True
    inactive_discrepancies = [d for d in result.discrepancies if d.discrepancy_type == "INACTIVE_REGISTRATION"]
    assert len(inactive_discrepancies) >= 2


def test_cross_verification_detects_debarred_vendor():
    submission_repo = Mock()
    submission_repo.get_by_id.return_value = None

    doc_repo = Mock()
    doc_repo.get_by_submission_id.return_value = []

    extraction_repo = Mock()
    verification_repo = Mock()
    v_deb = Mock(source="DEBARMENT", provider="DEBARMENT", identifier="PAN12345", status="VERIFIED", verified_data={"is_debarred": True, "debarment_status": "DEBARRED", "debarring_agency": "GeM"})
    verification_repo.get_by_submission.return_value = [v_deb]

    db = Mock()
    service = CrossVerificationService(
        doc_repo=doc_repo,
        extraction_repo=extraction_repo,
        verification_repo=verification_repo,
        submission_repo=submission_repo,
    )

    result = service.cross_verify_submission(db, bid_submission_id=10)

    assert result.has_discrepancies is True
    assert any(d.discrepancy_type == "DEBARRED_VENDOR" for d in result.discrepancies)


def test_cross_verification_detects_expired_document():
    submission_repo = Mock()
    submission_repo.get_by_id.return_value = None

    doc_repo = Mock()
    doc = Mock(id=1, file_name="oem_auth.pdf", document_type="OEM_AUTHORIZATION")
    doc_repo.get_by_submission_id.return_value = [doc]

    extraction_repo = Mock()
    ext = Mock(extracted_data={"is_expired": True, "valid_until": "2020-01-01T00:00:00Z"})
    extraction_repo.get_latest_by_document_id.return_value = ext

    verification_repo = Mock()
    verification_repo.get_by_submission.return_value = []

    db = Mock()
    service = CrossVerificationService(
        doc_repo=doc_repo,
        extraction_repo=extraction_repo,
        verification_repo=verification_repo,
        submission_repo=submission_repo,
    )

    result = service.cross_verify_submission(db, bid_submission_id=10)

    assert result.has_discrepancies is True
    assert any(d.discrepancy_type == "EXPIRED_DOCUMENT" for d in result.discrepancies)


def test_cross_verification_detects_missing_portal_verification():
    submission_repo = Mock()
    submission_repo.get_by_id.return_value = None

    doc_repo = Mock()
    doc = Mock(id=1, file_name="gst_cert.pdf", document_type="GST_CERTIFICATE")
    doc_repo.get_by_submission_id.return_value = [doc]

    extraction_repo = Mock()
    ext = Mock(extracted_data={"document_type": "GST_CERTIFICATE", "fields": {"gstin": "27ABCDE1234F1Z5"}})
    extraction_repo.get_latest_by_document_id.return_value = ext

    verification_repo = Mock()
    verification_repo.get_by_submission.return_value = []  # GST portal verification missing

    db = Mock()
    service = CrossVerificationService(
        doc_repo=doc_repo,
        extraction_repo=extraction_repo,
        verification_repo=verification_repo,
        submission_repo=submission_repo,
    )

    result = service.cross_verify_submission(db, bid_submission_id=10)

    assert result.has_discrepancies is True
    assert any(d.discrepancy_type == "MISSING_PORTAL_VERIFICATION" for d in result.discrepancies)

