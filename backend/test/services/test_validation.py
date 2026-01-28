import json
from typing import TypedDict, cast

from app.services.validation import JSONObject, normalize_dates, normalize_skills, validate_extraction


class SkillDict(TypedDict):
    id: str
    name: str
    level: str


class ExperienceDict(TypedDict):
    id: str
    company: str
    title: str
    start_date: str
    end_date: str
    description: str


class EducationDict(TypedDict):
    id: str
    institution: str
    degree: str
    field: str
    start_date: str
    end_date: str


class ExtractionDict(TypedDict):
    name: str
    email: str
    phone: str
    location: str
    title: str
    summary: str
    skills: list[SkillDict]
    experience: list[ExperienceDict]
    education: list[EducationDict]


def _valid_payload() -> ExtractionDict:
    return {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+1-555-0100",
        "location": "London, UK",
        "title": "Software Engineer",
        "summary": "Experienced engineer.",
        "skills": [
            {"id": "skill_1", "name": "Python", "level": "Expert"},
            {"id": "skill_2", "name": "SQL", "level": "Intermediate"},
        ],
        "experience": [
            {
                "id": "exp_1",
                "company": "ACME",
                "title": "Engineer",
                "start_date": "January 2020",
                "end_date": "present",
                "description": "Built systems.",
            }
        ],
        "education": [
            {
                "id": "edu_1",
                "institution": "University",
                "degree": "BS",
                "field": "Computer Science",
                "start_date": "2016",
                "end_date": "2019",
            }
        ],
    }


def test_validate_extraction_accepts_valid_payload():
    payload: ExtractionDict = _valid_payload()

    extraction, errors = validate_extraction(json.dumps(payload))

    assert errors == []
    assert extraction is not None
    extraction_data = cast(ExtractionDict, extraction)
    assert extraction_data["name"] == "Ada Lovelace"
    assert extraction_data["skills"][0]["level"] == "Expert"


def test_validate_extraction_rejects_invalid_json():
    extraction, errors = validate_extraction("{not valid json}")

    assert extraction is None
    assert errors


def test_validate_extraction_rejects_missing_fields():
    payload: ExtractionDict = _valid_payload()
    _ = payload.pop("skills")

    extraction, errors = validate_extraction(json.dumps(payload))

    assert extraction is None
    assert errors


def test_normalize_dates_and_skills():
    payload: ExtractionDict = _valid_payload()

    normalized = cast(ExtractionDict, normalize_skills(normalize_dates(cast(JSONObject, payload))))

    assert normalized["experience"][0]["start_date"] == "2020-01"
    assert normalized["experience"][0]["end_date"] == "present"
    assert normalized["education"][0]["start_date"] == "2016"
    assert normalized["skills"][0]["level"] == "expert"
    assert normalized["skills"][1]["level"] == "intermediate"


def test_normalize_dates_leaves_unknown_format_unchanged():
    payload: ExtractionDict = _valid_payload()
    payload["experience"][0]["start_date"] = "Q1 2020"

    normalized = cast(ExtractionDict, normalize_dates(cast(JSONObject, payload)))

    assert normalized["experience"][0]["start_date"] == "Q1 2020"
