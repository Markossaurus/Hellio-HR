import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import get_current_user
from ..db import get_db
from ..models import Candidate, CandidatePosition, Position, User
from ..services.embeddings import (
    build_candidate_embedding_text,
    build_position_embedding_text,
    find_similar_candidates,
    find_similar_positions,
    generate_match_explanation,
    generate_embedding_batch,
    rerank_candidates,
    rerank_positions,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/admin/generate-embeddings")
async def generate_embeddings_for_missing_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    is_admin = any(role.name.lower() == "admin" for role in current_user.roles)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    errors: list[str] = []
    candidates_processed = 0
    positions_processed = 0

    candidates = list(db.execute(select(Candidate).where(Candidate.embedding.is_(None))).scalars().all())
    for i in range(0, len(candidates), 50):
        batch = candidates[i : i + 50]
        texts: list[str] = []
        items: list[Candidate] = []

        for candidate in batch:
            try:
                profile_json = candidate.profile.profile_json if candidate.profile else {}
                if not (profile_json.get("summary") or profile_json.get("skills")):
                    continue
                embedding_text = build_candidate_embedding_text(
                    candidate,
                    profile_json=profile_json,
                    summary_text=profile_json.get("summary"),
                )
                texts.append(embedding_text)
                items.append(candidate)
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}")
                errors.append(f"candidate:{candidate.id}:{e}")
                continue

        if not texts:
            continue

        try:
            embeddings = await generate_embedding_batch(texts)
            for idx, candidate in enumerate(items):
                candidate.embedding_text = texts[idx]
                candidate.embedding = embeddings[idx]
                candidates_processed += 1
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            errors.append(f"candidate_batch:{i}:{e}")
            continue

    positions = list(db.execute(select(Position).where(Position.embedding.is_(None))).scalars().all())
    for i in range(0, len(positions), 50):
        batch = positions[i : i + 50]
        position_texts: list[str] = []
        position_items: list[Position] = []

        for position in batch:
            try:
                embedding_text = build_position_embedding_text(position)
                position_texts.append(embedding_text)
                position_items.append(position)
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}")
                errors.append(f"position:{position.id}:{e}")
                continue

        if not position_texts:
            continue

        try:
            embeddings = await generate_embedding_batch(position_texts)
            for idx, position in enumerate(position_items):
                position.embedding_text = position_texts[idx]
                position.embedding = embeddings[idx]
                positions_processed += 1
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            errors.append(f"position_batch:{i}:{e}")
            continue

    db.commit()
    return {
        "candidates_processed": candidates_processed,
        "positions_processed": positions_processed,
        "errors": errors,
    }


@router.get("/positions/{position_id}/suggestions", response_model=schemas.PositionSuggestionsResponse)
async def get_position_suggestions(
    position_id: str,
    limit: int = Query(default=3, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.PositionSuggestionsResponse:
    try:
        position_uuid = uuid.UUID(position_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found") from exc

    position = db.execute(select(Position).where(Position.id == position_uuid)).scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")

    if position.embedding is None:
        return schemas.PositionSuggestionsResponse(position_id=str(position.id), suggestions=[])

    applied_candidate_ids = list(
        db.execute(
        select(CandidatePosition.candidate_id).where(CandidatePosition.position_id == position.id)
        ).scalars().all()
    )

    vector_results = find_similar_candidates(position.id, db, limit=10, exclude_ids=applied_candidate_ids)
    reranked_results = await rerank_candidates(vector_results, position.embedding_text or "", db)

    suggestions: list[schemas.CandidateSuggestion] = []
    for result in reranked_results[:limit]:
        explanation = result.llm_reason.strip() if result.llm_reason else ""
        if not explanation:
            candidate = db.get(Candidate, result.id)
            explanation = await generate_match_explanation(
                candidate.embedding_text if candidate and candidate.embedding_text else "",
                position.embedding_text or "",
                float(result.llm_score),
            )

        suggestions.append(
            schemas.CandidateSuggestion(
                candidate_id=str(result.id),
                name=result.name,
                title=result.title,
                explanation=explanation,
            )
        )

    return schemas.PositionSuggestionsResponse(position_id=str(position.id), suggestions=suggestions)


@router.get("/candidates/{candidate_id}/suggestions", response_model=schemas.CandidateSuggestionsResponse)
async def get_candidate_suggestions(
    candidate_id: str,
    limit: int = Query(default=3, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.CandidateSuggestionsResponse:
    try:
        candidate_uuid = uuid.UUID(candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found") from exc

    candidate = db.execute(select(Candidate).where(Candidate.id == candidate_uuid)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    if candidate.embedding is None:
        return schemas.CandidateSuggestionsResponse(candidate_id=str(candidate.id), suggestions=[])

    vector_results = find_similar_positions(candidate.id, db, limit=10)
    reranked_results = await rerank_positions(vector_results, candidate.embedding_text or "", db)

    filtered_results = [result for result in reranked_results if result.llm_score >= 5][:limit]
    position_ids = [result.id for result in filtered_results]
    positions = db.execute(select(Position).where(Position.id.in_(position_ids))).scalars().all()
    positions_by_id = {position.id: position for position in positions}

    suggestions: list[schemas.PositionSuggestion] = []
    for result in filtered_results:
        position = positions_by_id.get(result.id)
        explanation = result.llm_reason.strip() if result.llm_reason else ""
        if not explanation:
            explanation = await generate_match_explanation(
                candidate.embedding_text or "",
                position.embedding_text if position and position.embedding_text else "",
                float(result.llm_score),
            )

        suggestions.append(
            schemas.PositionSuggestion(
                position_id=str(result.id),
                title=result.title or result.name,
                department=position.department if position else None,
                explanation=explanation,
            )
        )

    return schemas.CandidateSuggestionsResponse(candidate_id=str(candidate.id), suggestions=suggestions)
