from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.services.rag.generator_schema import (
    ExtractedRequirement,
    RequirementExtractionResponse,
)
from app.services.rag import requirement_service as requirement_service_module
import app.api.routes.tenders as tenders_route_module


import pytest
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


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app)


class FakeRAGService:
    def __init__(self):
        self.ingested_documents = []
        self.extraction_queries = []

    def ingest_document(
        self,
        text,
        source_document,
    ):
        self.ingested_documents.append(
            {
                "text": text,
                "source_document": source_document,
            }
        )

        return []

    def extract_requirements(
        self,
        query,
        top_k=5,
    ):
        self.extraction_queries.append(
            {
                "query": query,
                "top_k": top_k,
            }
        )

        return RequirementExtractionResponse(
            requirements=[
                ExtractedRequirement(
                    requirement_type="GST",
                    requirement_name="GST Registration",
                    description=(
                        "The bidder must possess "
                        "valid GST registration."
                    ),
                    is_required=True,
                    validation_config=None,
                    source_document="demo-tender.pdf",
                    source_chunk_ids=[
                        "demo-tender.pdf:chunk:0"
                    ],
                )
            ]
        )


def create_test_tender(db):
    tender = Tender(
        title="RAG API Test Tender",
        reference_number="RAG-API-TEST-001",
        description="Tender used for RAG API testing.",
        status="DRAFT",
    )

    db.add(tender)
    db.commit()
    db.refresh(tender)

    return tender


def test_rag_requirement_extraction_api():
    db = SessionLocal()
    tender = None

    fake_rag = FakeRAGService()

    original_requirement_rag = (
        requirement_service_module.requirement_service.rag
    )

    original_route_rag = (
        tenders_route_module.rag_service
    )

    try:
        tender = create_test_tender(db)

        # Patch the RAG instance used by RequirementService
        requirement_service_module.requirement_service.rag = (
            fake_rag
        )

        # Patch the RAG instance used directly by the API route
        tenders_route_module.rag_service = fake_rag

        response = client.post(
            f"/tenders/{tender.id}/requirements/extract",
            json={
                "text": (
                    "The bidder must possess "
                    "valid GST registration."
                ),
                "source_document": "demo-tender.pdf",
                "query": (
                    "Extract all statutory "
                    "requirements."
                ),
                "top_k": 5,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert "requirements" in data
        assert len(data["requirements"]) == 1

        requirement = data["requirements"][0]

        assert (
            requirement["requirement_type"]
            == "GST"
        )

        assert (
            requirement["requirement_name"]
            == "GST Registration"
        )

        assert (
            requirement["source_document"]
            == "demo-tender.pdf"
        )

        assert (
            requirement["source_chunk_ids"]
            == ["demo-tender.pdf:chunk:0"]
        )

        # Verify that the API route called
        # FakeRAGService.ingest_document()
        assert (
            fake_rag.ingested_documents
            == [
                {
                    "text": (
                        "The bidder must possess "
                        "valid GST registration."
                    ),
                    "source_document": (
                        "demo-tender.pdf"
                    ),
                }
            ]
        )

        # Verify that the RequirementService called
        # FakeRAGService.extract_requirements()
        assert (
            fake_rag.extraction_queries
            == [
                {
                    "query": (
                        "Extract all statutory "
                        "requirements."
                    ),
                    "top_k": 5,
                }
            ]
        )

        # Verify that the requirement was actually
        # persisted into the database.
        persisted_requirement = (
            db.query(TenderRequirement)
            .filter(
                TenderRequirement.tender_id
                == tender.id
            )
            .first()
        )

        assert persisted_requirement is not None

        assert (
            persisted_requirement.requirement_type
            == "GST"
        )

        assert (
            persisted_requirement.requirement_name
            == "GST Registration"
        )

        assert (
            persisted_requirement.source_document
            == "demo-tender.pdf"
        )

        assert (
            persisted_requirement.source_chunk_ids
            == ["demo-tender.pdf:chunk:0"]
        )

    finally:
        # Restore the original RAG references.
        requirement_service_module.requirement_service.rag = (
            original_requirement_rag
        )

        tenders_route_module.rag_service = (
            original_route_rag
        )

        # Clean up database state created by this test.
        db.rollback()

        if tender is not None:
            db.query(TenderRequirement).filter(
                TenderRequirement.tender_id
                == tender.id
            ).delete(
                synchronize_session=False
            )

            db.delete(tender)
            db.commit()

        db.close()


def test_rag_requirement_extraction_tender_not_found():
    fake_rag = FakeRAGService()

    original_requirement_rag = (
        requirement_service_module.requirement_service.rag
    )

    try:
        requirement_service_module.requirement_service.rag = (
            fake_rag
        )

        response = client.post(
            "/tenders/999999/requirements/extract",
            json={
                "text": (
                    "The bidder must possess "
                    "valid GST registration."
                ),
                "source_document": "demo-tender.pdf",
                "query": "Extract requirements.",
                "top_k": 5,
            },
        )

        assert response.status_code == 404

        assert (
            response.json()["detail"]
            == "Tender not found: 999999"
        )

        # RAG should not be called when the tender
        # does not exist.
        assert (
            fake_rag.ingested_documents == []
        )

        assert (
            fake_rag.extraction_queries == []
        )

    finally:
        requirement_service_module.requirement_service.rag = (
            original_requirement_rag
        )