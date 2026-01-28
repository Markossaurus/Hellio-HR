import json
import uuid
from collections.abc import Callable, Iterator
from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


def _ensure_auth_tables(test_db: Session) -> None:
    _ = test_db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
    )
    _ = test_db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
    )
    _ = test_db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id TEXT NOT NULL,
                role_id TEXT NOT NULL,
                PRIMARY KEY (user_id, role_id)
            )
            """
        )
    )
    _ = test_db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS auth_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,
                created_at TEXT
            )
            """
        )
    )
    test_db.commit()


def _ensure_candidate_tables(test_db: Session) -> None:
    _ = test_db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                location TEXT,
                title TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
    )
    _ = test_db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS candidate_profiles (
                id TEXT PRIMARY KEY,
                candidate_id TEXT UNIQUE NOT NULL,
                profile_json TEXT NOT NULL,
                schema_version TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
    )
    _ = test_db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS candidate_positions (
                id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                position_id TEXT NOT NULL,
                stage TEXT,
                applied_at TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
    )
    _ = test_db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS cv_documents (
                id TEXT PRIMARY KEY,
                candidate_id TEXT,
                display_name TEXT NOT NULL,
                source TEXT,
                reference TEXT NOT NULL,
                uploaded_at TEXT
            )
            """
        )
    )
    test_db.commit()


def _normalize_user_ids(test_db: Session) -> None:
    new_user_id = str(uuid.uuid4())
    new_role_id = str(uuid.uuid4())
    new_token_id = str(uuid.uuid4())

    _ = test_db.execute(
        text("UPDATE users SET id = :new_id WHERE id = :old_id"),
        {"new_id": new_user_id, "old_id": "test-user-id"},
    )
    _ = test_db.execute(
        text("UPDATE roles SET id = :new_id WHERE id = :old_id"),
        {"new_id": new_role_id, "old_id": "test-role-id"},
    )
    _ = test_db.execute(
        text(
            """
            UPDATE user_roles
            SET user_id = :new_user_id, role_id = :new_role_id
            WHERE user_id = :old_user_id AND role_id = :old_role_id
            """
        ),
        {
            "new_user_id": new_user_id,
            "new_role_id": new_role_id,
            "old_user_id": "test-user-id",
            "old_role_id": "test-role-id",
        },
    )

    _ = test_db.execute(
        text("UPDATE auth_tokens SET id = :new_id WHERE id = :old_id"),
        {"new_id": new_token_id, "old_id": "test-token-id"},
    )
    _ = test_db.execute(
        text("UPDATE auth_tokens SET user_id = :new_id WHERE user_id = :old_id"),
        {"new_id": new_user_id, "old_id": "test-user-id"},
    )
    test_db.commit()


def _seed_auth_placeholders_for_token(test_db: Session, token: str) -> None:
    import hashlib
    from datetime import datetime, timezone

    _ensure_auth_tables(test_db)

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at_str = "9999-12-31 23:59:59"

    _ = test_db.execute(text("DELETE FROM auth_tokens"))
    _ = test_db.execute(text("DELETE FROM user_roles"))
    _ = test_db.execute(text("DELETE FROM users"))
    _ = test_db.execute(text("DELETE FROM roles"))

    _ = test_db.execute(
        text("INSERT INTO roles (id, name) VALUES (:id, :name)"),
        {"id": "test-role-id", "name": "admin"},
    )
    _ = test_db.execute(
        text(
            """
            INSERT INTO users (id, email, password_hash, created_at, updated_at)
            VALUES (:id, :email, :hash, :created, :updated)
            """
        ),
        {
            "id": "test-user-id",
            "email": "test@example.com",
            "hash": "dummy",
            "created": now.isoformat(sep=" "),
            "updated": now.isoformat(sep=" "),
        },
    )
    _ = test_db.execute(
        text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
        {"user_id": "test-user-id", "role_id": "test-role-id"},
    )
    _ = test_db.execute(
        text(
            """
            INSERT INTO auth_tokens (id, user_id, token_hash, expires_at, created_at)
            VALUES (:id, :user_id, :hash, :expires, :created)
            """
        ),
        {
            "id": "test-token-id",
            "user_id": "test-user-id",
            "hash": token_hash,
            "expires": expires_at_str,
            "created": now.isoformat(sep=" "),
        },
    )
    test_db.commit()


def _prepare_auth(test_db: Session, token: str) -> None:
    _seed_auth_placeholders_for_token(test_db, token)
    _normalize_user_ids(test_db)


def _create_candidate(test_db: Session, *, status: str = "active", name: str = "Ada Lovelace") -> str:
    candidate_uuid = uuid.uuid4()
    candidate_id = str(candidate_uuid)
    profile_id = str(uuid.uuid4())
    profile = {
        "id": str(candidate_uuid),
        "status": status,
        "name": name,
    }

    _ = test_db.execute(
        text(
            """
            INSERT INTO candidates (
                id, status, name, email, phone, location, title, created_at, updated_at
            ) VALUES (
                :id, :status, :name, :email, :phone, :location, :title, :created_at, :updated_at
            )
            """
        ),
        {
            "id": candidate_id,
            "status": status,
            "name": name,
            "email": None,
            "phone": None,
            "location": None,
            "title": None,
            "created_at": None,
            "updated_at": None,
        },
    )
    _ = test_db.execute(
        text(
            """
            INSERT INTO candidate_profiles (
                id, candidate_id, profile_json, schema_version, created_at, updated_at
            ) VALUES (
                :id, :candidate_id, :profile_json, :schema_version, :created_at, :updated_at
            )
            """
        ),
        {
            "id": profile_id,
            "candidate_id": candidate_id,
            "profile_json": json.dumps(profile),
            "schema_version": "1.0",
            "created_at": None,
            "updated_at": None,
        },
    )
    test_db.commit()
    return str(candidate_uuid)


@pytest.fixture
def candidates_db(auth_token: str) -> Iterator[Callable[[], Session]]:
    import os
    import tempfile

    from app.db import get_db  # pyright: ignore[reportImplicitRelativeImport, reportUnknownVariableType]
    from app.main import app  # pyright: ignore[reportImplicitRelativeImport]

    get_db_dep = cast(Callable[..., object], get_db)

    tmp = tempfile.NamedTemporaryFile(prefix="candidates-test-", suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()

    engine = create_engine(
        f"sqlite+pysqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()
    try:
        _ensure_auth_tables(db)
        _ensure_candidate_tables(db)
        _prepare_auth(db, auth_token)
    finally:
        db.close()

    def override_get_db():
        db2 = SessionLocal()
        try:
            yield db2
        finally:
            db2.close()

    app.dependency_overrides[get_db_dep] = override_get_db

    try:
        yield SessionLocal
    finally:
        _ = app.dependency_overrides.pop(get_db_dep, None)
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_list_candidates_authenticated_returns_candidates(
    client: TestClient, candidates_db: Callable[[], Session], auth_token: str
) -> None:
    db = candidates_db()
    try:
        created_id = _create_candidate(db, status="active", name="Samira Khan")
    finally:
        db.close()

    response = client.get(
        "/candidates",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200, response.text
    assert "\"candidates\"" in response.text
    assert created_id in response.text


def test_list_candidates_unauthenticated_returns_401(client: TestClient) -> None:
    response = client.get("/candidates")
    assert response.status_code == 401


def test_get_candidate_by_id_returns_candidate(
    client: TestClient, candidates_db: Callable[[], Session], auth_token: str
) -> None:
    db = candidates_db()
    try:
        created_id = _create_candidate(db, status="active", name="Taylor Reed")
    finally:
        db.close()

    response = client.get(
        f"/candidates/{created_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200, response.text
    assert created_id in response.text
    assert "Taylor Reed" in response.text
    assert "active" in response.text


def test_get_nonexistent_candidate_returns_404(
    client: TestClient, candidates_db: Callable[[], Session], auth_token: str
) -> None:
    db = candidates_db()
    db.close()
    missing_id = str(uuid.uuid4())

    response = client.get(
        f"/candidates/{missing_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 404, response.text
    assert "Candidate not found" in response.text


def test_list_candidates_filter_by_status_returns_only_matching(
    client: TestClient, candidates_db: Callable[[], Session], auth_token: str
) -> None:
    db = candidates_db()
    try:
        active_id = _create_candidate(db, status="active", name="Alex Rivera")
        archived_id = _create_candidate(db, status="archived", name="Jordan Lee")
    finally:
        db.close()

    response = client.get(
        "/candidates?status=active",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200, response.text
    assert active_id in response.text
    assert archived_id not in response.text
    assert "active" in response.text
