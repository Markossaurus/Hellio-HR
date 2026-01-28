import copy
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from app.db import get_db
from app.models import Candidate, User, Document

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



def _build_candidate_response_dict(db: Session, candidate: Candidate) -> dict:
    profile_json = copy.deepcopy(candidate.profile.profile_json) if candidate.profile else {}

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
        "summary": profile_json.get("summary"),
        "position_ids": [str(link.position_id) for link in candidate.positions] if candidate.positions else [],
        "cv_document": None,
    }

    cv_doc = _get_latest_cv_document(db, candidate.id)
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

