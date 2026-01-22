import copy
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from app.db import get_db
from app.models import Candidate, User

router = APIRouter()


def _dt_to_str(value):
    return value.isoformat() if value else None


def _build_candidate_profile(candidate: Candidate) -> dict:
    profile = copy.deepcopy(candidate.profile.profile_json) if candidate.profile else {}
    if "id" not in profile:
        profile["id"] = str(candidate.id)
    if "status" not in profile:
        profile["status"] = candidate.status
    if "name" not in profile:
        profile["name"] = candidate.name
    if candidate.email is not None and "email" not in profile:
        profile["email"] = candidate.email
    if candidate.phone is not None and "phone" not in profile:
        profile["phone"] = candidate.phone
    if candidate.location is not None and "location" not in profile:
        profile["location"] = candidate.location
    if candidate.title is not None and "title" not in profile:
        profile["title"] = candidate.title
    if "createdAt" not in profile and candidate.created_at:
        profile["createdAt"] = _dt_to_str(candidate.created_at)
    if "updatedAt" not in profile and candidate.updated_at:
        profile["updatedAt"] = _dt_to_str(candidate.updated_at)

    for key in ("skills", "experience", "education"):
        if profile.get(key) is None:
            profile[key] = []

    if "positionIds" not in profile or not profile["positionIds"]:
        profile["positionIds"] = [str(link.position_id) for link in candidate.positions]

    if candidate.cv_documents:
        cv_document = candidate.cv_documents[0]
        if isinstance(profile.get("cvDocument"), dict):
            profile["cvDocument"].setdefault("id", str(cv_document.id))
            profile["cvDocument"].setdefault("filename", cv_document.display_name)
            profile["cvDocument"].setdefault("path", cv_document.reference)
            if cv_document.uploaded_at:
                profile["cvDocument"].setdefault("uploadedAt", _dt_to_str(cv_document.uploaded_at))
            if any(
                not profile["cvDocument"].get(key)
                for key in ("filename", "path", "uploadedAt")
            ):
                profile["cvDocument"] = None
        elif cv_document.uploaded_at:
            profile["cvDocument"] = {
                "id": str(cv_document.id),
                "filename": cv_document.display_name,
                "path": cv_document.reference,
                "uploadedAt": _dt_to_str(cv_document.uploaded_at),
            }

    return profile


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
    profiles: list[schemas.CandidateResponse] = []
    for candidate in candidates:
        if not candidate.profile:
            continue
        profile = _build_candidate_profile(candidate)
        profiles.append(schemas.CandidateResponse.model_validate(profile))
    return schemas.CandidateListResponse(candidates=profiles)


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
    if not candidate or not candidate.profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    profile = _build_candidate_profile(candidate)
    return schemas.CandidateResponse.model_validate(profile)
