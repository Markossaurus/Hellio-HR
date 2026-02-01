from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import ChatRequest, ChatResponse
from app.services.chat.sql_generation import generate_sql
from app.services.chat.validation import validate_sql
from app.services.chat.answer_generation import generate_answer

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
