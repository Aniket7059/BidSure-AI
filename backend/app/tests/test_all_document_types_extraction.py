from unittest.mock import MagicMock, patch
import pytest

from app.services.document_intelligence.schemas import (
    DOCUMENT_TYPE_FIELDS_MAP,
    BidderDeclarationFields,
    BlacklistingDebarmentFields,
    DigiLockerDocumentFields,
    DocumentClassificationResponse,
    DocumentFieldExtractionResponse,
    DocumentIntelligenceResult,
    DocumentType,
    EPFODocumentFields,
    ESICDocumentFields,
    GSTDocumentFields,
    GSTReturnDocumentFields,
    GeneralCertificateFields,
    IncomeTaxDocumentFields,
    MakeInIndiaFields,
    NSICDocumentFields,
    OEMAuthorizationFields,
    PANDocumentFields,
    StartupIndiaDocumentFields,
    UdyamDocumentFields,
    UnknownDocumentFields,
)
from app.services.document_intelligence.classifier import DocumentClassifier
from app.services.document_intelligence.field_extractor import (
    DocumentFieldExtractor,
    normalize_gstin,
    normalize_pan,
    normalize_udyam,
)


def make_mock_response(payload: str):
    mock = MagicMock()
    mock.output_text = payload
    return mock


def test_document_types_count_and_mapping():
    """Verify all structured PS document types are mapped in DOCUMENT_TYPE_FIELDS_MAP."""
    assert len(DocumentType) >= 16
    for doc_type, schema_class in DOCUMENT_TYPE_FIELDS_MAP.items():
        assert issubclass(schema_class, (
            GSTDocumentFields,
            GSTReturnDocumentFields,
            PANDocumentFields,
            IncomeTaxDocumentFields,
            UdyamDocumentFields,
            EPFODocumentFields,
            ESICDocumentFields,
            StartupIndiaDocumentFields,
            NSICDocumentFields,
            OEMAuthorizationFields,
            MakeInIndiaFields,
            DigiLockerDocumentFields,
            BlacklistingDebarmentFields,
            BidderDeclarationFields,
            GeneralCertificateFields,
        ))


def test_identifier_normalizers():
    """Test identifier normalization functions."""
    assert normalize_gstin(" 09abcde1234f1z5 ") == "09ABCDE1234F1Z5"
    assert normalize_gstin(None) is None
    assert normalize_pan(" abcde1234f ") == "ABCDE1234F"
    assert normalize_pan(None) is None
    assert normalize_udyam(" udyam-up-01-0012345 ") == "UDYAM-UP-01-0012345"
    assert normalize_udyam(None) is None


