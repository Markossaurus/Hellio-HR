from fastapi import APIRouter, Depends
from typing import Any
from sqlalchemy import Integer, bindparam, text
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector

from app.auth import get_current_user
from app.config import settings
from app.db import get_db
from app.models import User
from app.schemas import ChatRequest, ChatResponse
from app.services.embeddings import generate_embedding
from app.services.chat.sql_generation import generate_sql
from app.services.chat.validation import validate_sql
from app.services.chat.answer_generation import generate_answer

router = APIRouter()


async def _retrieve_rag_rows(
    question: str,
    db: Session,
    limit_each: int = 5,
) -> tuple[list[dict[str, Any]], list[str]]:
    query_embedding = await generate_embedding(question)

    candidate_stmt = text(
        "SELECT id::text AS id, 'candidate' AS source_type, name, title, location, "
        "COALESCE(embedding_text, '') AS embedding_text, embedding <=> :query_embedding AS distance "
        "FROM candidates "
        "WHERE embedding IS NOT NULL "
        "ORDER BY distance ASC "
        "LIMIT :limit"
    ).bindparams(
        bindparam("query_embedding", type_=Vector(settings.embedding_dimension)),
        bindparam("limit", type_=Integer),
    )

    position_stmt = text(
        "SELECT id::text AS id, 'position' AS source_type, title AS name, title, location, "
        "COALESCE(embedding_text, '') AS embedding_text, embedding <=> :query_embedding AS distance "
        "FROM positions "
        "WHERE embedding IS NOT NULL "
        "ORDER BY distance ASC "
        "LIMIT :limit"
    ).bindparams(
        bindparam("query_embedding", type_=Vector(settings.embedding_dimension)),
        bindparam("limit", type_=Integer),
    )

    params = {"query_embedding": query_embedding, "limit": limit_each}
    candidate_rows = [dict(row) for row in db.execute(candidate_stmt, params).mappings().all()]
    position_rows = [dict(row) for row in db.execute(position_stmt, params).mappings().all()]

    rows = sorted(candidate_rows + position_rows, key=lambda row: float(row.get("distance", 1.0)))[:10]
    columns = list(rows[0].keys()) if rows else []
    return rows, columns


@router.post("/chat", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    retrieval_mode = (request.retrieval_mode or "sql").lower()

    if retrieval_mode in {"rag", "hybrid"}:
        try:
            rag_rows, rag_columns = await _retrieve_rag_rows(request.question, db)
            if rag_rows:
                rag_answer = generate_answer(request.question, rag_rows, rag_columns)
                return ChatResponse(
                    answer=rag_answer,
                    sql="RAG retrieval",
                    row_count=len(rag_rows),
                    columns=rag_columns,
                )
            if retrieval_mode == "rag":
                return ChatResponse(
                    answer="I could not find relevant embedded context yet. Try generating embeddings first.",
                    sql="RAG retrieval",
                    row_count=0,
                    columns=[],
                )
        except Exception as e:
            if retrieval_mode == "rag":
                return ChatResponse(error=f"RAG retrieval failed: {str(e)}")

    try:
        sql = generate_sql(request.question, request.history)
    except Exception as e:
        return ChatResponse(error=f"SQL generation failed: {str(e)}")
    
    is_valid, error_msg = validate_sql(sql)
    if not is_valid:
        return ChatResponse(sql=sql, error=error_msg)
    
    if "LIMIT" not in sql.upper():
        sql = sql.rstrip(";") + " LIMIT 50"
    
    try:
        result = db.execute(text(sql))
        rows = [dict(row._mapping) for row in result]
        columns = list(rows[0].keys()) if rows else []
    except Exception as e:
        return ChatResponse(sql=sql, error=f"Query execution failed: {str(e)}")
    
    try:
        answer = generate_answer(request.question, rows, columns)
    except Exception as e:
        return ChatResponse(
            sql=sql, 
            row_count=len(rows), 
            columns=columns,
            error=f"Answer generation failed: {str(e)}"
        )
    
    return ChatResponse(
        answer=answer,
        sql=sql,
        row_count=len(rows),
        columns=columns
    )
