from pathlib import Path

import pytest

from app.services.document_intelligence.orchestrator import (
    DocumentIntelligenceOrchestrator,
)
from app.services.document_intelligence.schemas import (
    DocumentClassificationResponse,
    DocumentFieldExtractionResponse,
    DocumentIntelligenceResult,
    DocumentType,
    GSTDocumentFields,
    PDFTextExtractionResult,
    ExtractedPage,
    TextExtractionMethod,
)


class FakePDFExtractor:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def extract(self, path):
        self.calls.append(path)
        return self.result


class FakeOCRExtractor:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def extract(self, path):
        self.calls.append(path)
        return self.result


class FakeClassifier:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def classify(self, text):
        self.calls.append(text)
        return self.result


class FakeFieldExtractor:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def extract(self, text, document_type):
        self.calls.append((text, document_type))
        return self.result


def make_native_result(text: str) -> PDFTextExtractionResult:
    return PDFTextExtractionResult(
        pages=[
            ExtractedPage(
                page_number=1,
                text=text,
            )
        ],
        total_pages=1,
        total_characters=len(text),
    )


def make_ocr_result(text: str) -> PDFTextExtractionResult:
    return PDFTextExtractionResult(
        pages=[
            ExtractedPage(
                page_number=1,
                text=text,
            )
        ],
        total_pages=1,
        total_characters=len(text),
    )


def make_classification() -> DocumentClassificationResponse:
    return DocumentClassificationResponse(
        document_type=DocumentType.GST_CERTIFICATE,
        confidence=0.97,
    )


def make_field_extraction() -> DocumentFieldExtractionResponse:
    return DocumentFieldExtractionResponse(
        document_type=DocumentType.GST_CERTIFICATE,
        fields=GSTDocumentFields(
            gstin="09ABCDE1234F1Z5",
            legal_name="ABC PRIVATE LIMITED",
            status="Active",
        ),
        confidence=0.94,
    )


def test_native_pdf_is_used_when_text_is_available(tmp_path):
    pdf_path = tmp_path / "gst.pdf"
    pdf_path.write_bytes(b"fake pdf")

    pdf_extractor = FakePDFExtractor(
        make_native_result(
            "GSTIN: 09ABCDE1234F1Z5"
        )
    )

    ocr_extractor = FakeOCRExtractor(
        make_ocr_result(
            "OCR GSTIN: 09ABCDE1234F1Z5"
        )
    )

    classifier = FakeClassifier(
        make_classification()
    )

    field_extractor = FakeFieldExtractor(
        make_field_extraction()
    )

    orchestrator = DocumentIntelligenceOrchestrator(
        pdf_extractor=pdf_extractor,
        ocr_extractor=ocr_extractor,
        classifier=classifier,
        field_extractor=field_extractor,
    )

    result = orchestrator.process(pdf_path)

    assert isinstance(result, DocumentIntelligenceResult)

    assert result.extraction_method == TextExtractionMethod.NATIVE_PDF
    assert result.extracted_text == "GSTIN: 09ABCDE1234F1Z5"

    assert len(pdf_extractor.calls) == 1
    assert len(ocr_extractor.calls) == 0


def test_ocr_is_used_when_native_text_is_empty(tmp_path):
    pdf_path = tmp_path / "scanned.pdf"
    pdf_path.write_bytes(b"fake pdf")

    pdf_extractor = FakePDFExtractor(
        make_native_result("")
    )

    ocr_extractor = FakeOCRExtractor(
        make_ocr_result(
            "GSTIN: 09ABCDE1234F1Z5"
        )
    )

    classifier = FakeClassifier(
        make_classification()
    )

    field_extractor = FakeFieldExtractor(
        make_field_extraction()
    )

    orchestrator = DocumentIntelligenceOrchestrator(
        pdf_extractor=pdf_extractor,
        ocr_extractor=ocr_extractor,
        classifier=classifier,
        field_extractor=field_extractor,
    )

    result = orchestrator.process(pdf_path)

    assert result.extraction_method == TextExtractionMethod.OCR
    assert result.extracted_text == "GSTIN: 09ABCDE1234F1Z5"

    assert len(pdf_extractor.calls) == 1
    assert len(ocr_extractor.calls) == 1


def test_whitespace_only_native_text_triggers_ocr(tmp_path):
    pdf_path = tmp_path / "scanned.pdf"
    pdf_path.write_bytes(b"fake pdf")

    pdf_extractor = FakePDFExtractor(
        make_native_result("   \n\n   ")
    )

    ocr_extractor = FakeOCRExtractor(
        make_ocr_result(
            "GSTIN: 09ABCDE1234F1Z5"
        )
    )

    orchestrator = DocumentIntelligenceOrchestrator(
        pdf_extractor=pdf_extractor,
        ocr_extractor=ocr_extractor,
        classifier=FakeClassifier(
            make_classification()
        ),
        field_extractor=FakeFieldExtractor(
            make_field_extraction()
        ),
    )

    result = orchestrator.process(pdf_path)

    assert result.extraction_method == TextExtractionMethod.OCR
    assert len(ocr_extractor.calls) == 1


