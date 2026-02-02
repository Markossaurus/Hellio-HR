from __future__ import annotations

import logging
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict
from xml.etree import ElementTree as ET

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Position

logger = logging.getLogger(__name__)


class JobRecord(TypedDict):
    job_number: str
    title: str
    hiring_manager: str
    description_file: str


class ParsedJob(TypedDict):
    summary: str | None
    responsibilities: list[str]
    requirements: list[str]
    nice_to_have: list[str]
    location: str | None


def seed_positions_from_assets(db: Session) -> None:
    assets_path = Path(settings.positions_assets_path)
    if not assets_path.exists():
        logger.warning("Positions assets path missing: %s", assets_path)
        return

    xlsx_path = assets_path / "jobs.xlsx"
    if not xlsx_path.exists():
        logger.warning("Positions spreadsheet missing: %s", xlsx_path)
        return

    jobs = _load_jobs_xlsx(xlsx_path)
    if not jobs:
        logger.info("No jobs found in %s", xlsx_path)
        return

    now = datetime.now(timezone.utc)
    created = 0
    updated = 0
    linked = 0

    for job in jobs:
        title = job["title"]
        description_file = job["description_file"]

        if not title or not description_file:
            logger.warning("Missing title or description file for job: %s", title)
            continue

        description_path = assets_path / description_file
        if not description_path.exists():
            logger.warning("Description file not found: %s", description_path)
            continue

        parsed = _parse_job_text(description_path.read_text(encoding="utf-8"))

        position = (
            db.execute(select(Position).where(func.lower(Position.title) == title.lower()))
            .scalars()
            .first()
        )

        if position:
            _apply_position_updates(position, parsed, now)
            updated += 1
        else:
            position = Position(
                status="open",
                title=title,
                department=None,
                location=parsed.get("location"),
                type=None,
                summary=parsed.get("summary"),
                responsibilities=parsed.get("responsibilities") or [],
                requirements=parsed.get("requirements") or [],
                nice_to_have=parsed.get("nice_to_have") or [],
                created_at=now,
                updated_at=now,
            )
            db.add(position)
            db.flush()
            created += 1

    db.commit()
    logger.info(
        "Seeded positions from assets: created=%s updated=%s candidate_links=%s",
        created,
        updated,
        linked,
    )


def _apply_position_updates(position: Position, parsed: ParsedJob, now: datetime) -> None:
    if position.department and position.department.strip().lower() in {"null", "undefined"}:
        position.department = None
    if parsed["summary"]:
        position.summary = parsed["summary"]
    if parsed["responsibilities"]:
        position.responsibilities = parsed["responsibilities"]
    if parsed["requirements"]:
        position.requirements = parsed["requirements"]
    if parsed["nice_to_have"]:
        position.nice_to_have = parsed["nice_to_have"]
    if parsed["location"]:
        position.location = parsed["location"]
    if not position.status:
        position.status = "open"
    position.updated_at = now


def _load_jobs_xlsx(xlsx_path: Path) -> list[JobRecord]:
    with zipfile.ZipFile(xlsx_path) as workbook:
        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        rows = sheet.findall("s:sheetData/s:row", ns)
        if not rows:
            return []

        headers = _row_to_headers(rows[0], ns)
        if not headers:
            return []

        jobs: list[JobRecord] = []
        for row in rows[1:]:
            values = _row_to_values(row, ns, headers)
            job_number = values.get("Job #", "")
            title = values.get("Job Title", "")
            description_file = values.get("Description File", "")
            if not job_number and not title:
                continue

            jobs.append(
                {
                    "job_number": job_number.strip(),
                    "title": title.strip(),
                    "hiring_manager": values.get("Hiring Manager", "").strip(),
                    "description_file": description_file.strip(),
                }
            )

    return jobs


def _row_to_headers(row: ET.Element, ns: dict[str, str]) -> dict[str, str]:
    cells = {re.sub(r"\d", "", c.get("r", "")): _cell_value(c, ns) for c in row.findall("s:c", ns)}
    return {key: value for key, value in cells.items() if value is not None}


