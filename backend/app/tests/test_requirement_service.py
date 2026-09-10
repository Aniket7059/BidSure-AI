import pytest

from app.services.rag.generator_schema import (
    ExtractedRequirement,
    RequirementExtractionResponse,
)
from app.services.rag.requirement_service import (
    RequirementService,
)


class FakeRAGService:
    def __init__(self, result):
        self.result = result
        self.query = None
        self.top_k = None

    def extract_requirements(
        self,
        query,
        top_k=5,
    ):
        self.query = query
        self.top_k = top_k

        return self.result


class FakeRequirementRepository:
    def __init__(self):
        self.created = []

    def create(
        self,
        db,
        tender_id,
        requirement_data,
    ):
        self.created.append(
            {
                "db": db,
                "tender_id": tender_id,
                "requirement_data": requirement_data,
            }
        )

        return requirement_data

    def get_duplicate(
        self,
        db,
        tender_id,
        requirement_data,
    ):
        for item in self.created:
            existing = item["requirement_data"]

            if (
                item["tender_id"] == tender_id
                and existing.requirement_type
                == requirement_data.requirement_type
                and existing.requirement_name
                == requirement_data.requirement_name
                and existing.source_document
                == requirement_data.source_document
            ):
                return existing

        return None


def create_extraction_result():
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
                source_document="tender.pdf",
                source_chunk_ids=[
                    "tender:chunk:0"
                ],
            )
        ]
    )


def test_invalid_tender_id_returns_error():

    rag = FakeRAGService(
        create_extraction_result()
    )

    repository = FakeRequirementRepository()

    service = RequirementService(
        rag=rag,
        repository=repository,
    )

    with pytest.raises(
        ValueError,
        match="tender_id must be greater than zero",
    ):
        service.extract_and_persist_requirements(
            db=None,
            tender_id=0,
            query="GST requirement",
        )

    assert repository.created == []


def test_empty_query_returns_error():

    rag = FakeRAGService(
        create_extraction_result()
    )

    repository = FakeRequirementRepository()

    service = RequirementService(
        rag=rag,
        repository=repository,
    )

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        service.extract_and_persist_requirements(
            db=None,
            tender_id=1,
            query="",
        )

    assert repository.created == []


def test_no_requirements_does_not_persist():

    extraction_result = RequirementExtractionResponse(
        requirements=[]
    )

    rag = FakeRAGService(
        extraction_result
    )

    repository = FakeRequirementRepository()

    service = RequirementService(
        rag=rag,
        repository=repository,
    )

    result = service.extract_and_persist_requirements(
        db=None,
        tender_id=1,
        query="GST requirement",
    )

    assert result == extraction_result

    assert repository.created == []


def test_requirement_is_persisted():

    extraction_result = (
        create_extraction_result()
    )

    rag = FakeRAGService(
        extraction_result
    )

    repository = FakeRequirementRepository()

    service = RequirementService(
        rag=rag,
        repository=repository,
    )

    result = service.extract_and_persist_requirements(
        db=None,
        tender_id=10,
        query="GST requirement",
        top_k=3,
    )

    assert result == extraction_result

    assert len(repository.created) == 1

    created = repository.created[0]

    assert created["tender_id"] == 10

    requirement = created[
        "requirement_data"
    ]

    assert (
        requirement.requirement_type
        == "GST"
    )

    assert (
        requirement.requirement_name
        == "GST Registration"
    )

    assert (
        requirement.description
        == "The bidder must possess "
        "valid GST registration."
    )

    assert requirement.is_required is True

    assert (
        requirement.validation_config
        is None
    )

    assert (
        requirement.source_document
        == "tender.pdf"
    )

    assert (
        requirement.source_chunk_ids
        == ["tender:chunk:0"]
    )


def test_rag_receives_query_and_top_k():

    rag = FakeRAGService(
        create_extraction_result()
    )

    repository = FakeRequirementRepository()

    service = RequirementService(
        rag=rag,
        repository=repository,
    )

    service.extract_and_persist_requirements(
        db=None,
        tender_id=5,
        query="What GST requirement applies?",
        top_k=7,
    )

    assert rag.query == (
        "What GST requirement applies?"
    )

    assert rag.top_k == 7


