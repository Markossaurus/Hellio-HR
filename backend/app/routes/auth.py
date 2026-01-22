from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.auth import create_token, verify_password
from app.db import get_db
from app.models import User

router = APIRouter()


@router.post("/login", response_model=schemas.LoginResponse)
def login(
    payload: schemas.LoginRequest, db: Session = Depends(get_db)
) -> schemas.LoginResponse:
    stmt = select(User).where(User.email == payload.email)
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token(user.id, db)
    roles = [role.name for role in user.roles]
    return schemas.LoginResponse(
        token=token,
        user=schemas.UserInfo(id=str(user.id), email=user.email, roles=roles),
    )
