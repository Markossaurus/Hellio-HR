from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, candidates, documents, positions

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
app.include_router(documents.router, tags=["documents"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