def test_multiple_requirements_are_persisted():

    extraction_result = (
        RequirementExtractionResponse(
            requirements=[
                ExtractedRequirement(
                    requirement_type="GST",
                    requirement_name=(
                        "GST Registration"
                    ),
                    description=(
                        "Valid GST registration "
                        "is required."
                    ),
                    is_required=True,
                    validation_config=None,
                    source_document="tender.pdf",
                    source_chunk_ids=[
                        "chunk:0"
                    ],
                ),
                ExtractedRequirement(
                    requirement_type="UDYAM",
                    requirement_name=(
                        "Udyam Registration"
                    ),
                    description=(
                        "Valid Udyam registration "
                        "is required."
                    ),
                    is_required=True,
                    validation_config=None,
                    source_document="tender.pdf",
                    source_chunk_ids=[
                        "chunk:1"
                    ],
                ),
            ]
        )
    )

    rag = FakeRAGService(
        extraction_result
    )

    repository = FakeRequirementRepository()

    service = RequirementService(
        rag=rag,
        repository=repository,
    )

    service.extract_and_persist_requirements(
        db=None,
        tender_id=20,
        query="All eligibility requirements",
    )

    assert len(repository.created) == 2

    assert (
        repository.created[0][
            "requirement_data"
        ].requirement_type
        == "GST"
    )

    assert (
        repository.created[1][
            "requirement_data"
        ].requirement_type
        == "UDYAM"
    )

    assert (
        repository.created[0]["tender_id"]
        == 20
    )

    assert (
        repository.created[1]["tender_id"]
        == 20
    )


def test_validation_config_is_preserved():

    extraction_result = (
        RequirementExtractionResponse(
            requirements=[
                ExtractedRequirement(
                    requirement_type="GST",
                    requirement_name=(
                        "GST Registration"
                    ),
                    description=(
                        "Valid GST registration "
                        "is required."
                    ),
                    is_required=True,
                    validation_config=(
                        '{"verification": "GST_PORTAL", '
                        '"required": true}'
                    ),
                    source_document="tender.pdf",
                    source_chunk_ids=[
                        "chunk:0"
                    ],
                )
            ]
        )
    )

    rag = FakeRAGService(
        extraction_result
    )

    repository = FakeRequirementRepository()

    service = RequirementService(
        rag=rag,
        repository=repository,
    )

    service.extract_and_persist_requirements(
        db=None,
        tender_id=30,
        query="GST requirement",
    )

    requirement = repository.created[0][
        "requirement_data"
    ]

    assert (
        requirement.validation_config
        == '{"verification": "GST_PORTAL", '
        '"required": true}'
    )


def test_extraction_result_is_returned_unchanged():

    extraction_result = (
        create_extraction_result()
    )

    rag = FakeRAGService(
        extraction_result
    )

    repository = FakeRequirementRepository()

    service = RequirementService(
        rag=rag,
        repository=repository,
    )

    result = service.extract_and_persist_requirements(
        db=None,
        tender_id=40,
        query="GST requirement",
    )

    assert result is extraction_result

    assert (
        result.requirements[0]
        .source_document
        == "tender.pdf"
    )

    assert (
        result.requirements[0]
        .source_chunk_ids
        == ["tender:chunk:0"]
    )


def test_duplicate_requirement_is_not_persisted():

    extraction_result = (
        create_extraction_result()
    )

    rag = FakeRAGService(
        extraction_result
    )

    repository = FakeRequirementRepository()

    service = RequirementService(
        rag=rag,
        repository=repository,
    )

    first_result = (
        service.extract_and_persist_requirements(
            db=None,
            tender_id=50,
            query="GST requirement",
        )
    )

    second_result = (
        service.extract_and_persist_requirements(
            db=None,
            tender_id=50,
            query="GST requirement",
        )
    )

    assert first_result is extraction_result
    assert second_result is extraction_result

    assert len(repository.created) == 1


def test_same_requirement_from_different_source_is_persisted():

    first_extraction = (
        RequirementExtractionResponse(
            requirements=[
                ExtractedRequirement(
                    requirement_type="GST",
                    requirement_name=(
                        "GST Registration"
                    ),
                    description=(
                        "GST registration "
                        "is required."
                    ),
                    is_required=True,
                    validation_config=None,
                    source_document=(
                        "tender_a.pdf"
                    ),
                    source_chunk_ids=[
                        "tender_a:chunk:0"
                    ],
                )
            ]
        )
    )

    second_extraction = (
        RequirementExtractionResponse(
            requirements=[
                ExtractedRequirement(
                    requirement_type="GST",
                    requirement_name=(
                        "GST Registration"
                    ),
                    description=(
                        "GST registration "
                        "is required."
                    ),
                    is_required=True,
                    validation_config=None,
                    source_document=(
                        "tender_b.pdf"
                    ),
                    source_chunk_ids=[
                        "tender_b:chunk:0"
                    ],
                )
            ]
        )
    )

    first_rag = FakeRAGService(
        first_extraction
    )

    second_rag = FakeRAGService(
        second_extraction
    )

    repository = FakeRequirementRepository()

    first_service = RequirementService(
        rag=first_rag,
        repository=repository,
    )

    second_service = RequirementService(
        rag=second_rag,
        repository=repository,
    )

    first_service.extract_and_persist_requirements(
        db=None,
        tender_id=60,
        query="GST requirement",
    )

    second_service.extract_and_persist_requirements(
        db=None,
        tender_id=60,
        query="GST requirement",
    )

    assert len(repository.created) == 2

    assert (
        repository.created[0][
            "requirement_data"
        ].source_document
        == "tender_a.pdf"
    )

    assert (
        repository.created[1][
            "requirement_data"
        ].source_document
        == "tender_b.pdf"
    )