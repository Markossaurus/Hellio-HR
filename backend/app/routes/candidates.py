import copy
import uuid
from typing import Any

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import get_current_user
from ..db import get_db
from ..models import Candidate, CandidatePosition, Document, DocumentSummary, Position, User

router = APIRouter()


def _dt_to_str(value):
    return value.isoformat() if value else None


def _get_latest_cv_document(db: Session, candidate_id) -> Document | None:
    stmt = (
        select(Document)
        .where(Document.candidate_id == candidate_id)
        .where(Document.type == "cv")
        .order_by(Document.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()



def _build_candidate_response_dict(db: Session, candidate: Candidate) -> dict[str, Any]:
    profile_json = copy.deepcopy(candidate.profile.profile_json) if candidate.profile else {}

    # Get latest CV document and its summary
    cv_doc = _get_latest_cv_document(db, candidate.id)
    summary_text = None
    if cv_doc:
        summary = db.execute(
            select(DocumentSummary)
            .where(DocumentSummary.document_id == cv_doc.id)
            .order_by(DocumentSummary.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if summary:
            summary_text = summary.summary_text

    # Base candidate fields (authoritative)
    data: dict[str, Any] = {
        "id": str(candidate.id),
        "status": candidate.status,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "title": candidate.title,
        "created_at": _dt_to_str(candidate.created_at),
        "updated_at": _dt_to_str(candidate.updated_at),
        "skills": profile_json.get("skills") or [],
        "experience": profile_json.get("experience") or [],
        "education": profile_json.get("education") or [],
        "summary": summary_text,  # Use DocumentSummary instead of profile_json
        "position_ids": [str(link.position_id) for link in candidate.positions] if candidate.positions else [],
        "cv_document": None,
    }

    if cv_doc:
        data["cv_document"] = {
            "id": str(cv_doc.id),
            "filename": cv_doc.display_name,
            "path": f"/documents/{cv_doc.id}/download",
            "uploaded_at": _dt_to_str(cv_doc.created_at),
        }

    return data



@router.get("", response_model=schemas.CandidateListResponse)
def list_candidates(
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> schemas.CandidateListResponse:
    stmt = select(Candidate)
    if status:
        stmt = stmt.where(Candidate.status == status)

    candidates = db.execute(stmt).scalars().all()

    out: list[schemas.CandidateResponse] = []
    for candidate in candidates:
        payload = _build_candidate_response_dict(db, candidate)
        out.append(schemas.CandidateResponse.model_validate(payload))

    return schemas.CandidateListResponse(candidates=out)


@router.get("/{candidate_id}", response_model=schemas.CandidateResponse)
def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> schemas.CandidateResponse:
    try:
        candidate_uuid = uuid.UUID(candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found") from exc

    stmt = select(Candidate).where(Candidate.id == candidate_uuid)
    candidate = db.execute(stmt).scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    payload = _build_candidate_response_dict(db, candidate)
    return schemas.CandidateResponse.model_validate(payload)


@router.post("/{candidate_id}/positions/{position_id}", response_model=schemas.CandidateResponse)
def add_candidate_position(
    candidate_id: str,
    position_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> schemas.CandidateResponse:
    candidate_uuid = _parse_uuid(candidate_id)
    position_uuid = _parse_uuid(position_id)

    candidate = db.execute(select(Candidate).where(Candidate.id == candidate_uuid)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    position = db.execute(select(Position).where(Position.id == position_uuid)).scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")

    existing = (
        db.execute(
            select(CandidatePosition)
            .where(CandidatePosition.candidate_id == candidate.id)
            .where(CandidatePosition.position_id == position.id)
        )
        .scalars()
        .first()
    )

    now = datetime.now(timezone.utc)
    if not existing:
        db.add(
            CandidatePosition(
                candidate_id=candidate.id,
                position_id=position.id,
                stage="applied",
                applied_at=now,
                created_at=now,
                updated_at=now,
            )
        )
    candidate.updated_at = now
    db.commit()

    payload = _build_candidate_response_dict(db, candidate)
    return schemas.CandidateResponse.model_validate(payload)


@router.delete("/{candidate_id}/positions/{position_id}", response_model=schemas.CandidateResponse)
def remove_candidate_position(
    candidate_id: str,
    position_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> schemas.CandidateResponse:
    candidate_uuid = _parse_uuid(candidate_id)
    position_uuid = _parse_uuid(position_id)

    candidate = db.execute(select(Candidate).where(Candidate.id == candidate_uuid)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    link = (
        db.execute(
            select(CandidatePosition)
            .where(CandidatePosition.candidate_id == candidate_uuid)
            .where(CandidatePosition.position_id == position_uuid)
        )
        .scalars()
        .first()
    )

    if link:
        db.delete(link)
        candidate.updated_at = datetime.now(timezone.utc)
        db.commit()

    payload = _build_candidate_response_dict(db, candidate)
    return schemas.CandidateResponse.model_validate(payload)


def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from exc
