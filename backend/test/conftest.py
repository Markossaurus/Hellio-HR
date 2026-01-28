"""Test fixtures for backend suite."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from collections.abc import Generator
import sqlite3
import uuid

sqlite3.register_adapter(uuid.UUID, lambda value: str(value))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Engine
from sqlalchemy import text

from app.main import app
from app.db import get_db


@pytest.fixture(scope="session")
def sqlite_engine() -> Generator[Engine, None, None]:
    """Create shared in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    metadata = MetaData()
    Table(
        'users', metadata,
        Column('id', String(36), primary_key=True),
        Column('email', String(255), unique=True, nullable=False),
        Column('password_hash', String(255), nullable=False),
        Column('created_at', String(50)),
        Column('updated_at', String(50))
    )
    Table(
        'roles', metadata,
        Column('id', String(36), primary_key=True),
        Column('name', String(50), unique=True, nullable=False)
    )
    Table(
        'auth_tokens', metadata,
        Column('id', String(36), primary_key=True),
        Column('user_id', String(36), nullable=False),
        Column('token_hash', String(64), nullable=False),
        Column('expires_at', String(50), nullable=False),
        Column('revoked_at', String(50)),
        Column('created_at', String(50))
    )
    Table(
        'user_roles', metadata,
        Column('user_id', String(36), primary_key=True),
        Column('role_id', String(36), primary_key=True)
    )

    metadata.create_all(engine)
    yield engine


@pytest.fixture(scope="session")
def session_factory(sqlite_engine: Engine):
    return sessionmaker(
        bind=sqlite_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@pytest.fixture
def test_db(session_factory) -> Generator[Session, None, None]:
    """Provide a SQLAlchemy Session for direct db access in tests."""
    db = session_factory()
    from sqlalchemy import text

    for table in ("auth_tokens", "user_roles", "roles", "users"):
        db.execute(text(f"DELETE FROM {table}"))
    db.commit()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """Create a TestClient with overridden database dependency."""
    def override_get_db() -> Generator[Session, None, None]:
        test_db.expire_all()
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db: Session):
    """Create a test user in database."""
    from sqlalchemy import text
    
    test_user_id = "12345678-1234-5678-1234-567812345678"
    test_role_id = "87654321-4321-8765-4321-876543210987"
    
    # Create admin role
    test_db.execute(text("INSERT INTO roles (id, name) VALUES (:id, :name)"), 
                   {"id": test_role_id, "name": "admin"})
    
    # Create test user
    test_db.execute(text("""
        INSERT INTO users (id, email, password_hash, created_at, updated_at) 
        VALUES (:id, :email, :hash, :created, :updated)
    """), {
        "id": test_user_id, 
        "email": "test@example.com",
        "hash": "$2b$12$dummy_hash_for_testing",
        "created": "2024-01-01T00:00:00Z",
        "updated": "2024-01-01T00:00:00Z"
    })
    
    # Link user to role
    test_db.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
                   {"user_id": test_user_id, "role_id": test_role_id})
    
    test_db.commit()
    
    # Return a simple object that mimics User interface
    class SimpleUser:
        def __init__(self):
            self.id = test_user_id
            self.email = "test@example.com"
    
    return SimpleUser()


@pytest.fixture
def auth_token(test_user, test_db: Session) -> str:
    """Create a valid JWT token for the test user."""
    import secrets
    import hashlib
    from datetime import datetime, timezone, timedelta
    
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    from sqlalchemy import text
    test_db.execute(text("""
        INSERT INTO auth_tokens (id, user_id, token_hash, expires_at, created_at) 
        VALUES (:id, :user_id, :hash, :expires, :created)
    """), {
        "id": "test-token-id",
        "user_id": test_user.id,
        "hash": token_hash,
        "expires": expires_at.isoformat(),
        "created": datetime.now(timezone.utc).isoformat()
    })
    
    test_db.commit()
    return token