def test_classifier_receives_combined_text(tmp_path):
    pdf_path = tmp_path / "gst.pdf"
    pdf_path.write_bytes(b"fake pdf")

    pdf_extractor = FakePDFExtractor(
        PDFTextExtractionResult(
            pages=[
                ExtractedPage(
                    page_number=1,
                    text="GSTIN: 09ABCDE1234F1Z5",
                ),
                ExtractedPage(
                    page_number=2,
                    text="Legal Name: ABC PRIVATE LIMITED",
                ),
            ],
            total_pages=2,
            total_characters=65,
        )
    )

    classifier = FakeClassifier(
        make_classification()
    )

    field_extractor = FakeFieldExtractor(
        make_field_extraction()
    )

    orchestrator = DocumentIntelligenceOrchestrator(
        pdf_extractor=pdf_extractor,
        ocr_extractor=FakeOCRExtractor(
            make_ocr_result("unused")
        ),
        classifier=classifier,
        field_extractor=field_extractor,
    )

    result = orchestrator.process(pdf_path)

    assert classifier.calls == [
        "GSTIN: 09ABCDE1234F1Z5\n\n"
        "Legal Name: ABC PRIVATE LIMITED"
    ]

    assert result.total_pages == 2


def test_field_extractor_receives_classification_result(
    tmp_path,
):
    pdf_path = tmp_path / "gst.pdf"
    pdf_path.write_bytes(b"fake pdf")

    classifier = FakeClassifier(
        make_classification()
    )

    field_extractor = FakeFieldExtractor(
        make_field_extraction()
    )

    orchestrator = DocumentIntelligenceOrchestrator(
        pdf_extractor=FakePDFExtractor(
            make_native_result(
                "GSTIN: 09ABCDE1234F1Z5"
            )
        ),
        ocr_extractor=FakeOCRExtractor(
            make_ocr_result("unused")
        ),
        classifier=classifier,
        field_extractor=field_extractor,
    )

    orchestrator.process(pdf_path)

    assert len(field_extractor.calls) == 1

    text, document_type = field_extractor.calls[0]

    assert text == "GSTIN: 09ABCDE1234F1Z5"
    assert document_type == DocumentType.GST_CERTIFICATE


def test_complete_result_contains_classification_and_fields(
    tmp_path,
):
    pdf_path = tmp_path / "gst.pdf"
    pdf_path.write_bytes(b"fake pdf")

    orchestrator = DocumentIntelligenceOrchestrator(
        pdf_extractor=FakePDFExtractor(
            make_native_result(
                "GSTIN: 09ABCDE1234F1Z5"
            )
        ),
        ocr_extractor=FakeOCRExtractor(
            make_ocr_result("unused")
        ),
        classifier=FakeClassifier(
            make_classification()
        ),
        field_extractor=FakeFieldExtractor(
            make_field_extraction()
        ),
    )

    result = orchestrator.process(pdf_path)

    assert result.document_type == DocumentType.GST_CERTIFICATE
    assert result.classification_confidence == 0.97

    assert result.fields.gstin == "09ABCDE1234F1Z5"
    assert result.fields.legal_name == "ABC PRIVATE LIMITED"
    assert result.fields.status == "Active"

    assert result.extraction_confidence == 0.94


def test_native_extraction_is_preferred_over_ocr(tmp_path):
    pdf_path = tmp_path / "document.pdf"
    pdf_path.write_bytes(b"fake pdf")

    pdf_extractor = FakePDFExtractor(
        make_native_result("Native text")
    )

    ocr_extractor = FakeOCRExtractor(
        make_ocr_result("OCR text")
    )

    orchestrator = DocumentIntelligenceOrchestrator(
        pdf_extractor=pdf_extractor,
        ocr_extractor=ocr_extractor,
        classifier=FakeClassifier(
            make_classification()
        ),
        field_extractor=FakeFieldExtractor(
            make_field_extraction()
        ),
    )

    result = orchestrator.process(pdf_path)

    assert result.extracted_text == "Native text"
    assert result.extraction_method == TextExtractionMethod.NATIVE_PDF
    assert not ocr_extractor.calls


def test_page_order_is_preserved(tmp_path):
    pdf_path = tmp_path / "document.pdf"
    pdf_path.write_bytes(b"fake pdf")

    native_result = PDFTextExtractionResult(
        pages=[
            ExtractedPage(
                page_number=1,
                text="PAGE ONE",
            ),
            ExtractedPage(
                page_number=2,
                text="PAGE TWO",
            ),
            ExtractedPage(
                page_number=3,
                text="PAGE THREE",
            ),
        ],
        total_pages=3,
        total_characters=26,
    )

    classifier = FakeClassifier(
        make_classification()
    )

    field_extractor = FakeFieldExtractor(
        make_field_extraction()
    )

    orchestrator = DocumentIntelligenceOrchestrator(
        pdf_extractor=FakePDFExtractor(native_result),
        ocr_extractor=FakeOCRExtractor(
            make_ocr_result("unused")
        ),
        classifier=classifier,
        field_extractor=field_extractor,
    )

    result = orchestrator.process(pdf_path)

    assert result.extracted_text == (
        "PAGE ONE\n\n"
        "PAGE TWO\n\n"
        "PAGE THREE"
    )