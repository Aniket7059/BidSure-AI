from unittest.mock import Mock

import pytest

from app.services.document_intelligence.classifier import (
    DocumentClassifier,
)
from app.services.document_intelligence.schemas import (
    DocumentClassificationResponse,
    DocumentType,
)


def create_classifier():
    return DocumentClassifier(
        api_key="test-api-key",
        model="gemini-3.6-flash",
    )


def test_empty_document_text_returns_error():

    classifier = create_classifier()

    with pytest.raises(
        ValueError,
        match="Document text cannot be empty",
    ):
        classifier.classify("")


def test_missing_api_key_returns_error():

    classifier = DocumentClassifier(
        api_key="",
        model="gemini-3.6-flash",
    )

    classifier.client = None

    with pytest.raises(
        RuntimeError,
        match="GEMINI_API_KEY is not configured",
    ):
        classifier.classify(
            "Goods and Services Tax Registration Certificate"
        )


def test_gst_document_is_classified():

    classifier = create_classifier()

    expected = DocumentClassificationResponse(
        document_type=DocumentType.GST_CERTIFICATE,
        confidence=0.96,
    )

    mock_response = Mock()
    mock_response.output_text = expected.model_dump_json()

    classifier.client = Mock()
    classifier.client.interactions.create.return_value = (
        mock_response
    )

    result = classifier.classify(
        """
        Goods and Services Tax Registration Certificate

        This certificate confirms registration under GST.
        """
    )

    assert isinstance(
        result,
        DocumentClassificationResponse,
    )

    assert (
        result.document_type
        == DocumentType.GST_CERTIFICATE
    )

    assert result.confidence == 0.96


def test_udyam_document_is_classified():

    classifier = create_classifier()

    expected = DocumentClassificationResponse(
        document_type=DocumentType.UDYAM_CERTIFICATE,
        confidence=0.94,
    )

    mock_response = Mock()
    mock_response.output_text = expected.model_dump_json()

    classifier.client = Mock()
    classifier.client.interactions.create.return_value = (
        mock_response
    )

    result = classifier.classify(
        """
        UDYAM REGISTRATION CERTIFICATE

        Ministry of Micro, Small & Medium Enterprises
        Udyam Registration
        """
    )

    assert isinstance(
        result,
        DocumentClassificationResponse,
    )

    assert (
        result.document_type
        == DocumentType.UDYAM_CERTIFICATE
    )

    assert result.confidence == 0.94


def test_pan_document_is_classified():

    classifier = create_classifier()

    expected = DocumentClassificationResponse(
        document_type=DocumentType.PAN,
        confidence=0.97,
    )

    mock_response = Mock()
    mock_response.output_text = expected.model_dump_json()

    classifier.client = Mock()
    classifier.client.interactions.create.return_value = (
        mock_response
    )

    result = classifier.classify(
        """
        INCOME TAX DEPARTMENT

        PERMANENT ACCOUNT NUMBER
        """
    )

    assert isinstance(
        result,
        DocumentClassificationResponse,
    )

    assert (
        result.document_type
        == DocumentType.PAN
    )

    assert result.confidence == 0.97


def test_income_tax_document_is_classified():

    classifier = create_classifier()

    expected = DocumentClassificationResponse(
        document_type=DocumentType.INCOME_TAX,
        confidence=0.95,
    )

    mock_response = Mock()
    mock_response.output_text = expected.model_dump_json()

    classifier.client = Mock()
    classifier.client.interactions.create.return_value = (
        mock_response
    )

    result = classifier.classify(
        """
        INCOME TAX RETURN

        ITR acknowledgement
        Assessment Year
        """
    )

    assert isinstance(
        result,
        DocumentClassificationResponse,
    )

    assert (
        result.document_type
        == DocumentType.INCOME_TAX
    )

    assert result.confidence == 0.95


def test_unknown_document_is_classified():

    classifier = create_classifier()

    expected = DocumentClassificationResponse(
        document_type=DocumentType.UNKNOWN,
        confidence=0.91,
    )

    mock_response = Mock()
    mock_response.output_text = expected.model_dump_json()

    classifier.client = Mock()
    classifier.client.interactions.create.return_value = (
        mock_response
    )

    result = classifier.classify(
        """
        Random company correspondence
        regarding a business meeting.
        """
    )

    assert isinstance(
        result,
        DocumentClassificationResponse,
    )

    assert (
        result.document_type
        == DocumentType.UNKNOWN
    )

    assert result.confidence == 0.91


def test_gemini_receives_document_content():

    classifier = create_classifier()

    expected = DocumentClassificationResponse(
        document_type=DocumentType.GST_CERTIFICATE,
        confidence=0.96,
    )

    mock_response = Mock()
    mock_response.output_text = expected.model_dump_json()

    classifier.client = Mock()
    classifier.client.interactions.create.return_value = (
        mock_response
    )

    document_text = """
    Goods and Services Tax Registration Certificate
    GST registration certificate issued by the authority.
    """

    classifier.classify(document_text)

    call = (
        classifier.client
        .interactions
        .create
    )

    call.assert_called_once()

    kwargs = call.call_args.kwargs

    assert (
        kwargs["model"]
        == "gemini-3.6-flash"
    )

    assert (
        "Goods and Services Tax Registration Certificate"
        in kwargs["input"]
    )

    assert (
        "GST registration certificate issued by the authority."
        in kwargs["input"]
    )


def test_invalid_gemini_json_returns_validation_error():

    classifier = create_classifier()

    mock_response = Mock()
    mock_response.output_text = (
        '{"document_type": "GST_CERTIFICATE"}'
    )

    classifier.client = Mock()
    classifier.client.interactions.create.return_value = (
        mock_response
    )

    with pytest.raises(Exception):
        classifier.classify(
            "GST Registration Certificate"
        )