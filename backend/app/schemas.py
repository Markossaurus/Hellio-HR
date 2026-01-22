from __future__ import annotations

from datetime import datetime
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
