from sqlalchemy.orm import Session

from app.repositories.tender_requirement_repository import (
    tender_requirement_repository,
)
from app.schemas.tender_requirement import (
    TenderRequirementCreate,
)
from app.services.rag.generator_schema import (
    RequirementExtractionResponse,
)
from app.services.rag.service import (
    RAGService,
    rag_service,
)


class RequirementService:
    """
    Converts AI-generated tender requirements into
    persistent TenderRequirement records.

    Responsibilities:
    - Run RAG requirement extraction.
    - Convert extracted requirements into
      TenderRequirementCreate schemas.
    - Persist requirements through the repository.

    This service does not perform:
    - document chunking
    - embedding generation
    - vector retrieval
    - LLM generation
    - compliance evaluation
    """

    def __init__(
        self,
        rag: RAGService = rag_service,
        repository=tender_requirement_repository,
    ):
        self.rag = rag
        self.repository = repository

    def extract_and_persist_requirements(
        self,
        db: Session,
        tender_id: int,
        query: str,
        source_document: str = "demo-tender.pdf",
        top_k: int = 5,
    ) -> RequirementExtractionResponse:
        """
        Extract requirements using RAG/Gemini and persist
        them as TenderRequirement records.

        Retrieval is restricted to the specified source
        document so requirements from unrelated documents
        are not included.
        """

        if tender_id <= 0:
            raise ValueError(
                "tender_id must be greater than zero."
            )

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if not source_document or not source_document.strip():
            raise ValueError(
                "source_document cannot be empty."
            )

        try:
            extraction_result = self.rag.extract_requirements(
                query=query,
                top_k=top_k,
                source_document=source_document,
            )
        except TypeError:
            extraction_result = self.rag.extract_requirements(
                query=query,
                top_k=top_k,
            )

        if not extraction_result.requirements:
            return extraction_result

        for extracted_requirement in (
            extraction_result.requirements
        ):
            validation_config_text = (
                extracted_requirement.validation_config
            )

            requirement_data = TenderRequirementCreate(
                requirement_type=(
                    extracted_requirement.requirement_type
                ),
                requirement_name=(
                    extracted_requirement.requirement_name
                ),
                description=(
                    extracted_requirement.description
                ),
                is_required=(
                    extracted_requirement.is_required
                ),
                validation_config=(
                    validation_config_text
                ),
                source_document=(
                    extracted_requirement.source_document
                ),
                source_chunk_ids=(
                    extracted_requirement.source_chunk_ids
                ),
            )

            existing_requirement = (
                self.repository.get_duplicate(
                    db,
                    tender_id,
                    requirement_data,
                )
            )

            if existing_requirement is not None:
                continue

            self.repository.create(
                db,
                tender_id,
                requirement_data,
            )

        return extraction_result


requirement_service = RequirementService()