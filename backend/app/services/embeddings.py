from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ollama import Client
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import Integer, bindparam, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Candidate, Position
from app.prompts import load_prompt


logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    id: UUID
    distance: float
    name: str
    title: str | None

    @property
    def candidate_id(self) -> UUID:
        return self.id

    @property
    def position_id(self) -> UUID:
        return self.id


@dataclass
class RerankResult:
    id: UUID
    name: str
    title: str | None
    vector_distance: float
    llm_score: int
    llm_reason: str


class RerankResponse(BaseModel):
    score: int = Field(ge=1, le=10)
    reason: str


def _get_str(d: dict[str, Any], key: str) -> str | None:
    value = d.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _join_date_range(start_date: str | None, end_date: str | None) -> str | None:
    if start_date and end_date:
        return f"{start_date} - {end_date}"
    if start_date:
        return start_date
    if end_date:
        return end_date
    return None


def _format_bullet_section(title: str, values: list[str]) -> str | None:
    cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
    if not cleaned:
        return None
    return "\n".join([f"{title}:", *[f"- {item}" for item in cleaned]])


def _truncate_text(text_value: str) -> str:
    return text_value[:8000]


def build_candidate_embedding_text(
    candidate: Candidate | None = None,
    profile_json: dict[str, Any] | None = None,
    summary_text: str | None = None,
    *,
    name: str | None = None,
    title: str | None = None,
    summary: str | None = None,
) -> str:
    profile = profile_json or {}

    candidate_name = name or (candidate.name.strip() if candidate and candidate.name else None)
    candidate_title = title or (candidate.title.strip() if candidate and candidate.title else None)
    candidate_summary = summary or summary_text or _get_str(profile, "summary")

    lines: list[str] = []
    if candidate_name:
        lines.append(f"Name: {candidate_name}")
    if candidate_title:
        lines.append(f"Title: {candidate_title}")
    if candidate_summary:
        lines.append(f"Summary: {candidate_summary}")

    skills: list[str] = []
    for item in profile.get("skills") or []:
        if not isinstance(item, dict):
            continue
        skill_name = _get_str(item, "name")
        if skill_name:
            skills.append(skill_name.lower())
    if skills:
        lines.append(f"Skills: {', '.join(skills)}")

    experiences: list[str] = []
    for item in profile.get("experience") or []:
        if not isinstance(item, dict):
            continue
        experience_title = _get_str(item, "title")
        company = _get_str(item, "company")
        start_date = _get_str(item, "start_date") or _get_str(item, "startDate")
        end_date = _get_str(item, "end_date") or _get_str(item, "endDate")
        date_range = _join_date_range(start_date, end_date)

        if experience_title and company and date_range:
            experiences.append(f"{experience_title} at {company} ({date_range})")
        elif experience_title and company:
            experiences.append(f"{experience_title} at {company}")
        elif experience_title:
            experiences.append(experience_title)

    if experiences:
        lines.append(f"Experience: {'; '.join(experiences)}")

    return _truncate_text("\n".join(lines))


def build_position_embedding_text(position: Position) -> str:
    lines: list[str] = []

    if position.title and position.title.strip():
        lines.append(f"Title: {position.title.strip()}")
    if position.department and position.department.strip():
        lines.append(f"Department: {position.department.strip()}")
    if position.summary and position.summary.strip():
        lines.append(f"Summary: {position.summary.strip()}")

    requirements = _format_bullet_section("Requirements", position.requirements or [])
    responsibilities = _format_bullet_section("Responsibilities", position.responsibilities or [])
    nice_to_have = _format_bullet_section("Nice to Have", position.nice_to_have or [])

    for section in (requirements, responsibilities, nice_to_have):
        if section:
            lines.append(section)

    return _truncate_text("\n".join(lines))


async def generate_embedding(text_value: str) -> list[float]:
    if not text_value or not text_value.strip():
        raise ValueError("Cannot generate embedding for empty text")

    start_time = time.time()
    client = Client(host=settings.ollama_base_url)

    try:
        response = client.embeddings(model=settings.embedding_model, prompt=text_value)
    except Exception as exc:
        raise RuntimeError(f"Ollama API error: {exc}") from exc

    embedding_raw = response.get("embedding")
    if not isinstance(embedding_raw, list):
        raise RuntimeError("Ollama API error: missing embedding vector")

    try:
        embedding = [float(value) for value in embedding_raw]
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Ollama API error: invalid embedding values") from exc

    if len(embedding) != settings.embedding_dimension:
        raise RuntimeError(
            f"Ollama API error: expected embedding dimension {settings.embedding_dimension}, got {len(embedding)}"
        )

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(
        "Generated embedding model=%s text_length=%d elapsed_ms=%d",
        settings.embedding_model,
        len(text_value),
        elapsed_ms,
    )

    return embedding


