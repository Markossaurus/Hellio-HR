from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    CandidateProfile,
    Candidate,
    Document,
    DocumentExtraction,
    DocumentSummary,
    DocumentText,
)
from app.prompts import load_prompt
from app.services.heuristics import extract_all
from app.services.llm import LLMRequest, get_provider
from app.services.parsing import parse_document
from app.services.validation import validate_extraction


@dataclass
class IngestResult:
    document_id: UUID
    extraction_id: UUID | None
    summary_id: UUID | None
    status: str  # one of: success, failed_validation, llm_error, parse_error
    errors: list[str]
    candidate_id: UUID | None = None


class IngestionPipeline:
    async def ingest(
        self, document_id: UUID, db: Session, force: bool = False
    ) -> IngestResult:
        doc = db.get(Document, document_id)
        if not doc:
            return IngestResult(
                document_id=document_id,
                extraction_id=None,
                summary_id=None,
                status="parse_error",
                errors=["Document not found"],
            )

        if not force:
            existing_extraction = (
                db.execute(
                    select(DocumentExtraction)
                    .join(Document)
                    .where(Document.content_hash == doc.content_hash)
                    .where(DocumentExtraction.status == "success")
                    .order_by(DocumentExtraction.created_at.desc())
                )
                .scalars()
                .first()
            )
            if existing_extraction:
                summary = (
                    db.execute(
                        select(DocumentSummary)
                        .where(DocumentSummary.document_id == existing_extraction.document_id)
                        .order_by(DocumentSummary.created_at.desc())
                    )
                    .scalars()
                    .first()
                )
                return IngestResult(
                    document_id=document_id,
                    extraction_id=existing_extraction.id,
                    summary_id=summary.id if summary else None,
                    status="success",
                    errors=[],
                )

        try:
            file_path = Path(settings.cv_storage_path) / str(document_id)
            if not file_path.exists():
                return IngestResult(
                    document_id=document_id,
                    extraction_id=None,
                    summary_id=None,
                    status="parse_error",
                    errors=[f"File not found on disk: {file_path}"],
                )
            file_bytes = file_path.read_bytes()

            extracted_text, parser_version = parse_document(file_bytes, doc.content_type)
            doc_text = DocumentText(
                document_id=document_id,
                extracted_text=extracted_text,
                parser_version=parser_version,
            )
            db.add(doc_text)
            db.flush()

            heuristics = extract_all(extracted_text)

            prompt_version = "cv_extraction_v1"
            system_prompt = load_prompt(prompt_version)
            prompt = f"raw_cv_text: {extracted_text}\n\nheuristic_json: {json.dumps(heuristics, indent=2)}"

            provider = get_provider(settings.llm_provider)
            try:
                extraction_resp = await provider.generate(
                    LLMRequest(prompt=prompt, system_prompt=system_prompt),
                    prompt_version=prompt_version,
                )
            except Exception as exc:
                extraction = DocumentExtraction(
                    document_id=document_id,
                    heuristic_json=heuristics,
                    llm_raw_output="",
                    extraction_schema_version="1.0",
                    status="llm_error",
                    error_details={"error": str(exc)},
                    provider=settings.llm_provider,
                    model=settings.llm_model,
                    prompt_version=prompt_version,
                )
                db.add(extraction)
                db.commit()
                return IngestResult(
                    document_id=document_id,
                    extraction_id=extraction.id,
                    summary_id=None,
                    status="llm_error",
                    errors=[str(exc)],
                )

            validated_json, validation_errors = validate_extraction(extraction_resp.content)
            
            extraction = DocumentExtraction(
                document_id=document_id,
                heuristic_json=heuristics,
                llm_raw_output=extraction_resp.content,
                extracted_json_validated=validated_json,
                extraction_schema_version="1.0",
                status="success" if not validation_errors else "failed_validation",
                error_details={"validation_errors": validation_errors} if validation_errors else None,
                provider=extraction_resp.provider,
                model=extraction_resp.model,
                prompt_version=extraction_resp.prompt_version,
                token_estimate_in=extraction_resp.token_estimate_in,
                token_estimate_out=extraction_resp.token_estimate_out,
                cost_estimate_usd=extraction_resp.cost_estimate_usd,
                elapsed_ms=extraction_resp.elapsed_ms,
            )
            db.add(extraction)
            db.flush()

            if validation_errors:
                db.commit()
                return IngestResult(
                    document_id=document_id,
                    extraction_id=extraction.id,
                    summary_id=None,
                    status="failed_validation",
                    errors=validation_errors,
                )

            summary_id = None

            if validated_json:
                summary_prompt_version = "cv_summary_v1"
                summary_system_prompt = load_prompt(summary_prompt_version)
                summary_prompt = (
                    f"raw_cv_text: {extracted_text}\n\nextracted_json: {json.dumps(validated_json, indent=2)}"
                )

                try:
                    summary_resp = await provider.generate(
                        LLMRequest(prompt=summary_prompt, system_prompt=summary_system_prompt),
                        prompt_version=summary_prompt_version,
                    )
                except Exception as exc:
                    # LLM failed on summary => do NOT create candidate/profile/link doc
                    db.rollback()
                    return IngestResult(
                        document_id=document_id,
                        extraction_id=None,   # you can keep extraction.id if you want, but then you must commit it; better: None
                        summary_id=None,
                        status="llm_error",
                        errors=[f"Summary generation failed: {exc}"],
                    )

                summary = DocumentSummary(
                    document_id=document_id,
                    summary_text=summary_resp.content,
                    prompt_version=summary_resp.prompt_version,
                    provider=summary_resp.provider,
                    model=summary_resp.model,
                    token_estimate_in=summary_resp.token_estimate_in,
                    token_estimate_out=summary_resp.token_estimate_out,
                )
                db.add(summary)
                db.flush()
                summary_id = summary.id

                def _get_str(d: dict, key: str) -> str | None:
                    v = d.get(key)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
                    return None

                email = _get_str(validated_json, "email")
                phone = _get_str(validated_json, "phone")
                name = _get_str(validated_json, "name") or doc.display_name
                location = _get_str(validated_json, "location")
                title = _get_str(validated_json, "title")

                candidate = None

                if email:
                    candidate = (
                        db.execute(select(Candidate).where(func.lower(Candidate.email) == email.lower()))
                        .scalars()
                        .first()
                    )

                if not candidate and phone:
                    candidate = (
                        db.execute(select(Candidate).where(Candidate.phone == phone))
                        .scalars()
                        .first()
                    )

                if not candidate:
                    candidate = Candidate(
                        status="active",
                        name=name,
                        email=email,
                        phone=phone,
                        location=location,
                        title=title,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    db.add(candidate)
                    db.flush()
                else:
                    candidate.updated_at = datetime.now()
                    if not candidate.name and name:
                        candidate.name = name
                    if not candidate.email and email:
                        candidate.email = email
                    if not candidate.phone and phone:
                        candidate.phone = phone
                    if not candidate.location and location:
                        candidate.location = location
                    if not candidate.title and title:
                        candidate.title = title

                # Link doc -> candidate
                doc.candidate_id = candidate.id
                db.add(doc)
                db.flush()

                # update/create profile 
                profile = (
                    db.execute(select(CandidateProfile).where(CandidateProfile.candidate_id == candidate.id))
                    .scalars()
                    .first()
                )
                if not profile:
                    profile = CandidateProfile(
                        candidate_id=candidate.id,
                        profile_json=validated_json,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    db.add(profile)
                else:
                    profile.profile_json = validated_json
                    profile.updated_at = datetime.now()
            
            db.commit()
            return IngestResult(
                document_id=document_id,
                extraction_id=extraction.id,
                summary_id=summary_id,
                status="success",
                errors=[],
            )

        except Exception as exc:
            db.rollback()
            return IngestResult(
                document_id=document_id,
                extraction_id=None,
                summary_id=None,
                status="parse_error",
                errors=[str(exc)],
            )
