from __future__ import annotations

import importlib
import io
from types import ModuleType


class ParsingError(Exception):
    def __init__(self, message: str, *, details: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


def _load_module(module_name: str, display_name: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        raise ParsingError(
            f"{display_name} is not installed",
            details={"error": str(exc)},
        ) from exc


def _pymupdf_version(fitz_module: ModuleType) -> str:
    version = getattr(fitz_module, "__version__", None)
    if isinstance(version, str) and version:
        return version
    doc = getattr(fitz_module, "__doc__", "") or ""
    if isinstance(doc, str) and doc.startswith("PyMuPDF"):
        parts = doc.split()
        if len(parts) > 1:
            return parts[1].strip(":")
    return "unknown"


def parse_pdf(file_bytes: bytes) -> tuple[str, str]:
    try:
        fitz_module = _load_module("fitz", "PyMuPDF")
        document = fitz_module.open(stream=file_bytes, filetype="pdf")
        text_parts = [page.get_text("text") for page in document]
        document.close()
        text = "\n".join(part for part in text_parts if part)
        return text, f"pymupdf-{_pymupdf_version(fitz_module)}"
    except Exception as exc:
        raise ParsingError("Failed to parse PDF", details={"error": str(exc)}) from exc


def parse_docx(file_bytes: bytes) -> tuple[str, str]:
    try:
        docx_module = _load_module("docx", "python-docx")
        document = docx_module.Document(io.BytesIO(file_bytes))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text)
        version = getattr(docx_module, "__version__", None)
        version_text = version if isinstance(version, str) and version else "unknown"
        return text, f"python-docx-{version_text}"
    except Exception as exc:
        raise ParsingError("Failed to parse DOCX", details={"error": str(exc)}) from exc


def parse_document(file_bytes: bytes, content_type: str) -> tuple[str, str]:
    normalized_type = (content_type or "").lower()
    if normalized_type == "application/pdf":
        return parse_pdf(file_bytes)
    if normalized_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return parse_docx(file_bytes)
    raise ParsingError("Unsupported content type", details={"content_type": content_type})
