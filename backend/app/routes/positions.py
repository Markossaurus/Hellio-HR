import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user, require_roles
from app.db import get_db
from app.models import Position, User

router = APIRouter()


def _position_to_response(position: Position) -> schemas.PositionResponse:
    salary_range = None
    if (
        position.salary_min is not None
        or position.salary_max is not None
        or position.salary_currency is not None
    ):
        salary_range = schemas.SalaryRange(
            min=position.salary_min,
            max=position.salary_max,
            currency=position.salary_currency,
        )
    def dt_to_str(dt: datetime | None) -> str | None:
        return dt.isoformat() if dt else None
    return schemas.PositionResponse(
        id=str(position.id),
        status=position.status,
        title=position.title,
        department=position.department,
        location=position.location,
        type=position.type,
        summary=position.summary,
        responsibilities=position.responsibilities or [],
        requirements=position.requirements or [],
        nice_to_have=position.nice_to_have or [],
        salary_range=salary_range,
        created_at=dt_to_str(position.created_at),
        updated_at=dt_to_str(position.updated_at),
        closed_at=dt_to_str(position.closed_at),
    )


@router.get("", response_model=schemas.PositionListResponse)
def list_positions(
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> schemas.PositionListResponse:
    stmt = select(Position)
    if status:
        stmt = stmt.where(Position.status == status)
    positions = db.execute(stmt).scalars().all()
    return schemas.PositionListResponse(
        positions=[_position_to_response(position) for position in positions]
    )


@router.get("/{position_id}", response_model=schemas.PositionResponse)
def get_position(
    position_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> schemas.PositionResponse:
    try:
        position_uuid = uuid.UUID(position_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found") from exc
    stmt = select(Position).where(Position.id == position_uuid)
    position = db.execute(stmt).scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
    return _position_to_response(position)


@router.patch("/{position_id}", response_model=schemas.PositionResponse)
def update_position(
    position_id: str,
    payload: schemas.PositionUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["editor", "admin"])),
) -> schemas.PositionResponse:
    try:
        position_uuid = uuid.UUID(position_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found") from exc
    stmt = select(Position).where(Position.id == position_uuid)
    position = db.execute(stmt).scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")

    update_data = payload.model_dump(exclude_none=True)
    update_data.pop("salary_range", None)

    for field, value in update_data.items():
        setattr(position, field, value)

    if payload.salary_range is not None:
        position.salary_min = payload.salary_range.min
        position.salary_max = payload.salary_range.max
        position.salary_currency = payload.salary_range.currency

    position.updated_at = datetime.now(timezone.utc)
    db.add(position)
    db.commit()
    db.refresh(position)
    return _position_to_response(position)
