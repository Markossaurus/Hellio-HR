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


def _coerce_to_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _coerce_fields(payload: JSONObject) -> JSONObject:
    exp = payload.get("experience")
    if isinstance(exp, list):
        for item in exp:
            if not isinstance(item, dict):
                continue

            # required string fields
            if "id" in item:
                item["id"] = _coerce_to_str(item.get("id"))
            if "company" in item:
                item["company"] = _coerce_to_str(item.get("company"))
            if "title" in item:
                item["title"] = _coerce_to_str(item.get("title"))
            if "description" in item:
                item["description"] = _coerce_to_str(item.get("description"))
            if "start_date" in item:
                item["start_date"] = _coerce_to_str(item.get("start_date"))
            if "end_date" in item:
                item["end_date"] = _coerce_to_str(item.get("end_date"))

    edu = payload.get("education")
    if isinstance(edu, list):
        for item in edu:
            if not isinstance(item, dict):
                continue

            if "id" in item:
                item["id"] = _coerce_to_str(item.get("id"))
            if "institution" in item:
                item["institution"] = _coerce_to_str(item.get("institution"))
            if "degree" in item:
                item["degree"] = _coerce_to_str(item.get("degree"))
            if "field" in item:
                item["field"] = _coerce_to_str(item.get("field"))
            if "start_date" in item:
                item["start_date"] = _coerce_to_str(item.get("start_date"))
            if "end_date" in item:
                item["end_date"] = _coerce_to_str(item.get("end_date"))

    skills = payload.get("skills")
    if isinstance(skills, list):
        for item in skills:
            if not isinstance(item, dict):
                continue

            if "id" in item:
                item["id"] = _coerce_to_str(item.get("id"))
            if "name" in item:
                item["name"] = _coerce_to_str(item.get("name"))
            if "level" in item:
                item["level"] = _coerce_to_str(item.get("level"))

    for key in ("name", "email", "phone", "location", "title", "summary"):
        if key in payload:
            payload[key] = _coerce_to_str(payload.get(key))

    return payload




def validate_extraction(raw_json: str) -> tuple[JSONObject | None, list[str]]:
    try:
        payload: JSONValue = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON: {exc.msg}"]

    if not isinstance(payload, dict):
        return None, ["Invalid JSON: root must be an object"]

    payload = _coerce_fields(payload)

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
