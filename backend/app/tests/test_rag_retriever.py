import uuid

import chromadb
import pytest

from app.services.rag.chunker import document_chunker
from app.services.rag.embeddings import embedding_service
from app.services.rag.retriever import Retriever


class IsolatedVectorStore:
    """
    Isolated in-memory ChromaDB store for tests.

    This prevents persistent application data from
    affecting retrieval test results.
    """

    def __init__(self):
        self.client = chromadb.EphemeralClient()

        self.collection = (
            self.client.create_collection(
                name=f"test_{uuid.uuid4().hex}"
            )
        )

    def count(self):
        return self.collection.count()


def test_empty_query_returns_error():

    store = IsolatedVectorStore()

    retriever = Retriever(
        store=store,
        embeddings=embedding_service,
    )

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        retriever.retrieve("")


def test_invalid_top_k_returns_error():

    store = IsolatedVectorStore()

    retriever = Retriever(
        store=store,
        embeddings=embedding_service,
    )

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):
        retriever.retrieve(
            "GST registration",
            top_k=0,
        )


def test_empty_vector_store_returns_no_results():

    store = IsolatedVectorStore()

    retriever = Retriever(
        store=store,
        embeddings=embedding_service,
    )

    results = retriever.retrieve(
        "GST registration"
    )

    assert results == []


def test_retrieval_returns_relevant_document():

    store = IsolatedVectorStore()

    chunks = document_chunker.chunk(
        """
        The bidder must possess a valid GST
        registration certificate.

        The bidder shall submit audited financial
        statements for the previous three years.

        The bidder must provide proof of registered
        office address.
        """,
        "retrieval-test-tender.txt",
    )

    embeddings = (
        embedding_service.embed_documents(
            [
                chunk.text
                for chunk in chunks
            ]
        )
    )

    store.collection.add(
        ids=[
            chunk.chunk_id
            for chunk in chunks
        ],
        documents=[
            chunk.text
            for chunk in chunks
        ],
        embeddings=embeddings,
        metadatas=[
            {
                "source_document":
                    chunk.source_document,
                "chunk_index":
                    chunk.chunk_index,
            }
            for chunk in chunks
        ],
    )

    retriever = Retriever(
        store=store,
        embeddings=embedding_service,
    )

    results = retriever.retrieve(
        "What GST registration is required?",
        top_k=1,
    )

    assert len(results) == 1

    result = results[0]

    assert (
        "GST" in result.text
        or "gst" in result.text.lower()
    )

    assert (
        result.source_document
        == "retrieval-test-tender.txt"
    )

    assert result.chunk_id is not None

    assert result.chunk_index >= 0

    assert result.distance >= 0


def test_retrieval_preserves_source_metadata():

    store = IsolatedVectorStore()

    chunks = document_chunker.chunk(
        """
        The bidder must have a valid GST
        registration and must provide the
        corresponding registration details.
        """,
        "metadata-test-tender.pdf",
    )

    embeddings = (
        embedding_service.embed_documents(
            [
                chunk.text
                for chunk in chunks
            ]
        )
    )

    store.collection.add(
        ids=[
            chunk.chunk_id
            for chunk in chunks
        ],
        documents=[
            chunk.text
            for chunk in chunks
        ],
        embeddings=embeddings,
        metadatas=[
            {
                "source_document":
                    chunk.source_document,
                "chunk_index":
                    chunk.chunk_index,
            }
            for chunk in chunks
        ],
    )

    retriever = Retriever(
        store=store,
        embeddings=embedding_service,
    )

    results = retriever.retrieve(
        "GST registration details",
        top_k=1,
    )

    assert len(results) == 1

    result = results[0]

    assert (
        result.source_document
        == "metadata-test-tender.pdf"
    )

    assert result.chunk_index == 0