from pathlib import Path

import pytest

from app.services.parsing import ParsingError, parse_docx, parse_document, parse_pdf


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _read_fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def test_parse_pdf_extracts_text():
    pdf_bytes = _read_fixture("sample.pdf")

    text, version = parse_pdf(pdf_bytes)

    assert "Sample PDF Content" in text
    assert version.startswith("pymupdf-")


def test_parse_docx_extracts_text():
    docx_bytes = _read_fixture("sample.docx")

    text, version = parse_docx(docx_bytes)

    assert "Sample DOCX Content" in text
    assert version.startswith("python-docx-")


def test_parse_document_dispatches_by_content_type():
    pdf_bytes = _read_fixture("sample.pdf")
    docx_bytes = _read_fixture("sample.docx")

    pdf_text, pdf_version = parse_document(pdf_bytes, "application/pdf")
    docx_text, docx_version = parse_document(
        docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert "Sample PDF Content" in pdf_text
    assert pdf_version.startswith("pymupdf-")
    assert "Sample DOCX Content" in docx_text
    assert docx_version.startswith("python-docx-")


def test_parse_document_rejects_invalid_content_type():
    with pytest.raises(ParsingError):
        parse_document(b"not a document", "text/plain")
