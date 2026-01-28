# pyright: ignore[reportIgnoreCommentWithoutRule, reportUnnecessaryTypeIgnoreComment]
from __future__ import annotations

from app.services.heuristics import (
    extract_all,
    extract_dates,
    extract_emails,
    extract_phones,
    extract_section_headers,
    extract_urls,
)


def test_extract_emails_finds_multiple_addresses():
    text = """Contact: john.doe@example.com
    Backup: hr@company.co.uk
    """

    assert extract_emails(text) == ["john.doe@example.com", "hr@company.co.uk"]


def test_extract_phones_finds_common_formats():
    text = """Call +1 (415) 555-2671 or 415-555-2671.
    Alt: 415 555 2671
    """

    assert extract_phones(text) == [
        "+1 (415) 555-2671",
        "415-555-2671",
        "415 555 2671",
    ]


def test_extract_urls_classifies_known_sites():
    text = """https://www.linkedin.com/in/jane-doe
    https://github.com/janedoe
    https://portfolio.example.com
    """

    assert extract_urls(text) == [
        {"url": "https://www.linkedin.com/in/jane-doe", "type": "linkedin"},
        {"url": "https://github.com/janedoe", "type": "github"},
        {"url": "https://portfolio.example.com", "type": "other"},
    ]


def test_extract_dates_finds_date_ranges():
    text = """Jan 2020 - Feb 2021
    03/2019-07/2020
    2022 - Present
    """

    assert extract_dates(text) == [
        "Jan 2020 - Feb 2021",
        "03/2019-07/2020",
        "2022 - Present",
    ]


def test_extract_section_headers_finds_major_sections():
    text = """Experience
    Senior Engineer at Example

    EDUCATION
    University of Somewhere

    Skills & Tools
    Python, SQL
    """

    assert extract_section_headers(text) == [
        {"header": "Experience", "category": "experience", "line": 1},
        {"header": "EDUCATION", "category": "education", "line": 4},
        {"header": "Skills & Tools", "category": "skills", "line": 7},
    ]


def test_extract_all_returns_unified_payload():
    text = """Jane Doe
    Email: jane@example.com
    Phone: 555-123-4567
    LinkedIn: https://www.linkedin.com/in/jane-doe
    Experience
    Jan 2020 - Feb 2021
    """

    result = extract_all(text)

    assert result["emails"] == ["jane@example.com"]
    assert result["phones"] == ["555-123-4567"]
    assert result["urls"] == [
        {"url": "https://www.linkedin.com/in/jane-doe", "type": "linkedin"}
    ]
    assert result["dates"] == ["Jan 2020 - Feb 2021"]
    assert result["section_headers"] == [
        {"header": "Experience", "category": "experience", "line": 5}
    ]
