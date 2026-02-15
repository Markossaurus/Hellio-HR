from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, CITEXT, UUID as PG_UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class UUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type for PostgreSQL, String(36) for SQLite and others.
    """
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return uuid.UUID(value)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    roles: Mapped[list[Role]] = relationship("Role", secondary="user_roles", back_populates="users")
    tokens: Mapped[list[AuthToken]] = relationship("AuthToken", back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[list[User]] = relationship("User", secondary="user_roles", back_populates="roles")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("users.id"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("roles.id"), primary_key=True
    )


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    embedding_text: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))

    profile: Mapped[CandidateProfile | None] = relationship(
        "CandidateProfile", back_populates="candidate", uselist=False
    )
    positions: Mapped[list[CandidatePosition]] = relationship(
        "CandidatePosition", back_populates="candidate"
    )
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="candidate")



class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("candidates.id"), unique=True)
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), server_default="1.0")
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    candidate: Mapped[Candidate] = relationship("Candidate", back_populates="profile")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[str | None] = mapped_column(String(50))
    summary: Mapped[str | None] = mapped_column(Text)
    responsibilities: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    requirements: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    nice_to_have: Mapped[list[str] | None] = mapped_column("nice_to_have", ARRAY(Text))
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    embedding_text: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))

    candidates: Mapped[list[CandidatePosition]] = relationship(
        "CandidatePosition", back_populates="position"
    )


class CandidatePosition(Base):
    __tablename__ = "candidate_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("candidates.id"))
    position_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("positions.id"))
    stage: Mapped[str | None] = mapped_column(String(50), server_default="applied")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    candidate: Mapped[Candidate] = relationship("Candidate", back_populates="positions")
    position: Mapped[Position] = relationship("Position", back_populates="candidates")

class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship("User", back_populates="tokens")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(), ForeignKey("candidates.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate: Mapped[Candidate | None] = relationship("Candidate", back_populates="documents")
    texts: Mapped[list[DocumentText]] = relationship("DocumentText", back_populates="document", cascade="all, delete-orphan")
    extractions: Mapped[list[DocumentExtraction]] = relationship("DocumentExtraction", back_populates="document", cascade="all, delete-orphan")
    summaries: Mapped[list[DocumentSummary]] = relationship("DocumentSummary", back_populates="document", cascade="all, delete-orphan")


class DocumentText(Base):
    __tablename__ = "document_texts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    parser_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship("Document", back_populates="texts")


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    heuristic_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    llm_raw_output: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_json_validated: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    extraction_schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    error_details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    token_estimate_in: Mapped[int | None] = mapped_column(Integer)
    token_estimate_out: Mapped[int | None] = mapped_column(Integer)
    cost_estimate_usd: Mapped[float | None] = mapped_column(Numeric(10, 6))
    elapsed_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship("Document", back_populates="extractions")


class DocumentSummary(Base):
    __tablename__ = "document_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    token_estimate_in: Mapped[int | None] = mapped_column(Integer)
    token_estimate_out: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship("Document", back_populates="summaries")
