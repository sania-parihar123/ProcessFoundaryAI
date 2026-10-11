from __future__ import annotations

import re
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from member2.llm_helper import call_llm
from member2.prompts import EVIDENCE_SYSTEM_PROMPT, build_evidence_user_prompt
from member2.schemas import EvidenceRecord


class RawEvidence(BaseModel):
    quote: str
    claim_type: Literal["step", "rule", "actor", "deadline", "form", "other"]
    confidence_label: Literal["high", "medium", "low"]


class RawEvidenceList(BaseModel):
    items: list[RawEvidence]


# These confidence values are placeholders, not real probabilities.
CONFIDENCE_VALUES = {
    "high": Decimal("0.90"),
    "medium": Decimal("0.60"),
    "low": Decimal("0.30"),
}


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", text).casefold()


def extract_evidence(
    section: dict,
    project_id: str,
    counter_start: int = 1,
) -> list[EvidenceRecord]:
    section_text = section["text"]
    if not section_text or not section_text.strip():
        return []

    raw_evidence = call_llm(
        system_prompt=EVIDENCE_SYSTEM_PROMPT,
        user_prompt=build_evidence_user_prompt(section_text),
        response_model=RawEvidenceList,
        source_wrapped=True,
    )
    if raw_evidence is None:
        print(f"Warning: evidence extraction failed for section {section['id']}.")
        return []

    evidence_records: list[EvidenceRecord] = []
    normalized_section = _normalize_for_match(section_text)
    next_id = counter_start

    for item in raw_evidence.items:
        if _normalize_for_match(item.quote) not in normalized_section:
            print(f"Rejected quote not found in section {section['id']}: {item.quote}")
            continue

        # The project is part of the ID because the database uses id as a table-wide primary key.
        evidence_records.append(
            EvidenceRecord(
                id=f"{project_id}-EVD-{next_id:03d}",
                project_id=project_id,
                document_section_id=section["id"],
                quote=item.quote,
                claim_type=item.claim_type,
                confidence=CONFIDENCE_VALUES[item.confidence_label],
            )
        )
        next_id += 1

    return evidence_records
