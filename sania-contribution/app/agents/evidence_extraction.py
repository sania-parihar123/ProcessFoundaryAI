"""Deterministic, provenance-preserving scholarship evidence extraction."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence


_AMOUNT = (
    r"(?:₹|Rs\.?|INR)\s*[\d,]+|"
    r"[\d][\d,]*\s*(?:INR|rupees?)"
)
_INCOME_PATTERN = re.compile(
    rf"\b(?:annual\s+)?(?:family|household)\s+income\b"
    rf".{{0,100}}?(?:must\s+not\s+exceed|shall\s+not\s+exceed|cannot\s+exceed|"
    rf"does\s+not\s+exceed|not\s+more\s+than|no\s+more\s+than|not\s+exceed|"
    rf"less\s+than\s+or\s+equal\s+to|below|under|up\s+to|"
    rf"maximum\s+(?:of|is)?|limit\s+(?:is|of)?)\s*"
    rf"({_AMOUNT})",
    re.IGNORECASE,
)
_ENROLLMENT_PATTERNS = (
    re.compile(
        r"\b(?:applicant|student|candidate)s?\b.{0,80}?"
        r"\bmust\s+be\s+(?:currently\s+)?(?:enrolled|registered)\b"
        r"(?:\s+in|\s+with)?\s*([^.;\n]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\benrollment\s+in\s+([^.;\n]+?)\s+is\s+(?:required|mandatory)\b",
        re.IGNORECASE,
    ),
)
_ACADEMIC_PATTERN = re.compile(
    r"\b(?:academic|academics|marks?|score|performance|grade|percentage)\b"
    r".{0,70}?(?:minimum|at\s+least|not\s+less\s+than|above|of)\s*"
    r"(\d{1,3}(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)
_ACADEMIC_REVERSE_PATTERN = re.compile(
    r"\b(?:minimum|at\s+least|not\s+less\s+than)\s+"
    r"(\d{1,3}(?:\.\d+)?)\s*%\s*"
    r"(?:academic|marks?|score|performance|percentage)\b",
    re.IGNORECASE,
)
_DOCUMENT_PATTERN = re.compile(
    r"\b(?:(?:must|shall|required\s+to)\s+)?"
    r"(?:submit|provide|upload|attach)\s+(?:a|an|the)?\s*"
    r"([^.;\n]*(?:certificate|document|proof|form|letter|statement|transcript)"
    r"[^.;\n]*)",
    re.IGNORECASE,
)
_RESPONSIBILITY_PATTERNS = (
    re.compile(
        r"\b(?:final\s+)?(?:decision|approval)\s+"
        r"(?:will\s+be|is|shall\s+be)\s+(?:made|taken)\s+by\s+([^.;\n]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:requires|subject\s+to)\s+(?:a\s+)?"
        r"(?:human|manual)\s+(?:review|verification)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\breviewed\s+by\s+([^.;\n]+)",
        re.IGNORECASE,
    ),
)
_ATTENDANCE_PATTERNS = (
    re.compile(
    r"\battendance\b.{0,80}?"
    r"(?:(?:at\s+least|minimum(?:\s+of)?|not\s+less\s+than|threshold(?:\s+of)?)\s*)"
    r"(\d{1,3}(?:\.\d+)?)\s*%",
    re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:minimum|at\s+least)\s+attendance(?:\s+of)?\s*"
        r"(\d{1,3}(?:\.\d+)?)\s*%",
        re.IGNORECASE,
    ),
)


def _stable_id(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"evidence-{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _amount_value(value: str) -> int | None:
    digits = re.sub(r"[^\d]", "", value)
    return int(digits) if digits else None


def _sentence(text: str, start: int, end: int) -> str:
    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start)) + 1
    right_candidates = [index for index in (text.find(".", end), text.find("\n", end)) if index >= 0]
    right = min(right_candidates, default=len(text))
    return text[left:right].strip()


def _base_evidence(section: Mapping[str, Any], quote: str, assertion: dict[str, Any]) -> dict[str, Any]:
    document_id = str(section["document_id"])
    location = {
        key: section[key]
        for key in ("page", "section")
        if key in section
    }
    identifier_payload = {
        "document_id": document_id,
        "section_id": section["section_id"],
        "quote": quote,
        "assertion": assertion,
    }
    evidence_id = _stable_id(identifier_payload)
    evidence: dict[str, Any] = {
        "evidence_id": evidence_id,
        "source_id": document_id,
        "source_refs": [document_id],
        "document_id": document_id,
        "filename": section["filename"],
        "section_id": section["section_id"],
        "quote": quote,
        "assertion": assertion,
    }
    evidence.update(location)
    for field in (
        "worksheet_name",
        "row_number",
        "headers",
        "cells",
    ):
        if field in section:
            evidence[field] = section[field]
    if "cells" in section:
        evidence["cell_references"] = [
            cell["coordinate"]
            for cell in section["cells"]
            if isinstance(cell, Mapping) and cell.get("coordinate")
        ]
        spreadsheet_ref = (
            f"{document_id}:{section.get('worksheet_name')}"
            f"!{','.join(evidence['cell_references'])}"
        )
        evidence["source_refs"] = [document_id, spreadsheet_ref]
    return evidence


def extract_evidence(sections: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Extract explicit scholarship requirements and responsibilities."""

    evidence: list[dict[str, Any]] = []
    for section in sections:
        text = str(section.get("text", ""))
        for match in _INCOME_PATTERN.finditer(text):
            value = _amount_value(match.group(1))
            if value is None:
                continue
            evidence.append(
                _base_evidence(
                    section,
                    match.group(0),
                    {
                        "subject": "scholarship.eligibility",
                        "predicate": "family_income_limit",
                        "operator": "equals",
                        "value": value,
                        "unit": "INR",
                        "comparison": "less_than_or_equal",
                    },
                )
            )
        enrollment_matches = []
        for pattern in _ENROLLMENT_PATTERNS:
            enrollment_matches.extend(pattern.finditer(text))
        for match in enrollment_matches:
            value = match.group(1).strip()
            if value:
                evidence.append(
                    _base_evidence(
                        section,
                        match.group(0),
                        {
                            "subject": "scholarship.eligibility",
                            "predicate": "enrollment_requirement",
                            "operator": "requires",
                            "value": value,
                        },
                    )
                )
        academic_matches = [
            *_ACADEMIC_PATTERN.finditer(text),
            *_ACADEMIC_REVERSE_PATTERN.finditer(text),
        ]
        for match in academic_matches:
            value = float(match.group(1))
            assertion: dict[str, Any] = {
                "subject": "scholarship.eligibility",
                "predicate": "academic_threshold",
                "operator": "at_least",
                "value": int(value) if value.is_integer() else value,
                "unit": "percent",
            }
            sentence = _sentence(text, match.start(), match.end())
            if re.search(r"\bexcept\b|\bexemption\b|\bexempt\b", sentence, re.IGNORECASE):
                assertion["exception"] = sentence
            evidence.append(_base_evidence(section, sentence, assertion))
        for match in _DOCUMENT_PATTERN.finditer(text):
            value = match.group(1).strip()
            if value:
                evidence.append(
                    _base_evidence(
                        section,
                        match.group(0),
                        {
                            "subject": "scholarship.application",
                            "predicate": "required_supporting_document",
                            "operator": "requires",
                            "value": value,
                        },
                    )
                )
        for pattern in _RESPONSIBILITY_PATTERNS:
            for match in pattern.finditer(text):
                role = (
                    match.group(1).strip()
                    if match.lastindex
                    else "human reviewer"
                )
                evidence.append(
                    _base_evidence(
                        section,
                        match.group(0),
                        {
                            "subject": "scholarship.decision",
                            "predicate": "human_review_responsibility",
                            "operator": "assigned_to",
                            "value": role,
                        },
                    )
                )
        attendance_matches = []
        for pattern in _ATTENDANCE_PATTERNS:
            attendance_matches.extend(pattern.finditer(text))
        for match in attendance_matches:
            value = float(match.group(1))
            normalized_value: int | float = int(value) if value.is_integer() else value
            evidence.append(
                _base_evidence(
                    section,
                    match.group(0),
                    {
                        "subject": "scholarship.eligibility",
                        "predicate": "attendance_threshold",
                        "operator": "at_least",
                        "value": normalized_value,
                        "unit": "percent",
                    },
                )
            )
    return evidence
