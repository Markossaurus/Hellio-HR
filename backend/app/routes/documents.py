import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.db import get_db
from app.models import Document, DocumentExtraction, DocumentSummary, DocumentText, User
from app.schemas import (
    DocumentExtraction as DocumentExtractionSchema,
    DocumentMetadata,
    DocumentSummary as DocumentSummarySchema,
    DocumentText as DocumentTextSchema,
    DocumentUploadResponse,
    IngestRequest,
    IngestResponse,
)
from app.services.pipeline import IngestionPipeline

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit",
        )

    content_hash = hashlib.sha256(content).hexdigest()

    db_document = Document(
        id=uuid.uuid4(),
        type="cv",
        content_type=file.content_type,
        display_name=file.filename or "uploaded_file",
        content_hash=content_hash,
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    storage_path = Path(settings.cv_storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    file_path = storage_path / str(db_document.id)

    file_path.write_bytes(content)

    return DocumentUploadResponse(
        id=str(db_document.id),
        content_hash=content_hash,
        status="success",
        message="File uploaded successfully",
    )


@router.post("/{document_id}/ingest", response_model=IngestResponse)
async def ingest_document(
    document_id: uuid.UUID,
    request: IngestRequest = IngestRequest(force_reingest=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    pipeline = IngestionPipeline()
    result = await pipeline.ingest(document_id, db, force=request.force_reingest)

    return IngestResponse(
        document_id=str(result.document_id),
        extraction_id=str(result.extraction_id) if result.extraction_id else None,
        status=result.status,
        candidate_id=str(result.candidate_id) if getattr(result, "candidate_id", None) else None,
        summary=f"Ingestion {result.status}: {', '.join(result.errors) if result.errors else 'success'}",
    )


@router.get("/{document_id}", response_model=DocumentMetadata)
def get_document_metadata(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return DocumentMetadata(
        id=str(doc.id),
        type=doc.type,
        content_type=doc.content_type,
        display_name=doc.display_name,
        content_hash=doc.content_hash,
        candidate_id=str(doc.candidate_id) if doc.candidate_id else None,
        created_at=doc.created_at,
    )


@router.get("/{document_id}/text", response_model=DocumentTextSchema)
def get_document_text(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select

    doc_text = (
        db.execute(
            select(DocumentText)
            .where(DocumentText.document_id == document_id)
            .order_by(DocumentText.created_at.desc())
        )
        .scalars()
        .first()
    )

    if not doc_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document text not found. Document may not have been ingested yet.",
        )

    return DocumentTextSchema(
        id=str(doc_text.id),
        extracted_text=doc_text.extracted_text,
        parser_version=doc_text.parser_version,
        created_at=doc_text.created_at,
    )


@router.get("/{document_id}/extractions", response_model=list[DocumentExtractionSchema])
def get_document_extractions(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select

    extractions = (
        db.execute(
            select(DocumentExtraction)
            .where(DocumentExtraction.document_id == document_id)
            .order_by(DocumentExtraction.created_at.desc())
        )
        .scalars()
        .all()
    )

    return [
        DocumentExtractionSchema(
            id=str(e.id),
            document_id=str(e.document_id),
            heuristic_json=e.heuristic_json,
            llm_raw_output=e.llm_raw_output,
            extracted_json_validated=e.extracted_json_validated,
            extraction_schema_version=e.extraction_schema_version,
            status=e.status,
            error_details=e.error_details,
            provider=e.provider,
            model=e.model,
            prompt_version=e.prompt_version,
            token_estimate_in=e.token_estimate_in,
            token_estimate_out=e.token_estimate_out,
            cost_estimate_usd=e.cost_estimate_usd,
            elapsed_ms=e.elapsed_ms,
            created_at=e.created_at,
        )
        for e in extractions
    ]


@router.get("/{document_id}/summaries", response_model=list[DocumentSummarySchema])
def get_document_summaries(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select

    summaries = (
        db.execute(
            select(DocumentSummary)
            .where(DocumentSummary.document_id == document_id)
            .order_by(DocumentSummary.created_at.desc())
        )
        .scalars()
        .all()
    )

    return [
        DocumentSummarySchema(
            id=str(s.id),
            document_id=str(s.document_id),
            summary_text=s.summary_text,
            prompt_version=s.prompt_version,
            provider=s.provider,
            model=s.model,
            token_estimate_in=s.token_estimate_in,
            token_estimate_out=s.token_estimate_out,
            created_at=s.created_at,
        )
        for s in summaries
    ]

@router.get("/{document_id}/download")
def download_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(settings.cv_storage_path) / str(document_id)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Use the original filename if you want:
    filename = doc.display_name or f"{document_id}.pdf"
    media_type = doc.content_type or "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )