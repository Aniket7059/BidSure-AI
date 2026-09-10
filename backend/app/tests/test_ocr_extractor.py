from pathlib import Path
from unittest.mock import patch

import fitz
import pytest

from app.services.document_intelligence.ocr_extractor import (
    OCRExtractor,
)


def create_scanned_pdf(
    path: Path,
    page_count: int = 1,
) -> None:
    """
    Create a small image-only PDF for OCR unit tests.

    The pages contain no native PDF text.
    """
    document = fitz.open()

    for _ in range(page_count):
        page = document.new_page(width=400, height=400)

        # Create a simple white RGB image.
        width = 400
        height = 400

        samples = bytes([255]) * (width * height * 3)

        pixmap = fitz.Pixmap(
            fitz.csRGB,
            width,
            height,
            samples,
            False,
        )

        page.insert_image(
            page.rect,
            pixmap=pixmap,
        )

    document.save(path)
    document.close()

def test_extract_single_page_scanned_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "scanned.pdf"

    create_scanned_pdf(pdf_path)

    extractor = OCRExtractor()

    with patch(
        "app.services.document_intelligence.ocr_extractor.pytesseract.image_to_string",
        return_value="GSTIN: 29ABCDE1234F1Z5\nGST Certificate",
    ) as mock_ocr:
        result = extractor.extract(pdf_path)

    assert result.total_pages == 1
    assert result.total_characters > 0

    assert result.pages[0].page_number == 1
    assert "GSTIN" in result.pages[0].text

    mock_ocr.assert_called_once()


def test_extract_multiple_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "scanned_multi_page.pdf"

    create_scanned_pdf(
        pdf_path,
        page_count=3,
    )

    ocr_results = [
        "Page 1 - Udyam Registration Certificate",
        "Page 2 - Enterprise Details",
        "Page 3 - Registration Details",
    ]

    extractor = OCRExtractor()

    with patch(
        "app.services.document_intelligence.ocr_extractor.pytesseract.image_to_string",
        side_effect=ocr_results,
    ):
        result = extractor.extract(pdf_path)

    assert result.total_pages == 3

    assert result.pages[0].page_number == 1
    assert result.pages[0].text == ocr_results[0]

    assert result.pages[1].page_number == 2
    assert result.pages[1].text == ocr_results[1]

    assert result.pages[2].page_number == 3
    assert result.pages[2].text == ocr_results[2]


def test_page_order_is_preserved(tmp_path: Path) -> None:
    pdf_path = tmp_path / "ordered.pdf"

    create_scanned_pdf(
        pdf_path,
        page_count=3,
    )

    extractor = OCRExtractor()

    with patch(
        "app.services.document_intelligence.ocr_extractor.pytesseract.image_to_string",
        side_effect=[
            "FIRST PAGE",
            "SECOND PAGE",
            "THIRD PAGE",
        ],
    ):
        result = extractor.extract(pdf_path)

    assert [page.page_number for page in result.pages] == [
        1,
        2,
        3,
    ]

    assert [page.text for page in result.pages] == [
        "FIRST PAGE",
        "SECOND PAGE",
        "THIRD PAGE",
    ]


def test_total_character_count(tmp_path: Path) -> None:
    pdf_path = tmp_path / "characters.pdf"

    create_scanned_pdf(
        pdf_path,
        page_count=2,
    )

    extractor = OCRExtractor()

    with patch(
        "app.services.document_intelligence.ocr_extractor.pytesseract.image_to_string",
        side_effect=[
            "ABC",
            "DEFG",
        ],
    ):
        result = extractor.extract(pdf_path)

    assert result.total_characters == len("ABC") + len("DEFG")


def test_empty_ocr_result_is_allowed(tmp_path: Path) -> None:
    pdf_path = tmp_path / "empty_ocr.pdf"

    create_scanned_pdf(pdf_path)

    extractor = OCRExtractor()

    with patch(
        "app.services.document_intelligence.ocr_extractor.pytesseract.image_to_string",
        return_value="",
    ):
        result = extractor.extract(pdf_path)

    assert result.total_pages == 1
    assert result.total_characters == 0
    assert result.pages[0].text == ""


def test_missing_file_raises_error(tmp_path: Path) -> None:
    pdf_path = tmp_path / "does_not_exist.pdf"

    extractor = OCRExtractor()

    with pytest.raises(FileNotFoundError):
        extractor.extract(pdf_path)


def test_directory_path_raises_error(tmp_path: Path) -> None:
    extractor = OCRExtractor()

    with pytest.raises(ValueError, match="not a file"):
        extractor.extract(tmp_path)


def test_non_pdf_file_raises_error(tmp_path: Path) -> None:
    file_path = tmp_path / "document.txt"
    file_path.write_text("This is not a PDF.")

    extractor = OCRExtractor()

    with pytest.raises(ValueError, match="Expected a PDF"):
        extractor.extract(file_path)


def test_invalid_pdf_raises_runtime_error(tmp_path: Path) -> None:
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_bytes(b"this is not a real pdf")

    extractor = OCRExtractor()

    with pytest.raises(RuntimeError, match="Failed to perform OCR"):
        extractor.extract(pdf_path)


def test_custom_dpi_is_used(tmp_path: Path) -> None:
    pdf_path = tmp_path / "dpi.pdf"

    create_scanned_pdf(pdf_path)

    extractor = OCRExtractor(dpi=200)

    with patch(
        "app.services.document_intelligence.ocr_extractor.pytesseract.image_to_string",
        return_value="TEST",
    ):
        with patch.object(
            extractor,
            "_render_page",
            wraps=extractor._render_page,
        ) as mock_render:
            extractor.extract(pdf_path)

    mock_render.assert_called_once()


def test_custom_language_is_passed_to_tesseract(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "language.pdf"

    create_scanned_pdf(pdf_path)

    extractor = OCRExtractor(language="eng")

    with patch(
        "app.services.document_intelligence.ocr_extractor.pytesseract.image_to_string",
        return_value="PAN CARD",
    ) as mock_ocr:
        extractor.extract(pdf_path)

    mock_ocr.assert_called_once()

    _, kwargs = mock_ocr.call_args

    assert kwargs["lang"] == "eng"


def test_tesseract_failure_is_wrapped(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "ocr_failure.pdf"

    create_scanned_pdf(pdf_path)

    extractor = OCRExtractor()

    with patch(
        "app.services.document_intelligence.ocr_extractor.pytesseract.image_to_string",
        side_effect=RuntimeError("Tesseract failed"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Failed to perform OCR",
        ):
            extractor.extract(pdf_path)