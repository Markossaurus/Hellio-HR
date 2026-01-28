# pyright: ignore[reportIgnoreCommentWithoutRule, reportUnnecessaryTypeIgnoreComment]
from __future__ import annotations

import re


EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[\s.-]*)?(?:\(?\d{3}\)?[\s.-]*)\d{3}[\s.-]*\d{4}"
)
URL_REGEX = re.compile(r"\b(?:https?://|www\.)[^\s<>()]+", re.IGNORECASE)

MONTH_NAMES = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t)?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_RANGE_SEP = r"(?:\s*[-\u2013]\s*)"
DATE_PATTERNS = [
    re.compile(
        rf"\b{MONTH_NAMES}\s+\d{{4}}{DATE_RANGE_SEP}(?:{MONTH_NAMES}\s+\d{{4}}|Present|Current)\b",
        re.IGNORECASE,
    ),
    re.compile(rf"\b\d{{1,2}}/\d{{4}}{DATE_RANGE_SEP}\d{{1,2}}/\d{{4}}\b"),
    re.compile(rf"\b\d{{4}}{DATE_RANGE_SEP}(?:\d{{4}}|Present|Current)\b"),
]

EXPERIENCE_HEADER = re.compile(r"^(work\s+)?experience\b", re.IGNORECASE)
EDUCATION_HEADER = re.compile(r"^education\b", re.IGNORECASE)
SKILLS_HEADER = re.compile(
    r"^(technical\s+skills|skills\s*&\s*tools|skills|tools|technologies)\b",
    re.IGNORECASE,
)

__all__ = [
    "extract_all",
    "extract_dates",
    "extract_emails",
    "extract_phones",
    "extract_section_headers",
    "extract_urls",
]


UrlMatch = dict[str, str]
HeaderMatch = dict[str, str | int]
HeuristicPayload = dict[str, list[str] | list[UrlMatch] | list[HeaderMatch]]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        results.append(item)
    return results


def extract_emails(text: str) -> list[str]:
    return _dedupe([match.group(0) for match in EMAIL_REGEX.finditer(text)])


def extract_phones(text: str) -> list[str]:
    results: list[str] = []
    for match in PHONE_REGEX.finditer(text):
        raw = match.group(0).strip().strip(".,;:")
        digits = re.sub(r"\D", "", raw)
        if len(digits) < 10:
            continue
        results.append(raw)
    return _dedupe(results)


def extract_urls(text: str) -> list[UrlMatch]:
    urls: list[UrlMatch] = []
    for match in URL_REGEX.finditer(text):
        raw = match.group(0).rstrip(").,;:")
        lowered = raw.lower()
        if "linkedin.com" in lowered:
            url_type = "linkedin"
        elif "github.com" in lowered:
            url_type = "github"
        else:
            url_type = "other"
        urls.append({"url": raw, "type": url_type})
    return urls


def extract_dates(text: str) -> list[str]:
    matches: list[tuple[int, int, str]] = []
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end(), match.group(0)))

    matches.sort(key=lambda item: item[0])
    results: list[str] = []
    seen_spans: set[tuple[int, int]] = set()
    for start, end, value in matches:
        if (start, end) in seen_spans:
            continue
        seen_spans.add((start, end))
        results.append(value)
    return results


def extract_section_headers(text: str) -> list[HeaderMatch]:
    headers: list[HeaderMatch] = []
    for index, line in enumerate(text.splitlines(), start=1):
        raw_line = line.strip()
        if not raw_line:
            continue
        cleaned = raw_line.rstrip(":").strip()
        if EXPERIENCE_HEADER.match(cleaned):
            category = "experience"
        elif EDUCATION_HEADER.match(cleaned):
            category = "education"
        elif SKILLS_HEADER.match(cleaned):
            category = "skills"
        else:
            continue
        headers.append({"header": cleaned, "category": category, "line": index})
    return headers


def extract_all(text: str) -> HeuristicPayload:
    return {
        "emails": extract_emails(text),
        "phones": extract_phones(text),
        "urls": extract_urls(text),
        "dates": extract_dates(text),
        "section_headers": extract_section_headers(text),
    }