@pytest.mark.parametrize(
    "doc_type, sample_json, expected_class",
    [
        (
            DocumentType.GST_CERTIFICATE,
            '{"fields": {"gstin": " 09ABCDE1234F1Z5 ", "legal_name": "Acme Pvt Ltd"}, "confidence": 0.95}',
            GSTDocumentFields,
        ),
        (
            DocumentType.GST_RETURN,
            '{"fields": {"gstin": "09ABCDE1234F1Z5", "return_type": "GSTR-3B", "financial_year": "2024-25"}, "confidence": 0.94}',
            GSTReturnDocumentFields,
        ),
        (
            DocumentType.PAN,
            '{"fields": {"pan_number": " abcde1234f ", "name": "ACME PVT LTD"}, "confidence": 0.96}',
            PANDocumentFields,
        ),
        (
            DocumentType.INCOME_TAX,
            '{"fields": {"pan_number": "ABCDE1234F", "assessment_year": "2024-25", "itr_form": "ITR-6"}, "confidence": 0.93}',
            IncomeTaxDocumentFields,
        ),
        (
            DocumentType.UDYAM_CERTIFICATE,
            '{"fields": {"udyam_number": " udyam-up-01-0012345 ", "enterprise_name": "Acme Industries"}, "confidence": 0.95}',
            UdyamDocumentFields,
        ),
        (
            DocumentType.EPFO,
            '{"fields": {"establishment_id_pf_code": "DSNHP0012345000", "employer_name": "Acme Corp"}, "confidence": 0.92}',
            EPFODocumentFields,
        ),
        (
            DocumentType.ESIC,
            '{"fields": {"employer_code_esic_number": "11000123450000101", "employer_name": "Acme Corp"}, "confidence": 0.91}',
            ESICDocumentFields,
        ),
        (
            DocumentType.STARTUP_INDIA,
            '{"fields": {"recognition_number": "DPIIT12345", "entity_name": "Acme Tech Solutions"}, "confidence": 0.94}',
            StartupIndiaDocumentFields,
        ),
        (
            DocumentType.NSIC,
            '{"fields": {"nsic_certificate_number": "NSIC/GP/12345", "enterprise_name": "Acme Engineering"}, "confidence": 0.92}',
            NSICDocumentFields,
        ),
        (
            DocumentType.OEM_AUTHORIZATION,
            '{"fields": {"oem_name": "Global Tech OEM", "authorized_bidder_name": "Acme Reseller"}, "confidence": 0.95}',
            OEMAuthorizationFields,
        ),
        (
            DocumentType.MAKE_IN_INDIA,
            '{"fields": {"bidder_name": "Acme Mfg", "local_content_percentage": "65%", "local_content_class": "Class-I"}, "confidence": 0.93}',
            MakeInIndiaFields,
        ),
        (
            DocumentType.DIGILOCKER_DOCUMENT,
            '{"fields": {"issuing_authority": "UIDAI", "document_type": "Aadhaar", "holder_name": "John Doe"}, "confidence": 0.90}',
            DigiLockerDocumentFields,
        ),
        (
            DocumentType.BLACKLISTING_DEBARMENT,
            '{"fields": {"entity_name": "Acme Corp", "debarment_status": "NOT_DEBARRED"}, "confidence": 0.95}',
            BlacklistingDebarmentFields,
        ),
        (
            DocumentType.BIDDER_DECLARATION,
            '{"fields": {"bidder_name": "Acme Corp", "declaration_type": "UNDERTAKING"}, "confidence": 0.91}',
            BidderDeclarationFields,
        ),
        (
            DocumentType.GENERAL_CERTIFICATE,
            '{"fields": {"certificate_title": "ISO 9001:2015 Certificate", "issued_to": "Acme Corp"}, "confidence": 0.88}',
            GeneralCertificateFields,
        ),
    ]
)
def test_field_extraction_for_all_document_types(doc_type, sample_json, expected_class):
    extractor = DocumentFieldExtractor(api_key="test-key", model="test-model")
    mock_resp = make_mock_response(sample_json)

    with patch("app.services.document_intelligence.field_extractor.genai.Client") as client_class:
        client_class.return_value.interactions.create.return_value = mock_resp
        res = extractor.extract("Sample Document Text", doc_type)

    assert isinstance(res, DocumentFieldExtractionResponse)
    assert res.document_type == doc_type
    assert isinstance(res.fields, expected_class)
    assert res.confidence > 0.0

    # Verify normalization if applicable
    if hasattr(res.fields, "gstin") and res.fields.gstin:
        assert res.fields.gstin == "09ABCDE1234F1Z5"
    if hasattr(res.fields, "pan_number") and res.fields.pan_number:
        assert res.fields.pan_number == "ABCDE1234F"
    if hasattr(res.fields, "udyam_number") and res.fields.udyam_number:
        assert res.fields.udyam_number == "UDYAM-UP-01-0012345"


def test_unknown_and_other_document_types_raise_not_supported():
    """Verify UNKNOWN and OTHER document types raise ValueError during structured extraction."""
    extractor = DocumentFieldExtractor(api_key="test-key", model="test-model")
    for unmapped in (DocumentType.UNKNOWN, DocumentType.OTHER):
        with pytest.raises(ValueError, match="not supported"):
            extractor.extract("Unrecognized document text", unmapped)



