import pytest
from uuid import uuid4, UUID
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.pipeline import IngestionPipeline, IngestResult
from app.models import Document, DocumentText, DocumentExtraction, DocumentSummary, Candidate, CandidateProfile, Base
from app.services.llm import LLMResponse
from sqlalchemy.orm import Session
from sqlalchemy import Table, text

@pytest.fixture(autouse=True)
def setup_db_tables(test_db: Session):
    engine = test_db.get_bind()
    tables = [
        cast(Table, Candidate.__table__),
        cast(Table, CandidateProfile.__table__),
        cast(Table, Document.__table__),
        cast(Table, DocumentText.__table__),
        cast(Table, DocumentExtraction.__table__),
        cast(Table, DocumentSummary.__table__),
    ]
    Base.metadata.create_all(engine, tables=tables)
    
    for table in ["document_summaries", "document_extractions", "document_texts", "documents", "candidate_profiles", "candidates"]:
        test_db.execute(text(f"DELETE FROM {table}"))
    test_db.commit()
    yield

@pytest.fixture
def candidate(test_db: Session):
    c = Candidate(id=uuid4(), name="John Doe", status="new")
    test_db.add(c)
    test_db.commit()
    return c

@pytest.fixture
def document(test_db: Session, candidate):
    doc = Document(
        id=uuid4(),
        type="cv",
        content_type="application/pdf",
        display_name="resume.pdf",
        content_hash="abc123hash",
        candidate_id=candidate.id
    )
    test_db.add(doc)
    test_db.commit()
    return doc

@pytest.mark.asyncio
async def test_ingest_success_path(test_db: Session, document, candidate):
    pipeline = IngestionPipeline()
    
    parsed_text = "Extracted CV text"
    parser_version = "test-parser-1.0"
    heuristics = {"emails": ["test@example.com"]}
    llm_raw_output = '{"name": "John Doe", "skills": []}'
    validated_json = {
        "name": "John Doe",
        "summary": "Backend engineer with API experience",
        "skills": [{"name": "Python"}],
        "experience": [],
        "education": [],
    }
    summary_text = "A qualified candidate."
    
    with patch("app.services.pipeline.Path") as mock_path_class, \
         patch("app.services.pipeline.parse_document", return_value=(parsed_text, parser_version)), \
         patch("app.services.pipeline.extract_all", return_value=heuristics), \
         patch("app.services.pipeline.load_prompt", side_effect=lambda name: f"Prompt for {name}"), \
         patch("app.services.pipeline.get_provider") as mock_get_provider, \
         patch("app.services.pipeline.validate_extraction", return_value=(validated_json, [])), \
         patch("app.services.pipeline.generate_embedding", new=AsyncMock(return_value=[0.1] * 768)):
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_bytes.return_value = b"pdf content"
        mock_path_class.return_value.__truediv__.return_value = mock_path
        
        mock_provider = AsyncMock()
        mock_get_provider.return_value = mock_provider
        
        mock_provider.generate.side_effect = [
            LLMResponse(content=llm_raw_output, provider="test", model="test-model", 
                        prompt_version="v1", token_estimate_in=10, token_estimate_out=10, 
                        elapsed_ms=100, cost_estimate_usd=0.0),
            LLMResponse(content='{"summary": "A qualified candidate."}', provider="test", model="test-model", 
                        prompt_version="v1", token_estimate_in=10, token_estimate_out=10, 
                        elapsed_ms=100, cost_estimate_usd=0.0)
        ]
        
        result = await pipeline.ingest(document.id, test_db)
        
        assert result.status == "success"
        assert result.document_id == document.id
        assert result.extraction_id is not None
        assert result.summary_id is not None
        assert len(result.errors) == 0
        
        test_db.refresh(document)
        assert len(document.texts) == 1
        assert document.texts[0].extracted_text == parsed_text
        
        assert len(document.extractions) == 1
        assert document.extractions[0].status == "success"
        assert document.extractions[0].llm_raw_output == llm_raw_output
        assert document.extractions[0].extracted_json_validated == validated_json
        
        assert len(document.summaries) == 1
        assert document.summaries[0].summary_text == summary_text
        
        test_db.refresh(document)
        linked_candidate = test_db.get(Candidate, document.candidate_id)
        assert linked_candidate is not None
        assert linked_candidate.profile is not None
        assert linked_candidate.profile.profile_json["name"] == "John Doe"
        assert linked_candidate.embedding is not None
        assert linked_candidate.embedding_text is not None


