from app.schemas.document_extraction import (
    StandardizedDocumentExtraction,
    get_extracted_fields,
)


def test_standardized_document_extraction_schema():
    extraction = StandardizedDocumentExtraction(
        document_type="GST_CERTIFICATE",
        fields={
            "gstin": "29ABCDE1234F1Z5",
            "legal_name": "Acme Private Limited",
            "registration_date": "2020-01-01",
            "status": "ACTIVE",
        },
        classification_confidence=0.98,
        extraction_method="NATIVE_PDF",
    )

    dumped = extraction.model_dump()
    assert dumped["document_type"] == "GST_CERTIFICATE"
    assert dumped["fields"]["gstin"] == "29ABCDE1234F1Z5"
    assert dumped["fields"]["legal_name"] == "Acme Private Limited"


def test_get_extracted_fields_with_standardized_structure():
    data = {
        "document_type": "GST_CERTIFICATE",
        "classification_confidence": 0.95,
        "extraction_method": "NATIVE_PDF",
        "fields": {
            "gstin": "29ABCDE1234F1Z5",
            "legal_name": "Acme Private Limited",
        },
    }

    fields = get_extracted_fields(data)
    assert fields == {
        "gstin": "29ABCDE1234F1Z5",
        "legal_name": "Acme Private Limited",
    }


def test_get_extracted_fields_with_legacy_flat_structure():
    data = {
        "gstin": "29ABCDE1234F1Z5",
        "legal_name": "Acme Private Limited",
    }

    fields = get_extracted_fields(data)
    assert fields == {
        "gstin": "29ABCDE1234F1Z5",
        "legal_name": "Acme Private Limited",
    }


def test_get_extracted_fields_with_none_or_empty():
    assert get_extracted_fields(None) == {}
    assert get_extracted_fields({}) == {}