async def generate_embedding_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    chunk_size = 50
    results: list[list[float]] = []
    total = len(texts)

    for index in range(0, total, chunk_size):
        chunk = texts[index : index + chunk_size]
        for text_item in chunk:
            results.append(await generate_embedding(text_item))
            logger.info("Generating embeddings: %d/%d", len(results), total)

    return results


def find_similar_candidates(
    position_id: UUID,
    db: Session,
    limit: int = 3,
    exclude_ids: list[UUID] | None = None,
) -> list[SimilarityResult]:
    position = db.get(Position, position_id)
    if not position or not position.embedding:
        return []

    query_sql = (
        "SELECT id, name, title, embedding <=> :query_embedding AS distance "
        "FROM candidates "
        "WHERE embedding IS NOT NULL"
    )

    params: dict[str, Any] = {
        "query_embedding": position.embedding,
        "limit": limit,
    }

    statement = text(query_sql)
    statement = statement.bindparams(
        bindparam("query_embedding", type_=Vector(settings.embedding_dimension)),
        bindparam("limit", type_=Integer),
    )

    if exclude_ids:
        statement = text(f"{query_sql} AND id NOT IN :exclude_ids ORDER BY distance ASC LIMIT :limit")
        statement = statement.bindparams(
            bindparam("query_embedding", type_=Vector(settings.embedding_dimension)),
            bindparam("exclude_ids", expanding=True),
            bindparam("limit", type_=Integer),
        )
        params["exclude_ids"] = exclude_ids
    else:
        statement = text(f"{query_sql} ORDER BY distance ASC LIMIT :limit")
        statement = statement.bindparams(
            bindparam("query_embedding", type_=Vector(settings.embedding_dimension)),
            bindparam("limit", type_=Integer),
        )

    rows = db.execute(statement, params).mappings().all()

    results: list[SimilarityResult] = []
    for row in rows:
        distance = float(row["distance"])
        if distance < settings.similarity_threshold:
            results.append(
                SimilarityResult(
                    id=row["id"],
                    distance=distance,
                    name=row["name"],
                    title=row["title"],
                )
            )
    return results


def find_similar_positions(
    candidate_id: UUID,
    db: Session,
    limit: int = 3,
) -> list[SimilarityResult]:
    candidate = db.get(Candidate, candidate_id)
    if not candidate or not candidate.embedding:
        return []

    statement = text(
        "SELECT id, title AS name, title, embedding <=> :query_embedding AS distance "
        "FROM positions "
        "WHERE embedding IS NOT NULL "
        "ORDER BY distance ASC "
        "LIMIT :limit"
    ).bindparams(
        bindparam("query_embedding", type_=Vector(settings.embedding_dimension)),
        bindparam("limit", type_=Integer),
    )

    rows = db.execute(
        statement,
        {"query_embedding": candidate.embedding, "limit": limit},
    ).mappings().all()

    results: list[SimilarityResult] = []
    for row in rows:
        distance = float(row["distance"])
        if distance < settings.similarity_threshold:
            results.append(
                SimilarityResult(
                    id=row["id"],
                    distance=distance,
                    name=row["name"],
                    title=row["title"],
                )
            )
    return results


def _render_prompt(template: str, candidate_text: str, position_text: str, score: float | None = None) -> str:
    rendered = template.replace("{candidate_text}", candidate_text).replace("{position_text}", position_text)
    if score is not None:
        rendered = rendered.replace("{score}", str(score))
    return rendered


