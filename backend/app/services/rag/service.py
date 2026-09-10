from app.services.rag.chunker import (
    DocumentChunk,
    document_chunker,
)
from app.services.rag.embeddings import (
    embedding_service,
)
from app.services.rag.generator import (
    RequirementGenerator,
    requirement_generator,
)
from app.services.rag.generator_schema import (
    RequirementExtractionResponse,
)
from app.services.rag.retriever import (
    RetrievalResult,
    Retriever,
    retriever,
)
from app.services.rag.vector_store import (
    VectorStore,
    vector_store,
)


class RAGService:
    """
    Coordinates the complete RAG pipeline.

    Responsibilities:
    - Chunk extracted document text
    - Generate embeddings
    - Store chunks in the vector database
    - Retrieve relevant chunks
    - Generate structured requirements from retrieved context

    Database persistence of generated requirements is handled
    separately by the appropriate repository/service.
    """

    def __init__(
        self,
        chunker=document_chunker,
        embeddings=embedding_service,
        store=vector_store,
        document_retriever=retriever,
        generator=requirement_generator,
    ):
        self.chunker = chunker
        self.embeddings = embeddings
        self.store = store
        self.retriever = document_retriever
        self.generator = generator

    def ingest_document(
        self,
        text: str,
        source_document: str,
    ) -> list[DocumentChunk]:
        """
        Process and index a document.

        Pipeline:

            text
              ↓
            chunks
              ↓
            embeddings
              ↓
            vector store
        """

        if not text or not text.strip():
            raise ValueError(
                "Document text cannot be empty."
            )

        if not source_document or not source_document.strip():
            raise ValueError(
                "source_document cannot be empty."
            )

        chunks = self.chunker.chunk(
            text=text,
            source_document=source_document,
        )

        if not chunks:
            return []

        embeddings = (
            self.embeddings.embed_documents(
                [
                    chunk.text
                    for chunk in chunks
                ]
            )
        )

        self.store.add_chunks(
            chunks=chunks,
            embeddings=embeddings,
        )

        return chunks

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        source_document: str | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant document chunks.

        If source_document is provided, retrieval is restricted
        to chunks belonging to that document.
        """

        if source_document is not None:
            return self.retriever.retrieve(
                query=query,
                top_k=top_k,
                source_document=source_document,
            )

        return self.retriever.retrieve(
            query=query,
            top_k=top_k,
        )

    def extract_requirements(
        self,
        query: str,
        top_k: int = 5,
        source_document: str | None = None,
    ) -> RequirementExtractionResponse:
        """
        Retrieve relevant tender context from the specified
        document and use the LLM to extract structured
        tender requirements.

        Pipeline:

            query + source_document
                    ↓
                retrieval
                    ↓
            document-specific chunks
                    ↓
            structured context
                    ↓
                  Gemini
                    ↓
            RequirementExtractionResponse
        """

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if source_document is not None and not source_document.strip():
            raise ValueError(
                "source_document cannot be empty."
            )

        retrieved_chunks = self.retrieve(
            query=query,
            top_k=top_k,
            source_document=source_document,
        )

        if not retrieved_chunks:
            return RequirementExtractionResponse(
                requirements=[]
            )

        retrieved_context = [
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "source_document": (
                    chunk.source_document
                ),
            }
            for chunk in retrieved_chunks
        ]

        return self.generator.generate_requirements(
            query=query,
            retrieved_context=retrieved_context,
        )


rag_service = RAGService()