def _row_to_values(row: ET.Element, ns: dict[str, str], headers: dict[str, str]) -> dict[str, str]:
    cells = {re.sub(r"\d", "", c.get("r", "")): _cell_value(c, ns) for c in row.findall("s:c", ns)}
    values: dict[str, str] = {}
    for col, header in headers.items():
        if not header:
            continue
        cell_value = cells.get(col)
        values[header] = cell_value if cell_value is not None else ""
    return values


def _cell_value(cell: ET.Element, ns: dict[str, str]) -> str | None:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        texts = [node.text or "" for node in cell.findall("s:is/s:t", ns)]
        return "".join(texts)

    value = cell.find("s:v", ns)
    if value is None:
        return None
    return value.text


def _parse_job_text(text: str) -> ParsedJob:
    lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
    summary_lines: list[str] = []
    responsibilities: list[str] = []
    requirements: list[str] = []
    nice_to_have: list[str] = []
    location: str | None = None

    current_section: str | None = None
    seen_heading = False

    heading_map = {
        "the role": "responsibilities",
        "role": "responsibilities",
        "the opportunity": "responsibilities",
        "what staff engineer means here": "responsibilities",
        "your impact areas": "responsibilities",
        "what makes this role unique": "responsibilities",
        "key requirements": "requirements",
        "must have": "requirements",
        "must-have": "requirements",
        "what we're looking for": "requirements",
        "what we are looking for": "requirements",
        "technical requirements": "requirements",
        "requirements": "requirements",
        "tech stack": "requirements",
        "our stack": "requirements",
        "nice to have": "nice_to_have",
        "nice-to-have": "nice_to_have",
    }

    ignore_headings = {
        "benefits",
        "compensation",
        "timeline",
        "hiring process",
    }

    for line in lines:
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith(("from:", "to:", "subject:")):
            continue
        location_value = _extract_location(line)
        if location_value:
            location = location_value
            continue

        if lowered in {"hi", "hi there,", "hello", "hello team,", "hi team,", "hi there"}:
            continue

        normalized = (
            line.rstrip(":")
            .lower()
            .replace("\"", "")
            .replace("“", "")
            .replace("”", "")
        )
        if line.endswith(":") and normalized in heading_map:
            current_section = heading_map[normalized]
            seen_heading = True
            continue
        if normalized in heading_map:
            current_section = heading_map[normalized]
            seen_heading = True
            continue
        if line.endswith(":") and normalized in ignore_headings:
            current_section = None
            seen_heading = True
            continue

        is_bullet = line.startswith("-") or line.startswith("*")
        content = line.lstrip("-* ").strip()

        if current_section == "responsibilities":
            responsibilities.extend(_split_list_item(content, is_bullet))
        elif current_section == "requirements":
            requirements.extend(_split_list_item(content, is_bullet))
        elif current_section == "nice_to_have":
            nice_to_have.extend(_split_list_item(content, is_bullet))
        else:
            if not seen_heading:
                summary_lines.append(content)
            if not location:
                location = _infer_location_from_line(lowered)

    summary = " ".join(summary_lines).strip() if summary_lines else None

    return {
        "summary": summary,
        "responsibilities": responsibilities,
        "requirements": requirements,
        "nice_to_have": nice_to_have,
        "location": location,
    }


def _extract_location(line: str) -> str | None:
    match = re.search(r"\bLocation:\s*(.+)", line, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.search(r"\bWork (?:arrangement|setup):\s*(.+)", line, flags=re.IGNORECASE)
    if match:
        inferred = _infer_location_from_line(match.group(1).lower())
        return inferred

    match = re.search(r"\boffice(?:-based)? in ([A-Za-z ]+)", line, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.search(r"\boffice in ([A-Za-z ]+)", line, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.search(r"\bin ([A-Za-z ]+) office", line, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def _infer_location_from_line(line: str) -> str | None:
    cities = [
        "tel aviv",
        "herzliya",
        "jerusalem",
        "haifa",
        "ramat gan",
        "netanya",
        "petah tikva",
        "raanana",
        "hod hasharon",
    ]
    for city in cities:
        if city in line:
            return city.title() if city != "tel aviv" else "Tel Aviv"

    if "remote" in line:
        return "Remote"

    return None


def _split_list_item(content: str, is_bullet: bool) -> list[str]:
    if not content:
        return []
    return [content]