@pytest.mark.asyncio
async def test_ingest_fails_when_embedding_generation_fails(test_db: Session, document):
    pipeline = IngestionPipeline()

    validated_json = {
        "name": "John Doe",
        "summary": "Backend engineer with API experience",
        "skills": [{"name": "Python"}],
        "experience": [],
        "education": [],
    }

    with patch("app.services.pipeline.Path") as mock_path_class, \
         patch("app.services.pipeline.parse_document", return_value=("Extracted CV text", "test-parser-1.0")), \
         patch("app.services.pipeline.extract_all", return_value={"emails": ["test@example.com"]}), \
         patch("app.services.pipeline.load_prompt", side_effect=lambda name: f"Prompt for {name}"), \
         patch("app.services.pipeline.get_provider") as mock_get_provider, \
         patch("app.services.pipeline.validate_extraction", return_value=(validated_json, [])), \
         patch("app.services.pipeline.generate_embedding", new=AsyncMock(side_effect=RuntimeError("embedding unavailable"))):

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_bytes.return_value = b"pdf content"
        mock_path_class.return_value.__truediv__.return_value = mock_path

        mock_provider = AsyncMock()
        mock_get_provider.return_value = mock_provider
        mock_provider.generate.side_effect = [
            LLMResponse(
                content='{"name": "John Doe", "skills": [{"name": "Python"}]}',
                provider="test",
                model="test-model",
                prompt_version="v1",
                token_estimate_in=10,
                token_estimate_out=10,
                elapsed_ms=100,
                cost_estimate_usd=0.0,
            ),
            LLMResponse(
                content='{"summary": "A qualified candidate."}',
                provider="test",
                model="test-model",
                prompt_version="v1",
                token_estimate_in=10,
                token_estimate_out=10,
                elapsed_ms=100,
                cost_estimate_usd=0.0,
            ),
        ]

        result = await pipeline.ingest(document.id, test_db)

    assert result.status == "llm_error"
    assert result.summary_id is None
    assert result.extraction_id is None
    assert "Embedding generation failed" in result.errors[0]

    test_db.refresh(document)
    assert len(document.texts) == 0
    assert len(document.extractions) == 0
    assert len(document.summaries) == 0

@pytest.mark.asyncio
async def test_ingest_parsing_failure(test_db: Session, document):
    pipeline = IngestionPipeline()
    
    with patch("app.services.pipeline.Path") as mock_path_class, \
         patch("app.services.pipeline.parse_document", side_effect=Exception("Parsing failed")):
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_bytes.return_value = b"pdf content"
        mock_path_class.return_value.__truediv__.return_value = mock_path

        result = await pipeline.ingest(document.id, test_db)
        
        assert result.status == "parse_error"
        assert "Parsing failed" in result.errors[0]
        
        test_db.refresh(document)
        assert len(document.texts) == 0
        assert len(document.extractions) == 0

@pytest.mark.asyncio
async def test_ingest_llm_failure(test_db: Session, document):
    pipeline = IngestionPipeline()
    
    with patch("app.services.pipeline.Path") as mock_path_class, \
         patch("app.services.pipeline.parse_document", return_value=("text", "v1")), \
         patch("app.services.pipeline.extract_all", return_value={}), \
         patch("app.services.pipeline.load_prompt", return_value="prompt"), \
         patch("app.services.pipeline.get_provider") as mock_get_provider:
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_bytes.return_value = b"pdf content"
        mock_path_class.return_value.__truediv__.return_value = mock_path

        mock_provider = AsyncMock()
        mock_get_provider.return_value = mock_provider
        mock_provider.generate.side_effect = Exception("LLM connection failed")
        
        result = await pipeline.ingest(document.id, test_db)
        
        assert result.status == "llm_error"
        assert "LLM connection failed" in result.errors[0]
        
        test_db.refresh(document)
        assert len(document.extractions) == 1
        assert document.extractions[0].status == "llm_error"

@pytest.mark.asyncio
async def test_ingest_validation_failure(test_db: Session, document):
    pipeline = IngestionPipeline()
    
    with patch("app.services.pipeline.Path") as mock_path_class, \
         patch("app.services.pipeline.parse_document", return_value=("text", "v1")), \
         patch("app.services.pipeline.extract_all", return_value={}), \
         patch("app.services.pipeline.load_prompt", return_value="prompt"), \
         patch("app.services.pipeline.get_provider") as mock_get_provider, \
         patch("app.services.pipeline.validate_extraction", return_value=(None, ["Invalid field"])):
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_bytes.return_value = b"pdf content"
        mock_path_class.return_value.__truediv__.return_value = mock_path

        mock_provider = AsyncMock()
        mock_get_provider.return_value = mock_provider
        mock_provider.generate.return_value = LLMResponse(
            content="bad json", provider="test", model="test", prompt_version="v1",
            token_estimate_in=1, token_estimate_out=1, elapsed_ms=1, cost_estimate_usd=0
        )
        
        result = await pipeline.ingest(document.id, test_db)
        
        assert result.status == "failed_validation"
        assert "Invalid field" in result.errors
        
        test_db.refresh(document)
        assert len(document.extractions) == 1
        assert document.extractions[0].status == "failed_validation"
        assert document.extractions[0].error_details == {"validation_errors": ["Invalid field"]}

@pytest.mark.asyncio
async def test_ingest_idempotency(test_db: Session, document):
    pipeline = IngestionPipeline()
    
    doc2 = Document(
        id=uuid4(),
        type="cv",
        content_type="application/pdf",
        display_name="resume2.pdf",
        content_hash=document.content_hash,
        candidate_id=document.candidate_id
    )
    test_db.add(doc2)
    
    extraction = DocumentExtraction(
        document_id=document.id,
        status="success",
        heuristic_json={},
        llm_raw_output="{}",
        extraction_schema_version="v1",
        provider="test",
        model="test",
        prompt_version="v1"
    )
    test_db.add(extraction)
    test_db.commit()
    
    result = await pipeline.ingest(doc2.id, test_db, force=False)
    
    assert result.status == "success"
    assert result.extraction_id == extraction.id
    
    test_db.refresh(doc2)
    assert len(doc2.extractions) == 0