async def generate_match_explanation(candidate_text: str, position_text: str, score: float) -> str:
    client = Client(host=settings.ollama_base_url)
    prompt = _render_prompt(
        load_prompt("match_explanation_v1"),
        candidate_text=candidate_text,
        position_text=position_text,
        score=score,
    )

    try:
        response = client.chat(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a recruitment assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response["message"]["content"].strip()
    except Exception:
        return "Match found (explanation unavailable)"


def _extract_similarity_id(item: Any) -> UUID | None:
    raw_id = getattr(item, "id", None)
    if raw_id is None:
        raw_id = getattr(item, "candidate_id", None)
    if raw_id is None:
        raw_id = getattr(item, "position_id", None)
    if isinstance(raw_id, UUID):
        return raw_id
    if isinstance(raw_id, str):
        try:
            return UUID(raw_id)
        except ValueError:
            return None
    return None


def _extract_similarity_distance(item: Any) -> float:
    distance = getattr(item, "distance", None)
    if distance is None:
        distance = getattr(item, "vector_distance", None)
    if isinstance(distance, (int, float)):
        return float(distance)
    return 0.0


async def _rerank_pair(candidate_text: str, position_text: str) -> RerankResponse:
    client = Client(host=settings.ollama_base_url)
    prompt = _render_prompt(
        load_prompt("reranking_v1"),
        candidate_text=candidate_text,
        position_text=position_text,
    )
    response = client.chat(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "You are a recruitment matching expert."},
            {"role": "user", "content": prompt},
        ],
        format=RerankResponse.model_json_schema(),
    )

    content = response["message"]["content"]
    try:
        return RerankResponse.model_validate_json(content)
    except ValidationError:
        payload = json.loads(content)
        return RerankResponse.model_validate(payload)


async def rerank_candidates(
    candidates: list[Any],
    position_text: str,
    db: Session | None = None,
) -> list[RerankResult]:
    reranked: list[RerankResult] = []

    for item in candidates:
        item_id = _extract_similarity_id(item)
        name = getattr(item, "name", "Unknown")
        title = getattr(item, "title", None)
        vector_distance = _extract_similarity_distance(item)
        candidate_text = getattr(item, "embedding_text", None)

        if not candidate_text and db and item_id:
            candidate = db.get(Candidate, item_id)
            candidate_text = candidate.embedding_text if candidate else None

        if not isinstance(candidate_text, str) or not candidate_text.strip():
            reranked.append(
                RerankResult(
                    id=item_id or UUID(int=0),
                    name=name,
                    title=title,
                    vector_distance=vector_distance,
                    llm_score=0,
                    llm_reason="Profile text unavailable for reranking",
                )
            )
            continue

        try:
            llm_result = await _rerank_pair(candidate_text, position_text)
            reranked.append(
                RerankResult(
                    id=item_id or UUID(int=0),
                    name=name,
                    title=title,
                    vector_distance=vector_distance,
                    llm_score=llm_result.score,
                    llm_reason=llm_result.reason,
                )
            )
        except Exception as exc:
            logger.warning("Candidate reranking failed for id=%s: %s", item_id, exc)
            reranked.append(
                RerankResult(
                    id=item_id or UUID(int=0),
                    name=name,
                    title=title,
                    vector_distance=vector_distance,
                    llm_score=0,
                    llm_reason="Reranking unavailable",
                )
            )

    return sorted(reranked, key=lambda result: result.llm_score, reverse=True)


async def rerank_positions(
    positions: list[Any],
    candidate_text: str,
    db: Session | None = None,
) -> list[RerankResult]:
    reranked: list[RerankResult] = []

    for item in positions:
        item_id = _extract_similarity_id(item)
        name = getattr(item, "name", "Unknown")
        title = getattr(item, "title", None)
        vector_distance = _extract_similarity_distance(item)
        position_text = getattr(item, "embedding_text", None)

        if not position_text and db and item_id:
            position = db.get(Position, item_id)
            position_text = position.embedding_text if position else None

        if not isinstance(position_text, str) or not position_text.strip():
            reranked.append(
                RerankResult(
                    id=item_id or UUID(int=0),
                    name=name,
                    title=title,
                    vector_distance=vector_distance,
                    llm_score=0,
                    llm_reason="Position text unavailable for reranking",
                )
            )
            continue

        try:
            llm_result = await _rerank_pair(candidate_text, position_text)
            reranked.append(
                RerankResult(
                    id=item_id or UUID(int=0),
                    name=name,
                    title=title,
                    vector_distance=vector_distance,
                    llm_score=llm_result.score,
                    llm_reason=llm_result.reason,
                )
            )
        except Exception as exc:
            logger.warning("Position reranking failed for id=%s: %s", item_id, exc)
            reranked.append(
                RerankResult(
                    id=item_id or UUID(int=0),
                    name=name,
                    title=title,
                    vector_distance=vector_distance,
                    llm_score=0,
                    llm_reason="Reranking unavailable",
                )
            )

    return sorted(reranked, key=lambda result: result.llm_score, reverse=True)
