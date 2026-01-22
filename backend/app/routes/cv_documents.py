import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.db import get_db
from app.models import CvDocument, User

router = APIRouter()


@router.get("/{document_id}/download")
def download_cv(
    document_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        document_uuid = uuid.UUID(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found") from exc
    stmt = select(CvDocument).where(CvDocument.id == document_uuid)
    cv_document = db.execute(stmt).scalar_one_or_none()
    if not cv_document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    base_path = Path(settings.cv_storage_path).resolve()
    file_path = (base_path / cv_document.reference).resolve()
    if base_path not in file_path.parents and file_path != base_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        path=str(file_path),
        filename=cv_document.display_name,
        media_type=media_type or "application/octet-stream",
    )
