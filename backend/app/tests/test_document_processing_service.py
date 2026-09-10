from datetime import datetime

from app.models.document_extraction import DocumentExtraction
from app.services.document_intelligence.document_service import (
    DocumentProcessingService,
)
from app.services.document_intelligence.schemas import (
    DocumentIntelligenceResult,
    DocumentType,
    GSTDocumentFields,
    TextExtractionMethod,
)


class FakeRepository:
    def __init__(self):
        self.created = []

    def create(self, db, extraction):
        extraction.id = len(self.created) + 1
        self.created.append(extraction)
        return extraction


class FakeOrchestrator:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.received_file_path = None

    def process(self, file_path):
        self.received_file_path = file_path

        if self.error:
            raise self.error

        return self.result


class FakeDB:
    def __init__(self):
        self.commit_count = 0
        self.refresh_count = 0

    def commit(self):
        self.commit_count += 1

    def refresh(self, obj):
        self.refresh_count += 1


def create_result():
    return DocumentIntelligenceResult(
        document_type=DocumentType.GST_CERTIFICATE,
        classification_confidence=0.97,
        extraction_method=TextExtractionMethod.NATIVE_PDF,
        extracted_text="GSTIN: 27ABCDE1234F1Z5",
        total_pages=1,
        total_characters=28,
        fields=GSTDocumentFields(
            gstin="27ABCDE1234F1Z5",
            legal_name="ABC Private Limited",
            trade_name="ABC",
            registration_date="01/01/2024",
            status="Active",
        ),
        extraction_confidence=0.95,
    )


def test_process_document_creates_extraction_record():
    orchestrator = FakeOrchestrator(
        result=create_result()
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    extraction = service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert extraction.id == 1
    assert extraction.bid_document_id == 10
    assert extraction.extraction_status == "COMPLETED"


def test_process_document_passes_file_path_to_orchestrator():
    orchestrator = FakeOrchestrator(
        result=create_result()
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert (
        orchestrator.received_file_path
        == "documents/gst.pdf"
    )


def test_success_persists_extracted_text():
    orchestrator = FakeOrchestrator(
        result=create_result()
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    extraction = service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert (
        extraction.extracted_text
        == "GSTIN: 27ABCDE1234F1Z5"
    )


def test_success_persists_structured_data():
    orchestrator = FakeOrchestrator(
        result=create_result()
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    extraction = service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert extraction.extracted_data[
        "document_type"
    ] == "GST_CERTIFICATE"

    assert extraction.extracted_data[
        "extraction_method"
    ] == "NATIVE_PDF"

    assert extraction.extracted_data[
        "fields"
    ]["gstin"] == "27ABCDE1234F1Z5"


def test_success_persists_confidence():
    orchestrator = FakeOrchestrator(
        result=create_result()
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    extraction = service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert extraction.confidence_score == 0.95


def test_success_sets_completed_at():
    orchestrator = FakeOrchestrator(
        result=create_result()
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    extraction = service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert extraction.completed_at is not None


def test_success_clears_error_message():
    orchestrator = FakeOrchestrator(
        result=create_result()
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    extraction = service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert extraction.error_message is None


def test_processing_failure_is_persisted():
    orchestrator = FakeOrchestrator(
        error=RuntimeError("OCR failed")
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    extraction = service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert extraction.extraction_status == "FAILED"
    assert extraction.error_message == "OCR failed"


def test_failure_sets_completed_at():
    orchestrator = FakeOrchestrator(
        error=RuntimeError("Gemini failed")
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    extraction = service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert extraction.completed_at is not None


def test_failure_does_not_raise_processing_exception():
    orchestrator = FakeOrchestrator(
        error=RuntimeError("Extraction failed")
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    extraction = service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert isinstance(
        extraction,
        DocumentExtraction,
    )


def test_invalid_document_id_is_rejected():
    service = DocumentProcessingService()

    try:
        service.process_document(
            db=None,
            bid_document_id=0,
            file_path="documents/gst.pdf",
        )
        assert False
    except ValueError as exc:
        assert (
            str(exc)
            == "bid_document_id must be greater than zero."
        )


def test_empty_file_path_is_rejected():
    service = DocumentProcessingService()

    try:
        service.process_document(
            db=None,
            bid_document_id=10,
            file_path="",
        )
        assert False
    except ValueError as exc:
        assert (
            str(exc)
            == "file_path cannot be empty."
        )


def test_extractor_metadata_is_set():
    orchestrator = FakeOrchestrator(
        result=create_result()
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    extraction = service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert (
        extraction.extractor_name
        == "BidSureDocumentIntelligence"
    )

    assert (
        extraction.extractor_version
        == "1.0.0"
    )


def test_database_commit_happens_after_success():
    orchestrator = FakeOrchestrator(
        result=create_result()
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert db.commit_count == 1
    assert db.refresh_count == 1


def test_database_commit_happens_after_failure():
    orchestrator = FakeOrchestrator(
        error=RuntimeError("Processing failed")
    )
    repository = FakeRepository()
    db = FakeDB()

    service = DocumentProcessingService(
        orchestrator=orchestrator,
        repository=repository,
    )

    service.process_document(
        db=db,
        bid_document_id=10,
        file_path="documents/gst.pdf",
    )

    assert db.commit_count == 1
    assert db.refresh_count == 1