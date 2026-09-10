from unittest.mock import Mock

import pytest

from app.services.rag.generator import RequirementGenerator
from app.services.rag.generator_schema import (
    ExtractedRequirement,
    RequirementExtractionResponse,
)


def create_generator():
    return RequirementGenerator(
        api_key="test-api-key",
        model="gemini-3.6-flash",
    )


def valid_response():
    return RequirementExtractionResponse(
        requirements=[
            ExtractedRequirement(
                requirement_type="GST",
                requirement_name="GST Registration Certificate",
                description=(
                    "The bidder shall possess a valid "
                    "GST registration certificate."
                ),
                is_required=True,
                validation_config=None,
                source_document="tender.pdf",
                source_chunk_ids=[
                    "tender.pdf:chunk:0"
                ],
            )
        ]
    )


def test_empty_query_returns_error():

    generator = create_generator()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        generator.generate_requirements(
            query="",
            retrieved_context=[
                {
                    "chunk_id": "chunk:0",
                    "text": "GST registration required.",
                    "source_document": "tender.pdf",
                }
            ],
        )


def test_empty_context_returns_error():

    generator = create_generator()

    with pytest.raises(
        ValueError,
        match="Retrieved context cannot be empty",
    ):
        generator.generate_requirements(
            query="GST requirement",
            retrieved_context=[],
        )


def test_missing_api_key_returns_error():

    generator = RequirementGenerator(
        api_key=None,
        model="gemini-3.6-flash",
    )

    generator.client = None

    with pytest.raises(
        RuntimeError,
        match="GEMINI_API_KEY is not configured",
    ):
        generator.generate_requirements(
            query="GST requirement",
            retrieved_context=[
                {
                    "chunk_id": "chunk:0",
                    "text": "GST registration required.",
                    "source_document": "tender.pdf",
                }
            ],
        )


def test_valid_gemini_response_is_parsed():

    generator = create_generator()

    expected = valid_response()

    mock_response = Mock()
    mock_response.output_text = (
        expected.model_dump_json()
    )

    generator.client = Mock()
    generator.client.interactions.create.return_value = (
        mock_response
    )

    result = generator.generate_requirements(
        query="What GST requirement must the bidder satisfy?",
        retrieved_context=[
            {
                "chunk_id": "tender.pdf:chunk:0",
                "text": (
                    "The bidder shall possess a valid "
                    "GST registration certificate."
                ),
                "source_document": "tender.pdf",
            }
        ],
    )

    assert isinstance(
        result,
        RequirementExtractionResponse,
    )

    assert len(result.requirements) == 1

    requirement = result.requirements[0]

    assert requirement.requirement_type == "GST"

    assert (
        requirement.requirement_name
        == "GST Registration Certificate"
    )

    assert requirement.is_required is True


def test_gemini_receives_query_and_context():

    generator = create_generator()

    expected = valid_response()

    mock_response = Mock()
    mock_response.output_text = (
        expected.model_dump_json()
    )

    generator.client = Mock()
    generator.client.interactions.create.return_value = (
        mock_response
    )

    generator.generate_requirements(
        query="What GST requirement must the bidder satisfy?",
        retrieved_context=[
            {
                "chunk_id": "gst:chunk:7",
                "text": (
                    "The bidder must possess "
                    "valid GST registration."
                ),
                "source_document": "bid.pdf",
            }
        ],
    )

    call = (
        generator.client
        .interactions
        .create
    )

    call.assert_called_once()

    kwargs = call.call_args.kwargs

    assert kwargs["model"] == "gemini-3.6-flash"

    assert (
        "GST requirement"
        in kwargs["input"]
    )

    assert "gst:chunk:7" in kwargs["input"]

    assert "bid.pdf" in kwargs["input"]

    assert (
        "valid GST registration"
        in kwargs["input"]
    )


def test_source_metadata_is_preserved():

    generator = create_generator()

    response = RequirementExtractionResponse(
        requirements=[
            ExtractedRequirement(
                requirement_type="GST",
                requirement_name="GST Registration",
                description="Valid GST registration is required.",
                is_required=True,
                validation_config=None,
                source_document="source.pdf",
                source_chunk_ids=[
                    "source.pdf:chunk:12"
                ],
            )
        ]
    )

    mock_response = Mock()
    mock_response.output_text = (
        response.model_dump_json()
    )

    generator.client = Mock()
    generator.client.interactions.create.return_value = (
        mock_response
    )

    result = generator.generate_requirements(
        query="GST requirement",
        retrieved_context=[
            {
                "chunk_id": "source.pdf:chunk:12",
                "text": "Valid GST registration is required.",
                "source_document": "source.pdf",
            }
        ],
    )

    requirement = result.requirements[0]

    assert (
        requirement.source_document
        == "source.pdf"
    )

    assert (
        requirement.source_chunk_ids
        == ["source.pdf:chunk:12"]
    )


def test_invalid_gemini_json_returns_validation_error():

    generator = create_generator()

    mock_response = Mock()
    mock_response.output_text = (
        '{"requirements": [{"requirement_type": "GST"}]}'
    )

    generator.client = Mock()
    generator.client.interactions.create.return_value = (
        mock_response
    )

    with pytest.raises(Exception):
        generator.generate_requirements(
            query="GST requirement",
            retrieved_context=[
                {
                    "chunk_id": "chunk:0",
                    "text": "GST registration required.",
                    "source_document": "tender.pdf",
                }
            ],
        )