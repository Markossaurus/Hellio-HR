from datetime import datetime
import uuid
from app.schemas import (
    DocumentUploadResponse,
    DocumentMetadata,
    DocumentText,
    DocumentExtraction,
    DocumentSummary,
    IngestRequest,
    IngestResponse,
    ExtractionStatus
)

def test_document_upload_response_serialization():
    doc_id = str(uuid.uuid4())
    schema = DocumentUploadResponse(
        id=doc_id,
        content_hash="hash123",
        status="success",
        message="Uploaded successfully"
    )
    data = schema.model_dump(by_alias=True)
    assert data["id"] == doc_id
    assert data["contentHash"] == "hash123"
    assert data["status"] == "success"
    assert data["message"] == "Uploaded successfully"

def test_document_metadata_serialization():
    doc_id = str(uuid.uuid4())
    candidate_id = str(uuid.uuid4())
    now = datetime.now()
    schema = DocumentMetadata(
        id=doc_id,
        type="cv",
        content_type="application/pdf",
        display_name="resume.pdf",
        content_hash="hash123",
        candidate_id=candidate_id,
        created_at=now
    )
    data = schema.model_dump(by_alias=True)
    assert data["id"] == doc_id
    assert data["type"] == "cv"
    assert data["contentType"] == "application/pdf"
    assert data["displayName"] == "resume.pdf"
    assert data["contentHash"] == "hash123"
    assert data["candidateId"] == candidate_id
    assert isinstance(data["createdAt"], datetime)

def test_document_text_serialization():
    doc_id = str(uuid.uuid4())
    now = datetime.now()
    schema = DocumentText(
        id=doc_id,
        extracted_text="Hello World",
        parser_version="v1",
        created_at=now
    )
    data = schema.model_dump(by_alias=True)
    assert data["id"] == doc_id
    assert data["extractedText"] == "Hello World"
    assert data["parserVersion"] == "v1"

def test_document_extraction_serialization():
    doc_id = str(uuid.uuid4())
    schema = DocumentExtraction(
        id=doc_id,
        document_id=str(uuid.uuid4()),
        heuristic_json={"key": "value"},
        llm_raw_output="raw",
        extracted_json_validated={"name": "John"},
        extraction_schema_version="v1",
        status=ExtractionStatus.SUCCESS,
        error_details=None,
        provider="openai",
        model="gpt-4",
        prompt_version="v1",
        token_estimate_in=100,
        token_estimate_out=50,
        cost_estimate_usd=0.01,
        elapsed_ms=500,
        created_at=datetime.now()
    )
    data = schema.model_dump(by_alias=True)
    assert data["status"] == "success"
    assert data["heuristicJson"] == {"key": "value"}
    assert data["llmRawOutput"] == "raw"
    assert data["extractedJsonValidated"] == {"name": "John"}
    assert data["tokenEstimateIn"] == 100
    assert data["costEstimateUsd"] == 0.01

def test_document_summary_serialization():
    doc_id = str(uuid.uuid4())
    schema = DocumentSummary(
        id=doc_id,
        document_id=str(uuid.uuid4()),
        summary_text="This is a summary",
        prompt_version="v1",
        provider="openai",
        model="gpt-4",
        token_estimate_in=100,
        token_estimate_out=50,
        created_at=datetime.now()
    )
    data = schema.model_dump(by_alias=True)
    assert data["summaryText"] == "This is a summary"
    assert data["promptVersion"] == "v1"

def test_ingest_request_serialization():
    schema = IngestRequest(force_reingest=True)
    data = schema.model_dump(by_alias=True)
    assert data["forceReingest"] is True

    schema_default = IngestRequest()
    assert schema_default.force_reingest is False

def test_ingest_response_serialization():
    doc_id = str(uuid.uuid4())
    ext_id = str(uuid.uuid4())
    schema = IngestResponse(
        document_id=doc_id,
        extraction_id=ext_id,
        status="success",
        summary="Brief summary"
    )
    data = schema.model_dump(by_alias=True)
    assert data["documentId"] == doc_id
    assert data["extractionId"] == ext_id
    assert data["status"] == "success"
    assert data["summary"] == "Brief summary"
