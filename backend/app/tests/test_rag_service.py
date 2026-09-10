import pytest

from app.services.rag.service import RAGService


class FakeChunker:
    def chunk(self, text, source_document):
        from app.services.rag.chunker import DocumentChunk

        return [
            DocumentChunk(
                chunk_id="test:chunk:0",
                text=text,
                source_document=source_document,
                chunk_index=0,
            )
        ]


class FakeEmbeddings:
    def embed_documents(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeStore:
    def __init__(self):
        self.chunks = []
        self.embeddings = []

    def add_chunks(self, chunks, embeddings):
        self.chunks = chunks
        self.embeddings = embeddings


class FakeRetriever:
    def retrieve(self, query, top_k=5):
        return [
            {
                "query": query,
                "top_k": top_k,
            }
        ]


class NoOpGenerator:
    """
    Generator that should never be called in tests
    where validation should happen before generation.
    """

    def generate_requirements(
        self,
        query,
        retrieved_context,
    ):
        raise AssertionError(
            "Generator should not be called."
        )


def create_service():
    return RAGService(
        chunker=FakeChunker(),
        embeddings=FakeEmbeddings(),
        store=FakeStore(),
        document_retriever=FakeRetriever(),
        generator=NoOpGenerator(),
    )


def test_ingest_document_rejects_empty_text():

    service = create_service()

    with pytest.raises(
        ValueError,
        match="Document text cannot be empty",
    ):
        service.ingest_document(
            text="",
            source_document="tender.pdf",
        )


def test_ingest_document_rejects_empty_source():

    service = create_service()

    with pytest.raises(
        ValueError,
        match="source_document cannot be empty",
    ):
        service.ingest_document(
            text="Tender requirement text",
            source_document="",
        )


def test_ingest_document_runs_pipeline():

    service = create_service()

    chunks = service.ingest_document(
        text="Bidder must possess valid GST registration.",
        source_document="tender.pdf",
    )

    assert len(chunks) == 1

    assert (
        chunks[0].source_document
        == "tender.pdf"
    )

    assert (
        service.store.chunks
        == chunks
    )

    assert len(
        service.store.embeddings
    ) == 1

    assert (
        service.store.embeddings[0]
        == [0.1, 0.2, 0.3]
    )


def test_retrieve_delegates_to_retriever():

    service = create_service()

    results = service.retrieve(
        query="GST registration",
        top_k=3,
    )

    assert len(results) == 1

    assert (
        results[0]["query"]
        == "GST registration"
    )

    assert (
        results[0]["top_k"]
        == 3
    )


def test_extract_requirements_retrieves_context_and_generates_requirements():

    class FakeRetriever:
        def retrieve(self, query, top_k=5):
            return [
                type(
                    "Result",
                    (),
                    {
                        "chunk_id": "gst:chunk:0",
                        "text": (
                            "The bidder must possess "
                            "valid GST registration."
                        ),
                        "source_document": "tender.pdf",
                    },
                )()
            ]

    class FakeGenerator:
        def __init__(self):
            self.query = None
            self.context = None

        def generate_requirements(
            self,
            query,
            retrieved_context,
        ):
            from app.services.rag.generator_schema import (
                ExtractedRequirement,
                RequirementExtractionResponse,
            )

            self.query = query
            self.context = retrieved_context

            return RequirementExtractionResponse(
                requirements=[
                    ExtractedRequirement(
                        requirement_type="GST",
                        requirement_name="GST Registration",
                        description=(
                            "Valid GST registration "
                            "is required."
                        ),
                        is_required=True,
                        validation_config=None,
                        source_document="tender.pdf",
                        source_chunk_ids=[
                            "gst:chunk:0"
                        ],
                    )
                ]
            )

    fake_generator = FakeGenerator()

    service = RAGService(
        chunker=FakeChunker(),
        embeddings=FakeEmbeddings(),
        store=FakeStore(),
        document_retriever=FakeRetriever(),
        generator=fake_generator,
    )

    result = service.extract_requirements(
        query="What GST requirement applies?",
        top_k=3,
    )

    assert len(result.requirements) == 1

    assert (
        result.requirements[0].requirement_type
        == "GST"
    )

    assert fake_generator.query == (
        "What GST requirement applies?"
    )

    assert len(fake_generator.context) == 1

    assert (
        fake_generator.context[0]["chunk_id"]
        == "gst:chunk:0"
    )

    assert (
        fake_generator.context[0]["source_document"]
        == "tender.pdf"
    )


def test_extract_requirements_with_no_results_returns_empty():

    class EmptyRetriever:
        def retrieve(self, query, top_k=5):
            return []

    class FailingGenerator:
        def generate_requirements(
            self,
            query,
            retrieved_context,
        ):
            raise AssertionError(
                "Generator should not be called."
            )

    service = RAGService(
        chunker=FakeChunker(),
        embeddings=FakeEmbeddings(),
        store=FakeStore(),
        document_retriever=EmptyRetriever(),
        generator=FailingGenerator(),
    )

    result = service.extract_requirements(
        query="GST requirement",
    )

    assert result.requirements == []


def test_extract_requirements_rejects_empty_query():

    service = create_service()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        service.extract_requirements(
            query="",
        )