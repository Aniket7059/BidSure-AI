import pytest
from pydantic import ValidationError

from app.services.document_intelligence.schemas import (
    DocumentIntelligenceResult,
    DocumentType,
    GSTDocumentFields,
    TextExtractionMethod,
)


def test_document_intelligence_result_is_valid():
    result = DocumentIntelligenceResult(
        document_type=DocumentType.GST_CERTIFICATE,
        classification_confidence=0.98,
        extraction_method=TextExtractionMethod.NATIVE_PDF,
        extracted_text="GSTIN: 09ABCDE1234F1Z5",
        total_pages=2,
        total_characters=27,
        fields=GSTDocumentFields(
            gstin="09ABCDE1234F1Z5",
            legal_name="ABC PRIVATE LIMITED",
            status="Active",
        ),
        extraction_confidence=0.95,
    )

    assert result.document_type == DocumentType.GST_CERTIFICATE
    assert result.classification_confidence == 0.98
    assert result.extraction_method == TextExtractionMethod.NATIVE_PDF
    assert result.total_pages == 2
    assert result.fields.gstin == "09ABCDE1234F1Z5"
    assert result.extraction_confidence == 0.95


def test_ocr_extraction_method_is_supported():
    result = DocumentIntelligenceResult(
        document_type=DocumentType.GST_CERTIFICATE,
        classification_confidence=0.91,
        extraction_method=TextExtractionMethod.OCR,
        extracted_text="GSTIN: 09ABCDE1234F1Z5",
        total_pages=1,
        total_characters=22,
        fields=GSTDocumentFields(
            gstin="09ABCDE1234F1Z5",
        ),
        extraction_confidence=0.87,
    )

    assert result.extraction_method == TextExtractionMethod.OCR


def test_classification_confidence_cannot_exceed_one():
    with pytest.raises(ValidationError):
        DocumentIntelligenceResult(
            document_type=DocumentType.GST_CERTIFICATE,
            classification_confidence=1.1,
            extraction_method=TextExtractionMethod.NATIVE_PDF,
            extracted_text="GST document",
            total_pages=1,
            total_characters=12,
            fields=GSTDocumentFields(),
            extraction_confidence=0.9,
        )


def test_extraction_confidence_cannot_be_negative():
    with pytest.raises(ValidationError):
        DocumentIntelligenceResult(
            document_type=DocumentType.GST_CERTIFICATE,
            classification_confidence=0.9,
            extraction_method=TextExtractionMethod.NATIVE_PDF,
            extracted_text="GST document",
            total_pages=1,
            total_characters=12,
            fields=GSTDocumentFields(),
            extraction_confidence=-0.1,
        )


def test_negative_page_count_is_rejected():
    with pytest.raises(ValidationError):
        DocumentIntelligenceResult(
            document_type=DocumentType.GST_CERTIFICATE,
            classification_confidence=0.9,
            extraction_method=TextExtractionMethod.NATIVE_PDF,
            extracted_text="GST document",
            total_pages=-1,
            total_characters=12,
            fields=GSTDocumentFields(),
            extraction_confidence=0.9,
        )


def test_mismatched_document_type_and_fields_are_rejected():
    from app.services.document_intelligence.schemas import PANDocumentFields

    with pytest.raises(ValueError, match="does not match"):
        DocumentIntelligenceResult(
            document_type=DocumentType.GST_CERTIFICATE,
            classification_confidence=0.9,
            extraction_method=TextExtractionMethod.NATIVE_PDF,
            extracted_text="GST document",
            total_pages=1,
            total_characters=12,
            fields=PANDocumentFields(
                pan_number="ABCDE1234F",
            ),
            extraction_confidence=0.9,
        )