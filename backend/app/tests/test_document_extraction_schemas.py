import pytest
from pydantic import ValidationError

from app.services.document_intelligence.schemas import (
    DocumentFieldExtractionResponse,
    DocumentType,
    GSTDocumentFields,
    IncomeTaxDocumentFields,
    PANDocumentFields,
    UdyamDocumentFields,
)


def test_gst_fields_are_valid():
    fields = GSTDocumentFields(
        gstin="09ABCDE1234F1Z5",
        legal_name="ABC PRIVATE LIMITED",
        trade_name="ABC",
        registration_date="15/04/2021",
        status="Active",
    )

    assert fields.gstin == "09ABCDE1234F1Z5"
    assert fields.legal_name == "ABC PRIVATE LIMITED"
    assert fields.status == "Active"


def test_udyam_fields_are_valid():
    fields = UdyamDocumentFields(
        udyam_number="UDYAM-UP-01-0012345",
        enterprise_name="ABC PRIVATE LIMITED",
        organisation_type="Private Limited Company",
        major_activity="Manufacturing",
        registration_date="15/04/2021",
    )

    assert fields.udyam_number == "UDYAM-UP-01-0012345"
    assert fields.enterprise_name == "ABC PRIVATE LIMITED"


def test_pan_fields_are_valid():
    fields = PANDocumentFields(
        pan_number="ABCDE1234F",
        name="ABC PRIVATE LIMITED",
        date_of_birth_or_incorporation="15/04/2021",
    )

    assert fields.pan_number == "ABCDE1234F"
    assert fields.name == "ABC PRIVATE LIMITED"


def test_income_tax_fields_are_valid():
    fields = IncomeTaxDocumentFields(
        pan_number="ABCDE1234F",
        assessment_year="2025-26",
        acknowledgement_number="123456789012345",
        filing_date="31/07/2025",
        gross_total_income="1500000",
        total_income="1250000",
    )

    assert fields.pan_number == "ABCDE1234F"
    assert fields.assessment_year == "2025-26"
    assert fields.total_income == "1250000"


def test_missing_optional_fields_are_allowed():
    fields = GSTDocumentFields(
        gstin="09ABCDE1234F1Z5",
    )

    assert fields.gstin == "09ABCDE1234F1Z5"
    assert fields.legal_name is None
    assert fields.trade_name is None
    assert fields.registration_date is None
    assert fields.status is None


def test_gst_extraction_response_is_valid():
    response = DocumentFieldExtractionResponse(
        document_type=DocumentType.GST_CERTIFICATE,
        fields=GSTDocumentFields(
            gstin="09ABCDE1234F1Z5",
            legal_name="ABC PRIVATE LIMITED",
            status="Active",
        ),
        confidence=0.96,
    )

    assert response.document_type == DocumentType.GST_CERTIFICATE
    assert isinstance(response.fields, GSTDocumentFields)
    assert response.confidence == 0.96


def test_udyam_extraction_response_is_valid():
    response = DocumentFieldExtractionResponse(
        document_type=DocumentType.UDYAM_CERTIFICATE,
        fields=UdyamDocumentFields(
            udyam_number="UDYAM-UP-01-0012345",
            enterprise_name="ABC PRIVATE LIMITED",
        ),
        confidence=0.94,
    )

    assert response.document_type == DocumentType.UDYAM_CERTIFICATE
    assert isinstance(response.fields, UdyamDocumentFields)


def test_pan_extraction_response_is_valid():
    response = DocumentFieldExtractionResponse(
        document_type=DocumentType.PAN,
        fields=PANDocumentFields(
            pan_number="ABCDE1234F",
            name="ABC PRIVATE LIMITED",
        ),
        confidence=0.98,
    )

    assert response.document_type == DocumentType.PAN
    assert isinstance(response.fields, PANDocumentFields)


def test_income_tax_extraction_response_is_valid():
    response = DocumentFieldExtractionResponse(
        document_type=DocumentType.INCOME_TAX,
        fields=IncomeTaxDocumentFields(
            pan_number="ABCDE1234F",
            assessment_year="2025-26",
            total_income="1250000",
        ),
        confidence=0.91,
    )

    assert response.document_type == DocumentType.INCOME_TAX
    assert isinstance(response.fields, IncomeTaxDocumentFields)


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        DocumentFieldExtractionResponse(
            document_type=DocumentType.GST_CERTIFICATE,
            fields=GSTDocumentFields(
                gstin="09ABCDE1234F1Z5",
            ),
            confidence=1.5,
        )


def test_negative_confidence_is_rejected():
    with pytest.raises(ValidationError):
        DocumentFieldExtractionResponse(
            document_type=DocumentType.GST_CERTIFICATE,
            fields=GSTDocumentFields(
                gstin="09ABCDE1234F1Z5",
            ),
            confidence=-0.1,
        )


def test_mismatched_document_type_and_fields_are_rejected():
    with pytest.raises(ValueError, match="does not match"):
        DocumentFieldExtractionResponse(
            document_type=DocumentType.GST_CERTIFICATE,
            fields=PANDocumentFields(
                pan_number="ABCDE1234F",
                name="ABC PRIVATE LIMITED",
            ),
            confidence=0.95,
        )


def test_unknown_document_type_cannot_be_structured_extracted():
    with pytest.raises(ValueError, match="not supported"):
        DocumentFieldExtractionResponse(
            document_type=DocumentType.UNKNOWN,
            fields=GSTDocumentFields(
                gstin="09ABCDE1234F1Z5",
            ),
            confidence=0.5,
        )


def test_unexpected_fields_are_rejected():
    with pytest.raises(ValidationError):
        GSTDocumentFields(
            gstin="09ABCDE1234F1Z5",
            legal_name="ABC PRIVATE LIMITED",
            fake_field="should not be accepted",
        )