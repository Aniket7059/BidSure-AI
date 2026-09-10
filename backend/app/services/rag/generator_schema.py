from pydantic import BaseModel, Field

from app.core.taxonomy import RequirementType


class ExtractedRequirement(BaseModel):
    """
    Structured representation of a requirement identified
    from tender-document context.
    """

    requirement_type: RequirementType = Field(
        description="Canonical requirement type.",
    )

    requirement_name: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    is_required: bool

    validation_config: str | None = None

    source_document: str = Field(
        min_length=1,
    )

    source_chunk_ids: list[str] = Field(
        min_length=1,
    )


class RequirementExtractionResponse(BaseModel):
    """
    Structured response produced by the AI requirement
    extraction layer.
    """

    requirements: list[ExtractedRequirement]