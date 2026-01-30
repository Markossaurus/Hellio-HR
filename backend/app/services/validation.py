from __future__ import annotations

import copy
import json
import re
from typing import ClassVar, TypeAlias

from pydantic import BaseModel, ConfigDict, ValidationError as PydanticValidationError

from ..schemas import CandidateEducation, CandidateExperience, CandidateSkill

_MONTH_MAP = {
    "january": "01",
    "jan": "01",
    "february": "02",
    "feb": "02",
    "march": "03",
    "mar": "03",
    "april": "04",
    "apr": "04",
    "may": "05",
    "june": "06",
    "jun": "06",
    "july": "07",
    "jul": "07",
    "august": "08",
    "aug": "08",
    "september": "09",
    "sep": "09",
    "sept": "09",
    "october": "10",
    "oct": "10",
    "november": "11",
    "nov": "11",
    "december": "12",
    "dec": "12",
}

_LEVEL_ALIASES = {
    "beginner": "beginner",
    "novice": "beginner",
    "junior": "beginner",
    "entry": "beginner",
    "intermediate": "intermediate",
    "mid": "intermediate",
    "midlevel": "intermediate",
    "advanced": "advanced",
    "proficient": "advanced",
    "expert": "expert",
    "senior": "expert",
    "master": "expert",
}

JSONPrimitive: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONPrimitive | list["JSONValue"] | dict[str, "JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]


class ValidationError(Exception):
    def __init__(self, message: str, *, details: list[str] | None = None) -> None:
        super().__init__(message)
        self.details = details or []


class ExtractionSchema(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")
    name: str | None
    email: str | None
    phone: str | None
    location: str | None
    title: str | None
    summary: str | None
    skills: list[CandidateSkill]
    experience: list[CandidateExperience]
    education: list[CandidateEducation]





def validate_extraction(raw_json: str) -> tuple[JSONObject | None, list[str]]:
    try:
        payload: JSONValue = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON: {exc.msg}"]

    if not isinstance(payload, dict):
        return None, ["Invalid JSON: root must be an object"]


    try:
        extraction = ExtractionSchema.model_validate(payload)
    except PydanticValidationError as exc:
        errors: list[str] = []
        for error in exc.errors():
            loc = ".".join(str(part) for part in error.get("loc", []))
            msg = error.get("msg", "Invalid value")
            errors.append(f"{loc}: {msg}" if loc else msg)
        return None, errors

    return extraction.model_dump(), []


def normalize_dates(extraction: JSONObject) -> JSONObject:
    normalized = copy.deepcopy(extraction)
    for section in ("experience", "education"):
        items_value = normalized.get(section)
        if not isinstance(items_value, list):
            continue
        for item_value in items_value:
            if not isinstance(item_value, dict):
                continue
            for field in ("start_date", "end_date"):
                value = item_value.get(field)
                if not isinstance(value, str) or not value.strip():
                    continue
                item_value[field] = _normalize_date_value(value)
    return normalized


def normalize_skills(extraction: JSONObject) -> JSONObject:
    normalized = copy.deepcopy(extraction)
    skills_value = normalized.get("skills")
    if not isinstance(skills_value, list):
        return normalized
    for skill_value in skills_value:
        if not isinstance(skill_value, dict):
            continue
        level = skill_value.get("level")
        if not isinstance(level, str):
            continue
        skill_value["level"] = _normalize_level(level)
    return normalized


def _normalize_date_value(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in {"present", "current", "ongoing"}:
        return "present"
    if re.match(r"^\d{4}-\d{2}$", lowered):
        return lowered
    match = re.match(r"^(\d{4})-(\d{1})$", lowered)
    if match:
        return f"{match.group(1)}-0{match.group(2)}"
    if re.match(r"^\d{4}$", lowered):
        return lowered
    match = re.match(r"^(?P<month>[a-zA-Z]+)\s+(?P<year>\d{4})$", lowered)
    if match:
        month = _MONTH_MAP.get(match.group("month").lower())
        if month:
            return f"{match.group('year')}-{month}"
    return value


def _normalize_level(level: str) -> str:
    cleaned = level.strip().lower()
    key = re.sub(r"[\s\-_/]+", "", cleaned)
    return _LEVEL_ALIASES.get(key, cleaned)
