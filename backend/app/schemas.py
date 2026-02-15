from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class LoginRequest(BaseSchema):
    email: str
    password: str


class UserInfo(BaseSchema):
    id: str
    email: str
    roles: list[str]


class LoginResponse(BaseSchema):
    token: str
    user: UserInfo


class CandidateSkill(BaseSchema):
    id: str
    name: str
    level: str


class CandidateExperience(BaseSchema):
    id: str
    company: str
    title: str
    start_date: str
    end_date: str
    description: str


class CandidateEducation(BaseSchema):
    id: str
    institution: str
    degree: str
    field: str
    start_date: str
    end_date: str


class CandidateCvDocument(BaseSchema):
    id: str | None = None
    filename: str
    path: str
    uploaded_at: str


class CandidateResponse(BaseSchema):
    id: str
    status: str
    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    title: str | None = None
    summary: str | None = None
    skills: list[CandidateSkill] = Field(default_factory=list)
    experience: list[CandidateExperience] = Field(default_factory=list)
    education: list[CandidateEducation] = Field(default_factory=list)
    position_ids: list[str] = Field(default_factory=list)
    cv_document: CandidateCvDocument | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CandidateListResponse(BaseSchema):
    candidates: list[CandidateResponse]


class SalaryRange(BaseSchema):
    min: int | None = None
    max: int | None = None
    currency: str | None = None


class PositionResponse(BaseSchema):
    id: str
    status: str
    title: str
    department: str | None = None
    location: str | None = None
    type: str | None = None
    summary: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    salary_range: SalaryRange | None = None
    created_at: str | None = None
    updated_at: str | None = None
    closed_at: str | None = None


class PositionListResponse(BaseSchema):
    positions: list[PositionResponse]


class CandidateSuggestion(BaseSchema):
    candidate_id: str
    name: str
    title: str | None
    explanation: str


class PositionSuggestionsResponse(BaseSchema):
    position_id: str
    suggestions: list[CandidateSuggestion]


class PositionSuggestion(BaseSchema):
    position_id: str
    title: str
    department: str | None
    explanation: str


class CandidateSuggestionsResponse(BaseSchema):
    candidate_id: str
    suggestions: list[PositionSuggestion]


class PositionUpdateRequest(BaseSchema):
    status: str | None = None
    title: str | None = None
    department: str | None = None
    location: str | None = None
    type: str | None = None
    summary: str | None = None
    responsibilities: list[str] | None = None
    requirements: list[str] | None = None
    nice_to_have: list[str] | None = None
    salary_range: SalaryRange | None = None
    closed_at: datetime | None = None


class ExtractionStatus(str, Enum):
    SUCCESS = "success"
    FAILED_VALIDATION = "failed_validation"
    LLM_ERROR = "llm_error"
    PARSE_ERROR = "parse_error"


class DocumentUploadResponse(BaseSchema):
    id: str
    content_hash: str
    status: str
    message: str


class DocumentMetadata(BaseSchema):
    id: str
    type: str
    content_type: str
    display_name: str
    content_hash: str
    candidate_id: str | None = None
    created_at: datetime


class DocumentText(BaseSchema):
    id: str
    extracted_text: str
    parser_version: str
    created_at: datetime


class DocumentExtraction(BaseSchema):
    id: str
    document_id: str
    heuristic_json: dict[str, Any]
    llm_raw_output: str
    extracted_json_validated: dict[str, Any] | None = None
    extraction_schema_version: str
    status: ExtractionStatus
    error_details: dict[str, Any] | None = None
    provider: str
    model: str
    prompt_version: str
    token_estimate_in: int | None = None
    token_estimate_out: int | None = None
    cost_estimate_usd: float | None = None
    elapsed_ms: int | None = None
    created_at: datetime


class DocumentSummary(BaseSchema):
    id: str
    document_id: str
    summary_text: str
    prompt_version: str
    provider: str
    model: str
    token_estimate_in: int | None = None
    token_estimate_out: int | None = None
    created_at: datetime


class IngestRequest(BaseSchema):
    force_reingest: bool = False


class IngestResponse(BaseSchema):
    document_id: str
    extraction_id: str | None = None
    status: str
    summary: str
    candidate_id: str | None = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    history: list[dict[str, Any]] | None = None
    model: str = "ollama"
    retrieval_mode: str = "sql"


class ChatResponse(BaseModel):
    answer: str | None = None
    sql: str | None = None
    row_count: int | None = None
    columns: list[str] | None = None
    error: str | None = None
