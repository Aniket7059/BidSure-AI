from unittest.mock import MagicMock, patch

import pytest

from app.services.document_intelligence.field_extractor import (
    DocumentFieldExtractor,
)
from app.services.document_intelligence.schemas import (
    DocumentFieldExtractionResponse,
    DocumentType,
    GSTDocumentFields,
    IncomeTaxDocumentFields,
    PANDocumentFields,
    UdyamDocumentFields,
)


def make_response(payload: str):
    """
    Create a mock Gemini Interactions API response.

    The current google-genai Interactions API exposes
    generated text through `response.output_text`.
    """
    response = MagicMock()
    response.output_text = payload

    return response


def test_extracts_gst_fields():
    response = make_response(
        """
        {
            "fields": {
                "gstin": "09ABCDE1234F1Z5",
                "legal_name": "ABC PRIVATE LIMITED",
                "trade_name": "ABC",
                "registration_date": "15/04/2021",
                "status": "Active"
            },
            "confidence": 0.96
        }
        """
    )

    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    with patch(
        "app.services.document_intelligence.field_extractor.genai.Client"
    ) as client_class:
        client_class.return_value.interactions.create.return_value = response

        result = extractor.extract(
            "GSTIN: 09ABCDE1234F1Z5\n"
            "Legal Name: ABC PRIVATE LIMITED\n"
            "Status: Active",
            DocumentType.GST_CERTIFICATE,
        )

    assert isinstance(result, DocumentFieldExtractionResponse)
    assert result.document_type == DocumentType.GST_CERTIFICATE
    assert isinstance(result.fields, GSTDocumentFields)
    assert result.fields.gstin == "09ABCDE1234F1Z5"
    assert result.fields.legal_name == "ABC PRIVATE LIMITED"
    assert result.confidence == 0.96


def test_extracts_udyam_fields():
    response = make_response(
        """
        {
            "fields": {
                "udyam_number": "UDYAM-UP-01-0012345",
                "enterprise_name": "ABC PRIVATE LIMITED",
                "organisation_type": "Private Limited Company",
                "major_activity": "Manufacturing",
                "registration_date": "15/04/2021"
            },
            "confidence": 0.94
        }
        """
    )

    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    with patch(
        "app.services.document_intelligence.field_extractor.genai.Client"
    ) as client_class:
        client_class.return_value.interactions.create.return_value = response

        result = extractor.extract(
            "UDYAM-UP-01-0012345\nABC PRIVATE LIMITED",
            DocumentType.UDYAM_CERTIFICATE,
        )

    assert isinstance(result.fields, UdyamDocumentFields)
    assert result.fields.udyam_number == "UDYAM-UP-01-0012345"


def test_extracts_pan_fields():
    response = make_response(
        """
        {
            "fields": {
                "pan_number": "ABCDE1234F",
                "name": "ABC PRIVATE LIMITED",
                "date_of_birth_or_incorporation": "15/04/2021"
            },
            "confidence": 0.98
        }
        """
    )

    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    with patch(
        "app.services.document_intelligence.field_extractor.genai.Client"
    ) as client_class:
        client_class.return_value.interactions.create.return_value = response

        result = extractor.extract(
            "Permanent Account Number: ABCDE1234F",
            DocumentType.PAN,
        )

    assert isinstance(result.fields, PANDocumentFields)
    assert result.fields.pan_number == "ABCDE1234F"


def test_extracts_income_tax_fields():
    response = make_response(
        """
        {
            "fields": {
                "pan_number": "ABCDE1234F",
                "assessment_year": "2025-26",
                "acknowledgement_number": "123456789012345",
                "filing_date": "31/07/2025",
                "gross_total_income": "1500000",
                "total_income": "1250000"
            },
            "confidence": 0.91
        }
        """
    )

    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    with patch(
        "app.services.document_intelligence.field_extractor.genai.Client"
    ) as client_class:
        client_class.return_value.interactions.create.return_value = response

        result = extractor.extract(
            "Assessment Year: 2025-26\n"
            "PAN: ABCDE1234F\n"
            "Total Income: 1250000",
            DocumentType.INCOME_TAX,
        )

    assert isinstance(result.fields, IncomeTaxDocumentFields)
    assert result.fields.pan_number == "ABCDE1234F"
    assert result.fields.assessment_year == "2025-26"
    assert result.fields.total_income == "1250000"


