from __future__ import annotations

import re
from pathlib import Path

from member2.as_is_node import build_as_is
from member2.doc_parser import ParseError, parse_document
from member2.evidence_node import extract_evidence
from member2.rules_node import extract_rules
from member2.schemas import MemberTwoOutput, SourceSection


def _fallback_document_id(file_path: str) -> str:
    stem = Path(file_path).stem
    safe_id = re.sub(r"[^A-Za-z0-9_-]+", "_", stem)
    safe_id = re.sub(r"_+", "_", safe_id).strip("_")
    return safe_id or "document"


def run_member2_pipeline(
    file_path: str,
    project_id: str,
    document_id: str | None = None,
) -> MemberTwoOutput:
    resolved_document_id = document_id or _fallback_document_id(file_path)
    warnings: list[str] = []

    try:
        parsed_sections = parse_document(file_path, document_id=document_id)
    except ParseError as exc:
        warnings.append(f"Document parsing failed: {exc}")
        return MemberTwoOutput(
            project_id=project_id,
            document_id=resolved_document_id,
            warnings=warnings,
        )

    if parsed_sections:
        resolved_document_id = parsed_sections[0]["document_id"]

    sections = [SourceSection(**section) for section in parsed_sections]
    evidence = []
    evidence_counter = 1
    for section in parsed_sections:
        try:
            section_evidence = extract_evidence(
                section,
                project_id=project_id,
                counter_start=evidence_counter,
            )
        except Exception as exc:
            warnings.append(
                f"Evidence extraction failed for section {section['id']}: {exc}"
            )
            continue

        evidence.extend(section_evidence)
        evidence_counter += len(section_evidence)

    if not evidence:
        warnings.append("Evidence extraction returned no evidence.")

    try:
        steps = build_as_is(evidence, project_id=project_id)
    except Exception as exc:
        warnings.append(f"As-Is step extraction failed: {exc}")
        steps = []
    if not steps:
        warnings.append("As-Is step extraction returned no steps.")

    try:
        rules = extract_rules(evidence, project_id=project_id)
    except Exception as exc:
        warnings.append(f"Rule extraction failed: {exc}")
        rules = []
    if not rules:
        warnings.append("Rule extraction returned no rules.")

    if not parsed_sections:
        warnings.append("Document parsing returned no sections.")

    return MemberTwoOutput(
        project_id=project_id,
        document_id=resolved_document_id,
        sections=sections,
        evidence=evidence,
        steps=steps,
        rules=rules,
        warnings=warnings,
    )
