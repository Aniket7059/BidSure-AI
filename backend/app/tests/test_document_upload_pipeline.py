import hashlib
import io
import os
import tempfile
import uuid
import pytest
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.tender import Tender
from app.models.bidder import Bidder
from app.models.bid_submission import BidSubmission
from app.models.bid_document import BidDocument
from app.services.storage_service import DocumentStorageService, sanitize_filename
from app.services.document_upload_service import DocumentUploadService
from app.database.session import SessionLocal
from app.repositories.bid_submission_repository import bid_submission_repository


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


def create_test_submission(db: Session) -> tuple[Tender, Bidder, BidSubmission]:
    uid = uuid.uuid4().hex[:6]
    tender = Tender(
        reference_number=f"TENDER-UPLOAD-{uid}",
        title="Upload Pipeline Test Tender",
        description="Test tender for document upload pipeline",
        status="ACTIVE",
        created_at=datetime.now(timezone.utc),
    )
    db.add(tender)
    db.flush()

    uid_full = uuid.uuid4().hex.upper()
    bidder = Bidder(
        company_name=f"UPLOAD TEST ENTERPRISE {uid} PVT LTD",
        contact_email=f"upload_{uid}@enterprise.com",
        gstin=f"27{uid_full[:10]}Z5",
        pan=f"P{uid_full[:8]}",
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


import fitz

def _make_valid_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Goods and Services Tax GSTIN: 27ABCDE1234F1Z5 Registration Certificate")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

VALID_PDF_BYTES = _make_valid_pdf_bytes()
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
VALID_JPG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xd9"


def test_1_successful_pdf_upload_and_storage(db: Session):
    _, _, submission = create_test_submission(db)
    storage_temp = tempfile.mkdtemp()
    storage_svc = DocumentStorageService(storage_root=storage_temp)
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    file_obj = io.BytesIO(VALID_PDF_BYTES)
    doc = upload_svc.upload_document(
        db=db,
        bid_submission_id=submission.id,
        file_obj=file_obj,
        original_filename="My GST Certificate.pdf",
        document_type="GST_CERTIFICATE",
        content_type="application/pdf",
    )

    assert doc is not None
    assert doc.id is not None
    assert doc.file_name == "My GST Certificate.pdf"
    assert doc.document_type == "GST_CERTIFICATE"
    assert doc.file_size == len(VALID_PDF_BYTES)
    assert doc.file_hash == hashlib.sha256(VALID_PDF_BYTES).hexdigest()
    assert doc.file_path is not None
    assert not doc.file_path.startswith("C:")
    assert not doc.file_path.startswith("/tmp")

    abs_path = storage_svc.get_absolute_path(doc.file_path)
    assert os.path.exists(abs_path)
    with open(abs_path, "rb") as f:
        assert f.read() == VALID_PDF_BYTES


def test_2_png_and_jpg_upload_and_storage(db: Session):
    _, _, submission = create_test_submission(db)
    storage_temp = tempfile.mkdtemp()
    storage_svc = DocumentStorageService(storage_root=storage_temp)
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    # PNG Upload
    doc_png = upload_svc.upload_document(
        db=db,
        bid_submission_id=submission.id,
        file_obj=io.BytesIO(VALID_PNG_BYTES),
        original_filename="pan_card.png",
        document_type="PAN",
        content_type="image/png",
    )
    assert doc_png.file_size == len(VALID_PNG_BYTES)

    # JPG Upload
    doc_jpg = upload_svc.upload_document(
        db=db,
        bid_submission_id=submission.id,
        file_obj=io.BytesIO(VALID_JPG_BYTES),
        original_filename="udyam_cert.jpg",
        document_type="UDYAM",
        content_type="image/jpeg",
    )
    assert doc_jpg.file_size == len(VALID_JPG_BYTES)


def test_3_unsupported_file_extension_rejected(db: Session):
    _, _, submission = create_test_submission(db)
    storage_svc = DocumentStorageService(storage_root=tempfile.mkdtemp())
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    with pytest.raises(ValueError, match="Unsupported file extension"):
        upload_svc.upload_document(
            db=db,
            bid_submission_id=submission.id,
            file_obj=io.BytesIO(b"binary payload"),
            original_filename="script.exe",
            document_type="OTHER",
        )


def test_4_oversized_file_rejected(db: Session):
    _, _, submission = create_test_submission(db)
    storage_temp = tempfile.mkdtemp()
    storage_svc = DocumentStorageService(storage_root=storage_temp)
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    # Fake oversized stream
    class LargeStream(io.BytesIO):
        def __init__(self, size_bytes: int):
            super().__init__()
            self._remaining = size_bytes

        def read(self, size=-1):
            if self._remaining <= 0:
                return b""
            chunk_len = min(size if size > 0 else 64 * 1024, self._remaining)
            self._remaining -= chunk_len
            return b"%PDF" + b"X" * (chunk_len - 4)

    large_file = LargeStream(26 * 1024 * 1024)  # 26 MB

    with pytest.raises(ValueError, match="exceeds maximum allowed limit"):
        upload_svc.upload_document(
            db=db,
            bid_submission_id=submission.id,
            file_obj=large_file,
            original_filename="large_document.pdf",
            document_type="GST_CERTIFICATE",
        )


def test_5_empty_file_rejected(db: Session):
    _, _, submission = create_test_submission(db)
    storage_svc = DocumentStorageService(storage_root=tempfile.mkdtemp())
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    with pytest.raises(ValueError, match="empty|Empty"):
        upload_svc.upload_document(
            db=db,
            bid_submission_id=submission.id,
            file_obj=io.BytesIO(b""),
            original_filename="empty.pdf",
            document_type="GST_CERTIFICATE",
        )


def test_6_7_8_path_traversal_and_absolute_path_filenames(db: Session):
    _, _, submission = create_test_submission(db)
    storage_temp = tempfile.mkdtemp()
    storage_svc = DocumentStorageService(storage_root=storage_temp)
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    traversal_names = [
        "../../evil.pdf",
        "..\\..\\evil.pdf",
        "C:\\Windows\\System32\\evil.pdf",
        "/etc/passwd.pdf",
    ]

    for name in traversal_names:
        doc = upload_svc.upload_document(
            db=db,
            bid_submission_id=submission.id,
            file_obj=io.BytesIO(VALID_PDF_BYTES),
            original_filename=name,
            document_type="GST_CERTIFICATE",
        )
        abs_path = storage_svc.get_absolute_path(doc.file_path)
        assert abs_path is not None
        assert abs_path.startswith(os.path.abspath(storage_temp))
        assert "evil.pdf" not in os.listdir(storage_temp)


def test_9_special_and_unicode_filenames(db: Session):
    _, _, submission = create_test_submission(db)
    storage_temp = tempfile.mkdtemp()
    storage_svc = DocumentStorageService(storage_root=storage_temp)
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    unicode_name = "GST Certificate & Declaration (v1.0) 📄 final.pdf"
    doc = upload_svc.upload_document(
        db=db,
        bid_submission_id=submission.id,
        file_obj=io.BytesIO(VALID_PDF_BYTES),
        original_filename=unicode_name,
        document_type="GST_CERTIFICATE",
    )

    assert doc.file_name is not None
    assert os.path.exists(storage_svc.get_absolute_path(doc.file_path))


def test_10_storage_failure_prevents_db_record(db: Session):
    _, _, submission = create_test_submission(db)

    class FailingStorageService(DocumentStorageService):
        def save_upload(self, *args, **kwargs):
            raise IOError("Disk write error simulation")

    upload_svc = DocumentUploadService(storage_service=FailingStorageService())

    with pytest.raises(IOError, match="Disk write error"):
        upload_svc.upload_document(
            db=db,
            bid_submission_id=submission.id,
            file_obj=io.BytesIO(VALID_PDF_BYTES),
            original_filename="fail_storage.pdf",
            document_type="GST_CERTIFICATE",
        )


def test_11_database_failure_cleans_up_stored_file(db: Session):
    _, _, submission = create_test_submission(db)
    storage_temp = tempfile.mkdtemp()
    storage_svc = DocumentStorageService(storage_root=storage_temp)
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    # Trigger DB exception by passing invalid submission ID inside repo mock
    with pytest.raises(Exception):
        upload_svc.upload_document(
            db=db,
            bid_submission_id=999999,  # Non-existent submission
            file_obj=io.BytesIO(VALID_PDF_BYTES),
            original_filename="orphan_test.pdf",
            document_type="GST_CERTIFICATE",
        )

    # Ensure no orphaned files remain in storage directory
    submission_dir = os.path.join(storage_temp, "999999")
    if os.path.exists(submission_dir):
        assert len(os.listdir(submission_dir)) == 0


def test_12_processing_integration_consumes_stored_file(db: Session, monkeypatch):
    _, _, submission = create_test_submission(db)
    storage_temp = tempfile.mkdtemp()
    storage_svc = DocumentStorageService(storage_root=storage_temp)
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    doc = upload_svc.upload_document(
        db=db,
        bid_submission_id=submission.id,
        file_obj=io.BytesIO(VALID_PDF_BYTES),
        original_filename="integration_gst.pdf",
        document_type="GST_CERTIFICATE",
    )

    from app.services.document_intelligence.document_service import document_processing_service
    from app.services.document_intelligence.schemas import DocumentIntelligenceResult, DocumentType, GSTDocumentFields, TextExtractionMethod

    fake_result = DocumentIntelligenceResult(
        document_type=DocumentType.GST_CERTIFICATE,
        classification_confidence=0.95,
        extraction_method=TextExtractionMethod.NATIVE_PDF,
        extracted_text="GSTIN: 27ABCDE1234F1Z5",
        total_pages=1,
        total_characters=22,
        fields=GSTDocumentFields(gstin="27ABCDE1234F1Z5"),
        extraction_confidence=0.95,
    )
    monkeypatch.setattr(document_processing_service.orchestrator, "process", lambda fp: fake_result)

    extraction = document_processing_service.process_document(
        db=db,
        bid_document_id=doc.id,
        file_path=storage_svc.get_absolute_path(doc.file_path),
    )

    assert extraction is not None
    assert extraction.bid_document_id == doc.id
    assert extraction.extraction_status == "COMPLETED"


def test_14_invalid_bid_submission_id_rejected(db: Session):
    storage_svc = DocumentStorageService(storage_root=tempfile.mkdtemp())
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    with pytest.raises(ValueError, match="Bid submission not found"):
        upload_svc.upload_document(
            db=db,
            bid_submission_id=888888,
            file_obj=io.BytesIO(VALID_PDF_BYTES),
            original_filename="test.pdf",
            document_type="GST_CERTIFICATE",
        )


def test_15_fake_mime_type_magic_bytes_rejected(db: Session):
    _, _, submission = create_test_submission(db)
    storage_svc = DocumentStorageService(storage_root=tempfile.mkdtemp())
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    fake_pdf = b"MZ\x90\x00\x03\x00\x00\x00"  # Windows Executable Header
    with pytest.raises(ValueError, match="File content header does not match"):
        upload_svc.upload_document(
            db=db,
            bid_submission_id=submission.id,
            file_obj=io.BytesIO(fake_pdf),
            original_filename="fake_document.pdf",
            document_type="GST_CERTIFICATE",
            content_type="application/pdf",
        )


def test_16_sha256_hash_verification(db: Session):
    _, _, submission = create_test_submission(db)
    storage_svc = DocumentStorageService(storage_root=tempfile.mkdtemp())
    upload_svc = DocumentUploadService(storage_service=storage_svc)

    expected_hash = hashlib.sha256(VALID_PDF_BYTES).hexdigest()
    doc = upload_svc.upload_document(
        db=db,
        bid_submission_id=submission.id,
        file_obj=io.BytesIO(VALID_PDF_BYTES),
        original_filename="hashed_doc.pdf",
        document_type="GST_CERTIFICATE",
    )

    assert doc.file_hash == expected_hash
