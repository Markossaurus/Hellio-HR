import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.main import app
from app.models import (
    Base,
    Candidate,
    CandidateProfile,
    Document,
    DocumentExtraction,
    DocumentSummary,
    DocumentText,
)
from app.services.llm import LLMResponse


# Manual verification (Docker + curl):
# 1) docker compose up -d db && docker compose run --rm migrate
# 2) docker compose up
# 3) curl -H "Authorization: Bearer <token>" -F "file=@backend/test/fixtures/sample.pdf" http://localhost:8000/documents/upload
# 4) curl -H "Authorization: Bearer <token>" -X POST http://localhost:8000/documents/<document_id>/ingest -H "Content-Type: application/json" -d '{"force_reingest": false}'
# 5) curl -H "Authorization: Bearer <token>" http://localhost:8000/documents/<document_id>/text


def _sample_pdf_bytes() -> bytes:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    return fixture_path.read_bytes()


def _extraction_payload() -> dict:
    return {
        "name": "Jamie Example",
        "email": "jamie@example.com",
        "phone": "+1-555-0100",
        "location": "Portland, OR",
        "title": "Software Engineer",
        "summary": "Experienced engineer focused on backend systems.",
        "skills": [
            {
                "id": "b3c0b23e-2c47-4d48-a4dd-7e6f9374cb66",
                "name": "Python",
                "level": "advanced",
            }
        ],
        "experience": [
            {
                "id": "2fd419a9-1327-4ca6-9b3a-624a8208c78f",
                "company": "Acme Corp",
                "title": "Backend Engineer",
                "start_date": "2021-01",
                "end_date": "present",
                "description": "Built ingestion services.",
            }
        ],
        "education": [
            {
                "id": "a96f3f7e-23d2-4a98-bf71-6bcf7c11f0d3",
                "institution": "State University",
                "degree": "BSc",
                "field": "Computer Science",
                "start_date": "2016-09",
                "end_date": "2020-06",
            }
        ],
    }


@pytest.fixture(autouse=True)
def setup_ingestion_tables(test_db: Session):
    engine = test_db.get_bind()
    tables = [
        Candidate.__table__,
        CandidateProfile.__table__,
        Document.__table__,
        DocumentText.__table__,
        DocumentExtraction.__table__,
        DocumentSummary.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)

    for table in [
        "document_summaries",
        "document_extractions",
        "document_texts",
        "documents",
        "candidate_profiles",
        "candidates",
    ]:
        test_db.execute(text(f"DELETE FROM {table}"))
    test_db.commit()


def test_ingestion_end_to_end(client, test_db: Session, test_user, tmp_path):
    extraction_payload = _extraction_payload()
    extraction_json = json.dumps(extraction_payload)
    summary_text = "Summary: backend-focused engineer with ingestion experience."

    app.dependency_overrides[get_current_user] = lambda: test_user
    try:
        with patch("app.routes.documents.settings") as route_settings, \
            patch("app.services.pipeline.settings") as pipeline_settings, \
            patch("app.services.pipeline.get_provider") as mock_get_provider:
            route_settings.cv_storage_path = str(tmp_path)
            pipeline_settings.cv_storage_path = str(tmp_path)
            pipeline_settings.llm_provider = "mock"
            pipeline_settings.llm_model = "mock-model"

            mock_provider = AsyncMock()
            mock_provider.generate.side_effect = [
                LLMResponse(
                    content=extraction_json,
                    provider="mock",
                    model="mock-model",
                    prompt_version="cv_extraction_v1",
                    token_estimate_in=120,
                    token_estimate_out=45,
                    elapsed_ms=12,
                    cost_estimate_usd=0.0,
                ),
                LLMResponse(
                    content=summary_text,
                    provider="mock",
                    model="mock-model",
                    prompt_version="cv_summary_v1",
                    token_estimate_in=80,
                    token_estimate_out=30,
                    elapsed_ms=8,
                    cost_estimate_usd=0.0,
                ),
            ]
            mock_get_provider.return_value = mock_provider

            upload_response = client.post(
                "/documents/upload",
                files={"file": ("sample.pdf", _sample_pdf_bytes(), "application/pdf")},
            )
            assert upload_response.status_code == 200
            document_id = upload_response.json()["id"]

            candidate = Candidate(
                id=uuid.uuid4(),
                name="Jamie Example",
                status="new",
            )
            test_db.add(candidate)
            test_db.commit()

            document = test_db.get(Document, uuid.UUID(document_id))
            document.candidate_id = candidate.id
            test_db.commit()

            ingest_response = client.post(
                f"/documents/{document_id}/ingest",
                json={"force_reingest": False},
            )
            assert ingest_response.status_code == 200
            assert ingest_response.json()["status"] == "success"

            text_response = client.get(f"/documents/{document_id}/text")
            assert text_response.status_code == 200
            assert text_response.json()["extractedText"].strip()

            extraction_response = client.get(f"/documents/{document_id}/extractions")
            assert extraction_response.status_code == 200
            extraction_items = extraction_response.json()
            assert len(extraction_items) == 1
            assert extraction_items[0]["status"] == "success"
            assert extraction_items[0]["extractedJsonValidated"] == extraction_payload

            summary_response = client.get(f"/documents/{document_id}/summaries")
            assert summary_response.status_code == 200
            summary_items = summary_response.json()
            assert len(summary_items) == 1
            assert summary_items[0]["summaryText"] == summary_text

            texts = test_db.execute(
                select(DocumentText).where(
                    DocumentText.document_id == uuid.UUID(document_id)
                )
            ).scalars().all()
            extractions = test_db.execute(
                select(DocumentExtraction).where(
                    DocumentExtraction.document_id == uuid.UUID(document_id)
                )
            ).scalars().all()
            summaries = test_db.execute(
                select(DocumentSummary).where(
                    DocumentSummary.document_id == uuid.UUID(document_id)
                )
            ).scalars().all()
            profiles = test_db.execute(
                select(CandidateProfile).where(
                    CandidateProfile.candidate_id == candidate.id
                )
            ).scalars().all()

            assert len(texts) == 1
            assert len(extractions) == 1
            assert len(summaries) == 1
            assert len(profiles) == 1
            assert profiles[0].profile_json == extraction_payload
    finally:
        del app.dependency_overrides[get_current_user]
