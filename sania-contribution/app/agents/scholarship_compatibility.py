"""Compatibility extraction for the original scholarship demonstration."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from app.contracts.evidence import EvidenceItem


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
        r"\brequires|subject\s+to\s+(?:a\s+)?"
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


def _amount_value(value: str) -> int | None:
    digits = re.sub(r"[^\d]", "", value)
    return int(digits) if digits else None


def _sentence(text: str, start: int, end: int) -> str:
    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start)) + 1
    right_candidates = [
        index for index in (text.find(".", end), text.find("\n", end))
        if index >= 0
    ]
    right = min(right_candidates, default=len(text))
    return text[left:right].strip()


def extract_scholarship_evidence(
    sections: Sequence[Mapping[str, Any]],
    *,
    base_evidence: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
    """Map legacy scholarship claims into the shared evidence envelope."""

    evidence: list[dict[str, Any]] = []
    for section in sections:
        text = str(section.get("text", ""))
        for match in _INCOME_PATTERN.finditer(text):
            value = _amount_value(match.group(1))
            if value is not None:
                evidence.append(
                    base_evidence(
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
        enrollment_matches = [
            match
            for pattern in _ENROLLMENT_PATTERNS
            for match in pattern.finditer(text)
        ]
        for match in enrollment_matches:
            value = match.group(1).strip()
            if value:
                evidence.append(
                    base_evidence(
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
            evidence.append(base_evidence(section, sentence, assertion))
        for match in _DOCUMENT_PATTERN.finditer(text):
            value = match.group(1).strip()
            if value:
                evidence.append(
                    base_evidence(
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
                    base_evidence(
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
        attendance_matches = [
            match
            for pattern in _ATTENDANCE_PATTERNS
            for match in pattern.finditer(text)
        ]
        for match in attendance_matches:
            value = float(match.group(1))
            normalized_value: int | float = (
                int(value) if value.is_integer() else value
            )
            evidence.append(
                base_evidence(
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
    for item in evidence:
        predicate = item.get("assertion", {}).get("predicate")
        item["kind"] = (
            "responsibility"
            if predicate == "human_review_responsibility"
            else "requirement"
        )
        item["status"] = "extracted"
        EvidenceItem.model_validate(item)
    return evidence