def test_missing_fields_are_null():
    """Verify missing fields remain None without hallucination."""
    extractor = DocumentFieldExtractor(api_key="test-key", model="test-model")
    sample_json = '{"fields": {"oem_name": "Tech Corp", "authorized_bidder_name": null, "validity_period": null}, "confidence": 0.90}'
    mock_resp = make_mock_response(sample_json)

    with patch("app.services.document_intelligence.field_extractor.genai.Client") as client_class:
        client_class.return_value.interactions.create.return_value = mock_resp
        res = extractor.extract("OEM Authorization Letter", DocumentType.OEM_AUTHORIZATION)

    assert res.fields.oem_name == "Tech Corp"
    assert res.fields.authorized_bidder_name is None
    assert res.fields.validity_period is None


def test_rule_based_keyword_classification_fallback():
    """Test deterministic rule-based keyword classification fallback."""
    res = DocumentClassifier.classify_by_keywords("FORM GST REG-06 Goods and Services Tax Registration Certificate")
    assert res.document_type == DocumentType.GST_CERTIFICATE

    res = DocumentClassifier.classify_by_keywords("GSTR-3B GST RETURN Filing Acknowledgement")
    assert res.document_type == DocumentType.GST_RETURN

    res = DocumentClassifier.classify_by_keywords("PERMANENT ACCOUNT NUMBER Income Tax Department")
    assert res.document_type == DocumentType.PAN

    res = DocumentClassifier.classify_by_keywords("INCOME TAX RETURN ACKNOWLEDGEMENT ITR-V")
    assert res.document_type == DocumentType.INCOME_TAX

    res = DocumentClassifier.classify_by_keywords("UDYAM REGISTRATION CERTIFICATE Ministry of MSME")
    assert res.document_type == DocumentType.UDYAM_CERTIFICATE

    res = DocumentClassifier.classify_by_keywords("EMPLOYEES' PROVIDENT FUND ORGANISATION EPFO PF CODE")
    assert res.document_type == DocumentType.EPFO

    res = DocumentClassifier.classify_by_keywords("EMPLOYEES' STATE INSURANCE CORPORATION ESIC ESI CODE")
    assert res.document_type == DocumentType.ESIC

    res = DocumentClassifier.classify_by_keywords("STARTUP INDIA Recognition Certificate DPIIT")
    assert res.document_type == DocumentType.STARTUP_INDIA

    res = DocumentClassifier.classify_by_keywords("NSIC National Small Industries Corporation")
    assert res.document_type == DocumentType.NSIC

    res = DocumentClassifier.classify_by_keywords("OEM AUTHORIZATION LETTER Manufacturer Authorization Form")
    assert res.document_type == DocumentType.OEM_AUTHORIZATION

    res = DocumentClassifier.classify_by_keywords("MAKE IN INDIA Local Content Declaration Class-I Local Supplier")
    assert res.document_type == DocumentType.MAKE_IN_INDIA

    res = DocumentClassifier.classify_by_keywords("DIGILOCKER Issued Document")
    assert res.document_type == DocumentType.DIGILOCKER_DOCUMENT

    res = DocumentClassifier.classify_by_keywords("AFFIDAVIT REGARDING NON BLACKLISTING / DEBARMENT")
    assert res.document_type == DocumentType.BLACKLISTING_DEBARMENT

    res = DocumentClassifier.classify_by_keywords("BIDDER DECLARATION UNDERTAKING FORM")
    assert res.document_type == DocumentType.BIDDER_DECLARATION

    res = DocumentClassifier.classify_by_keywords("CERTIFICATE OF INCORPORATION")
    assert res.document_type == DocumentType.GENERAL_CERTIFICATE

    res = DocumentClassifier.classify_by_keywords("Random unclassifiable text sample")
    assert res.document_type == DocumentType.UNKNOWN
