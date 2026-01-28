import hashlib
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.models import (
    Base,
    Candidate,
    Document,
    DocumentExtraction,
    DocumentSummary,
    DocumentText,
    User,
)
from app.services.pipeline import IngestResult


@pytest.fixture
def mock_user():
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="dummy",
    )


@pytest.fixture(autouse=True)
def setup_document_tables(test_db: Session):
    engine = test_db.get_bind()
    tables = [
        Document.__table__,
        DocumentText.__table__,
        DocumentExtraction.__table__,
        DocumentSummary.__table__,
    ]
    try:
        Base.metadata.create_all(engine, tables=[Candidate.__table__] + tables)
    except Exception:
        Base.metadata.create_all(engine, tables=tables)

    for table in [
        "document_summaries",
        "document_extractions",
        "document_texts",
        "documents",
    ]:
        test_db.execute(text(f"DELETE FROM {table}"))
    test_db.commit()


@pytest.fixture
def authenticated_client(client, mock_user):
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client
    del app.dependency_overrides[get_current_user]


def test_upload_pdf_success(authenticated_client: TestClient, tmp_path):
    with patch("app.routes.documents.settings") as mock_settings:
        mock_settings.cv_storage_path = str(tmp_path)

        file_content = b"%PDF-1.4 test content"
        files = {"file": ("test.pdf", file_content, "application/pdf")}
        response = authenticated_client.post(
            "/documents/upload",
            files=files,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "id" in data
        assert data["contentHash"] == hashlib.sha256(file_content).hexdigest()


def test_upload_docx_success(authenticated_client: TestClient, tmp_path):
    with patch("app.routes.documents.settings") as mock_settings:
        mock_settings.cv_storage_path = str(tmp_path)

        file_content = b"docx content"
        files = {
            "file": (
                "test.docx",
                file_content,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        response = authenticated_client.post(
            "/documents/upload",
            files=files,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


def test_upload_invalid_type_returns_400(authenticated_client: TestClient):
    files = {"file": ("test.txt", b"text content", "text/plain")}
    response = authenticated_client.post(
        "/documents/upload",
        files=files,
    )
    assert response.status_code == 400


def test_upload_large_file_returns_413(authenticated_client: TestClient):
    large_content = b"a" * (10 * 1024 * 1024 + 1)
    files = {"file": ("large.pdf", large_content, "application/pdf")}
    response = authenticated_client.post(
        "/documents/upload",
        files=files,
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_ingest_document_success(
    authenticated_client: TestClient, test_db: Session
):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        type="cv",
        content_type="application/pdf",
        display_name="test.pdf",
        content_hash="hash123",
    )
    test_db.add(doc)
    test_db.commit()

    with patch("app.routes.documents.IngestionPipeline") as mock_pipeline_class:
        mock_pipeline = mock_pipeline_class.return_value
        mock_pipeline.ingest = AsyncMock(
            return_value=IngestResult(
                document_id=doc_id,
                status="success",
                extraction_id=uuid.uuid4(),
                summary_id=uuid.uuid4(),
                errors=[],
            )
        )

        response = authenticated_client.post(
            f"/documents/{doc_id}/ingest",
            json={"force_reingest": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["documentId"] == str(doc_id)


def test_get_document_metadata(authenticated_client: TestClient, test_db: Session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        type="cv",
        content_type="application/pdf",
        display_name="test.pdf",
        content_hash="hash123",
    )
    test_db.add(doc)
    test_db.commit()

    response = authenticated_client.get(f"/documents/{doc_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(doc_id)
    assert data["displayName"] == "test.pdf"


def test_get_document_text(authenticated_client: TestClient, test_db: Session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        type="cv",
        content_type="application/pdf",
        display_name="test.pdf",
        content_hash="hash123",
    )
    test_db.add(doc)
    test_db.flush()

    doc_text = DocumentText(
        id=uuid.uuid4(),
        document_id=doc_id,
        extracted_text="Some extracted text",
        parser_version="v1",
    )
    test_db.add(doc_text)
    test_db.commit()

    response = authenticated_client.get(f"/documents/{doc_id}/text")

    assert response.status_code == 200
    data = response.json()
    assert data["extractedText"] == "Some extracted text"


def test_get_document_text_not_found(authenticated_client: TestClient):
    doc_id = uuid.uuid4()
    response = authenticated_client.get(f"/documents/{doc_id}/text")
    assert response.status_code == 404


def test_get_document_extractions(authenticated_client: TestClient, test_db: Session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        type="cv",
        content_type="application/pdf",
        display_name="test.pdf",
        content_hash="hash123",
    )
    test_db.add(doc)
    test_db.flush()

    extraction = DocumentExtraction(
        id=uuid.uuid4(),
        document_id=doc_id,
        heuristic_json={},
        llm_raw_output="{}",
        extraction_schema_version="v1",
        status="success",
        provider="test",
        model="test",
        prompt_version="v1",
    )
    test_db.add(extraction)
    test_db.commit()

    response = authenticated_client.get(f"/documents/{doc_id}/extractions")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["documentId"] == str(doc_id)


def test_get_document_summaries(authenticated_client: TestClient, test_db: Session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        type="cv",
        content_type="application/pdf",
        display_name="test.pdf",
        content_hash="hash123",
    )
    test_db.add(doc)
    test_db.flush()

    summary = DocumentSummary(
        id=uuid.uuid4(),
        document_id=doc_id,
        summary_text="A summary",
        prompt_version="v1",
        provider="test",
        model="test",
    )
    test_db.add(summary)
    test_db.commit()

    response = authenticated_client.get(f"/documents/{doc_id}/summaries")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["summaryText"] == "A summary"


def test_unauthenticated_returns_401(client: TestClient):
    response = client.get(f"/documents/{uuid.uuid4()}")
    assert response.status_code == 401
