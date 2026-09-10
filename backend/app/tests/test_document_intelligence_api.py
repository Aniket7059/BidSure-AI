from types import SimpleNamespace
from unittest.mock import Mock
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import bid_documents
from app.api.routes.bid_documents import router
from app.database.session import get_db


from app.api.dependencies import get_current_user
from app.models.user import User


def mock_get_current_user():
    return User(
        id=1,
        full_name="Test Officer",
        email="officer@test.com",
        role="PROCUREMENT_OFFICER",
        is_active=True,
    )


def create_test_app():
    app = FastAPI()
    app.include_router(router)

    db = Mock()

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = mock_get_current_user

    return app, db


def test_process_document_returns_extraction():
    app, db = create_test_app()

    document = SimpleNamespace(
        id=1,
        file_path="uploads/gst_certificate.pdf",
    )

    extraction = SimpleNamespace(
        id=10,
        bid_document_id=1,
        extraction_status="COMPLETED",
        extracted_data={
            "document_type": "GST_CERTIFICATE",
        },
        extracted_text="GSTIN: 29ABCDE1234F1Z5",
        confidence_score=0.95,
        extractor_name="BidSureDocumentIntelligence",
        extractor_version="1.0.0",
        error_message=None,
        started_at=None,
        completed_at=None,
        created_at=datetime.now(timezone.utc),
    )

    orig_get_by_id = bid_documents.bid_document_repository.get_by_id
    orig_process_doc = bid_documents.document_processing_service.process_document

    bid_documents.bid_document_repository.get_by_id = Mock(
        return_value=document,
    )
    bid_documents.document_processing_service.process_document = Mock(
        return_value=extraction,
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/bid-submissions/documents/1/process",
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == 10
        assert data["bid_document_id"] == 1
        assert data["extraction_status"] == "COMPLETED"

        bid_documents.document_processing_service.process_document.assert_called_once_with(
            db=db,
            bid_document_id=1,
            file_path="uploads/gst_certificate.pdf",
        )
    finally:
        bid_documents.bid_document_repository.get_by_id = orig_get_by_id
        bid_documents.document_processing_service.process_document = orig_process_doc


def test_process_document_returns_404_when_document_not_found():
    app, _ = create_test_app()

    orig_get_by_id = bid_documents.bid_document_repository.get_by_id
    bid_documents.bid_document_repository.get_by_id = Mock(
        return_value=None,
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/bid-submissions/documents/999/process",
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Bid document not found."
    finally:
        bid_documents.bid_document_repository.get_by_id = orig_get_by_id


def test_get_document_extraction_returns_latest_extraction():
    app, db = create_test_app()

    document = SimpleNamespace(
        id=1,
        file_path="uploads/gst_certificate.pdf",
    )

    extraction = SimpleNamespace(
        id=10,
        bid_document_id=1,
        extraction_status="COMPLETED",
        extracted_data={
            "document_type": "GST_CERTIFICATE",
        },
        extracted_text="GSTIN: 29ABCDE1234F1Z5",
        confidence_score=0.95,
        extractor_name="BidSureDocumentIntelligence",
        extractor_version="1.0.0",
        error_message=None,
        started_at=None,
        completed_at=None,
        created_at=datetime.now(timezone.utc),
    )

    orig_get_by_id = bid_documents.bid_document_repository.get_by_id
    bid_documents.bid_document_repository.get_by_id = Mock(
        return_value=document,
    )

    repository = Mock()
    repository.get_latest_by_document_id = Mock(
        return_value=extraction,
    )

    original_repository = (
        bid_documents.DocumentExtractionRepository
    )

    bid_documents.DocumentExtractionRepository = Mock(
        return_value=repository,
    )

    try:
        client = TestClient(app)

        response = client.get(
            "/bid-submissions/documents/1/extraction",
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == 10
        assert data["bid_document_id"] == 1
        assert data["extraction_status"] == "COMPLETED"

        repository.get_latest_by_document_id.assert_called_once_with(
            db,
            1,
        )

    finally:
        bid_documents.bid_document_repository.get_by_id = orig_get_by_id
        bid_documents.DocumentExtractionRepository = (
            original_repository
        )


def test_get_document_extraction_returns_404_when_document_not_found():
    app, _ = create_test_app()

    orig_get_by_id = bid_documents.bid_document_repository.get_by_id
    bid_documents.bid_document_repository.get_by_id = Mock(
        return_value=None,
    )

    try:
        client = TestClient(app)

        response = client.get(
            "/bid-submissions/documents/999/extraction",
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Bid document not found."
    finally:
        bid_documents.bid_document_repository.get_by_id = orig_get_by_id


def test_get_document_extraction_returns_404_when_extraction_not_found():
    app, db = create_test_app()

    document = SimpleNamespace(
        id=1,
        file_path="uploads/gst_certificate.pdf",
    )

    orig_get_by_id = bid_documents.bid_document_repository.get_by_id
    bid_documents.bid_document_repository.get_by_id = Mock(
        return_value=document,
    )

    repository = Mock()
    repository.get_latest_by_document_id = Mock(
        return_value=None,
    )

    original_repository = (
        bid_documents.DocumentExtractionRepository
    )

    bid_documents.DocumentExtractionRepository = Mock(
        return_value=repository,
    )

    try:
        client = TestClient(app)

        response = client.get(
            "/bid-submissions/documents/1/extraction",
        )

        assert response.status_code == 404
        assert (
            response.json()["detail"]
            == "No extraction found for this document."
        )

    finally:
        bid_documents.bid_document_repository.get_by_id = orig_get_by_id
        bid_documents.DocumentExtractionRepository = (
            original_repository
        )