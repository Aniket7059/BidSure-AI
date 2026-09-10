import fitz
import pytest

from app.services.document_intelligence.pdf_extractor import (
    PDFTextExtractor,
)


def create_pdf(
    path,
    pages: list[str],
):
    document = fitz.open()

    for text in pages:
        page = document.new_page()
        page.insert_text(
            (72, 72),
            text,
        )

    document.save(path)
    document.close()


def test_extract_single_page_pdf(tmp_path):

    pdf_path = tmp_path / "gst.pdf"

    create_pdf(
        pdf_path,
        [
            "Goods and Services Tax Registration Certificate"
        ],
    )

    extractor = PDFTextExtractor()

    result = extractor.extract(pdf_path)

    assert result.total_pages == 1

    assert result.total_characters > 0

    assert len(result.pages) == 1

    assert (
        result.pages[0].page_number
        == 1
    )

    assert (
        "Goods and Services Tax"
        in result.pages[0].text
    )


def test_extract_multiple_pages(tmp_path):

    pdf_path = tmp_path / "document.pdf"

    create_pdf(
        pdf_path,
        [
            "Page one - GST Registration Certificate",
            "Page two - Registration details",
            "Page three - Additional information",
        ],
    )

    extractor = PDFTextExtractor()

    result = extractor.extract(pdf_path)

    assert result.total_pages == 3

    assert len(result.pages) == 3

    assert result.pages[0].page_number == 1
    assert result.pages[1].page_number == 2
    assert result.pages[2].page_number == 3

    assert "Page one" in result.pages[0].text
    assert "Page two" in result.pages[1].text
    assert "Page three" in result.pages[2].text


def test_page_text_is_preserved(tmp_path):

    pdf_path = tmp_path / "udyam.pdf"

    expected_text = (
        "UDYAM REGISTRATION CERTIFICATE"
    )

    create_pdf(
        pdf_path,
        [expected_text],
    )

    extractor = PDFTextExtractor()

    result = extractor.extract(pdf_path)

    assert (
        expected_text
        in result.pages[0].text
    )


def test_missing_file_returns_error(tmp_path):

    pdf_path = (
        tmp_path / "does-not-exist.pdf"
    )

    extractor = PDFTextExtractor()

    with pytest.raises(
        FileNotFoundError,
        match="PDF file not found",
    ):
        extractor.extract(pdf_path)


def test_directory_path_returns_error(tmp_path):

    extractor = PDFTextExtractor()

    with pytest.raises(
        ValueError,
        match="PDF path is not a file",
    ):
        extractor.extract(tmp_path)


def test_non_pdf_file_returns_error(tmp_path):

    file_path = tmp_path / "document.txt"

    file_path.write_text(
        "This is not a PDF."
    )

    extractor = PDFTextExtractor()

    with pytest.raises(
        ValueError,
        match="File must have a .pdf extension",
    ):
        extractor.extract(file_path)


def test_invalid_pdf_returns_error(tmp_path):

    pdf_path = tmp_path / "invalid.pdf"

    pdf_path.write_bytes(
        b"This is not a real PDF."
    )

    extractor = PDFTextExtractor()

    with pytest.raises(
        ValueError,
        match="Unable to open PDF",
    ):
        extractor.extract(pdf_path)


def test_empty_pdf_returns_zero_characters(tmp_path):

    pdf_path = tmp_path / "empty.pdf"

    document = fitz.open()

    document.new_page()

    document.save(pdf_path)

    document.close()

    extractor = PDFTextExtractor()

    result = extractor.extract(pdf_path)

    assert result.total_pages == 1

    assert result.total_characters == 0

    assert result.pages[0].text == ""