def test_missing_fields_are_returned_as_none():
    response = make_response(
        """
        {
            "fields": {
                "gstin": "09ABCDE1234F1Z5",
                "legal_name": "ABC PRIVATE LIMITED",
                "trade_name": null,
                "registration_date": null,
                "status": "Active"
            },
            "confidence": 0.88
        }
        """
    )

    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    with patch(
        "app.services.document_intelligence.field_extractor.genai.Client"
    ) as client_class:
        client_class.return_value.interactions.create.return_value = response

        result = extractor.extract(
            "GSTIN: 09ABCDE1234F1Z5",
            DocumentType.GST_CERTIFICATE,
        )

    assert result.fields.trade_name is None
    assert result.fields.registration_date is None


def test_empty_document_text_is_rejected():
    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        extractor.extract(
            "",
            DocumentType.GST_CERTIFICATE,
        )


def test_whitespace_document_text_is_rejected():
    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        extractor.extract(
            "   ",
            DocumentType.GST_CERTIFICATE,
        )


def test_unknown_document_type_is_rejected():
    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    with pytest.raises(ValueError, match="not supported"):
        extractor.extract(
            "Some document text",
            DocumentType.UNKNOWN,
        )


def test_missing_api_key_is_rejected():
    with patch(
        "app.services.document_intelligence.field_extractor.settings"
    ) as mock_settings:
        mock_settings.GEMINI_API_KEY = None
        mock_settings.GEMINI_MODEL = "test-model"

        extractor = DocumentFieldExtractor()

        with pytest.raises(
            RuntimeError,
            match="GEMINI_API_KEY",
        ):
            extractor.extract(
                "GSTIN: 09ABCDE1234F1Z5",
                DocumentType.GST_CERTIFICATE,
            )


def test_invalid_json_is_rejected():
    response = make_response(
        "this is not valid json"
    )

    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    with patch(
        "app.services.document_intelligence.field_extractor.genai.Client"
    ) as client_class:
        client_class.return_value.interactions.create.return_value = response

        with pytest.raises(
            ValueError,
            match="invalid JSON",
        ):
            extractor.extract(
                "GSTIN: 09ABCDE1234F1Z5",
                DocumentType.GST_CERTIFICATE,
            )


def test_gemini_client_receives_correct_model():
    response = make_response(
        """
        {
            "fields": {
                "gstin": "09ABCDE1234F1Z5",
                "legal_name": null,
                "trade_name": null,
                "registration_date": null,
                "status": null
            },
            "confidence": 0.80
        }
        """
    )

    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="custom-model",
    )

    with patch(
        "app.services.document_intelligence.field_extractor.genai.Client"
    ) as client_class:
        client_class.return_value.interactions.create.return_value = response

        extractor.extract(
            "GSTIN: 09ABCDE1234F1Z5",
            DocumentType.GST_CERTIFICATE,
        )

    client_class.assert_called_once_with(
        api_key="test-key"
    )

    create_call = (
        client_class.return_value
        .interactions
        .create
    )

    assert (
        create_call.call_args.kwargs["model"]
        == "custom-model"
    )


def test_gemini_receives_document_text():
    response = make_response(
        """
        {
            "fields": {
                "gstin": "09ABCDE1234F1Z5",
                "legal_name": null,
                "trade_name": null,
                "registration_date": null,
                "status": null
            },
            "confidence": 0.80
        }
        """
    )

    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    document_text = "GSTIN: 09ABCDE1234F1Z5"

    with patch(
        "app.services.document_intelligence.field_extractor.genai.Client"
    ) as client_class:
        client_class.return_value.interactions.create.return_value = response

        extractor.extract(
            document_text,
            DocumentType.GST_CERTIFICATE,
        )

    call_args = (
        client_class.return_value
        .interactions
        .create.call_args
    )

    input_text = call_args.kwargs["input"]

    assert document_text in input_text


def test_gemini_receives_structured_response_schema():
    response = make_response(
        """
        {
            "fields": {
                "gstin": "09ABCDE1234F1Z5",
                "legal_name": null,
                "trade_name": null,
                "registration_date": null,
                "status": null
            },
            "confidence": 0.80
        }
        """
    )

    extractor = DocumentFieldExtractor(
        api_key="test-key",
        model="test-model",
    )

    with patch(
        "app.services.document_intelligence.field_extractor.genai.Client"
    ) as client_class:
        client_class.return_value.interactions.create.return_value = response

        extractor.extract(
            "GSTIN: 09ABCDE1234F1Z5",
            DocumentType.GST_CERTIFICATE,
        )

    response_format = (
        client_class.return_value
        .interactions
        .create.call_args
        .kwargs["response_format"]
    )

    assert response_format["type"] == "text"
    assert response_format["mime_type"] == "application/json"
    assert "fields" in response_format["schema"]["properties"]
    assert (
        "confidence"
        in response_format["schema"]["properties"]
    )