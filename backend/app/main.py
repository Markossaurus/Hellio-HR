import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import SessionLocal
from .routes import auth, candidates, chat, documents, positions, suggestions
from .services.positions_seed import seed_positions_from_assets

app = FastAPI(title="Hellio HR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
app.include_router(positions.router, prefix="/positions", tags=["positions"])
app.include_router(suggestions.router, tags=["suggestions"])
app.include_router(documents.router, tags=["documents"])
app.include_router(chat.router, tags=["chat"])

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def load_positions_assets() -> None:
    db = SessionLocal()
    try:
        await seed_positions_from_assets(db)
    except Exception as exc:
        logger.exception("Failed to seed positions from assets: %s", exc)
    finally:
        db.close()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
