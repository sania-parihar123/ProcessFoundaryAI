"""Deterministic evidence extraction with generic and legacy strategies."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from app.contracts.evidence import EvidenceItem, SourceLocator
from app.agents.scholarship_compatibility import extract_scholarship_evidence


def _stable_id(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"evidence-{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _base_evidence(
    section: Mapping[str, Any],
    quote: str,
    assertion: dict[str, Any] | None = None,
    *,
    kind: str = "statement",
    status: str = "extracted",
) -> dict[str, Any]:
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
    }
    if assertion is not None:
        identifier_payload["assertion"] = assertion
    else:
        identifier_payload.update({"kind": kind, "status": status})
    evidence_id = _stable_id(identifier_payload)
    evidence: dict[str, Any] = {
        "evidence_id": evidence_id,
        "source_id": document_id,
        "source_refs": [document_id],
        "document_id": document_id,
        "filename": section["filename"],
        "section_id": section["section_id"],
        "quote": quote,
        "kind": kind,
        "status": status,
    }
    if assertion is not None:
        evidence["assertion"] = assertion
    source_locator = section.get("source_locator")
    if isinstance(source_locator, Mapping):
        locator = SourceLocator.model_validate(source_locator)
        quote_start = str(section.get("text", "")).find(quote)
        if quote_start >= 0:
            quote_end = quote_start + len(quote)
            locator_update: dict[str, Any] = {
                "char_start": quote_start,
                "char_end": quote_end,
            }
            if locator.line_start is not None:
                source_text = str(section.get("text", ""))
                locator_update.update(
                    {
                        "line_start": source_text.count("\n", 0, quote_start) + 1,
                        "line_end": source_text.count("\n", 0, quote_end) + 1,
                    }
                )
            locator = locator.model_copy(
                update=locator_update
            )
            evidence["quote_char_start"] = quote_start
            evidence["quote_char_end"] = quote_end
        evidence["source_locations"] = [
            locator.model_dump(exclude_none=True, exclude_defaults=True)
        ]
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


def _extract_scholarship_evidence(
    sections: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Delegate legacy parsing without exposing it to generic extraction."""

    return extract_scholarship_evidence(
        sections,
        base_evidence=_base_evidence,
    )


_GENERIC_MARKERS = {
    "requirement": (
        "must",
        "shall",
        "required",
        "require",
        "requires",
        "need to",
        "needs to",
    ),
    "decision": ("decide", "decision", "approve", "approval", "reject"),
    "exception": ("except", "unless", "otherwise"),
    "condition": ("if ", "when ", "provided that", "only when"),
}
_DEADLINE_PATTERN = re.compile(
    r"\b(?:within|by|before)\s+[^.;,\n]+",
    re.IGNORECASE,
)
_ACTOR_BY_PATTERN = re.compile(r"\bby\s+([^.;,\n]+)", re.IGNORECASE)


def _sentences(text: str) -> list[tuple[str, int, int]]:
    result: list[tuple[str, int, int]] = []
    for match in re.finditer(r"[^.!?\n]+(?:[.!?]|$)", text):
        raw = match.group(0)
        quote = raw.strip()
        if not quote:
            continue
        start = match.start() + len(raw) - len(raw.lstrip())
        end = start + len(quote)
        result.append((quote, start, end))
    return result


def _configured_terms(
    configuration: Mapping[str, Any],
    vocabulary: Mapping[str, Any] | None,
    key: str,
) -> tuple[str, ...]:
    values: Any = None
    if vocabulary is not None:
        values = vocabulary.get(key)
    if values is None:
        values = configuration.get(key)
    if isinstance(values, str):
        return (values,)
    if isinstance(values, Sequence) and not isinstance(values, (bytes, bytearray)):
        return tuple(str(value) for value in values if str(value).strip())
    return ()


def _contains_marker(text: str, markers: Sequence[str]) -> bool:
    folded = text.casefold()
    return any(marker.casefold() in folded for marker in markers)


def _generic_kind(
    quote: str,
    configuration: Mapping[str, Any],
    vocabulary: Mapping[str, Any] | None,
) -> str:
    configured_kinds: Any = None
    if vocabulary is not None:
        configured_kinds = vocabulary.get("kind_markers")
    if configured_kinds is None:
        configured_kinds = configuration.get("kind_markers")
    if isinstance(configured_kinds, Mapping):
        for configured_kind, markers in configured_kinds.items():
            if (
                configured_kind in {
                    "activity",
                    "actor",
                    "requirement",
                    "condition",
                    "decision",
                    "exception",
                    "deadline",
                    "responsibility",
                    "data",
                    "relationship",
                    "unknown",
                    "statement",
                }
                and isinstance(markers, Sequence)
                and _contains_marker(quote, [str(marker) for marker in markers])
            ):
                return str(configured_kind)
    exception_markers = _configured_terms(
        configuration, vocabulary, "exception_markers"
    ) or _GENERIC_MARKERS["exception"]
    if _contains_marker(quote, exception_markers):
        return "exception"
    if _DEADLINE_PATTERN.search(quote):
        return "deadline"
    condition_markers = _configured_terms(
        configuration, vocabulary, "condition_markers"
    ) or _GENERIC_MARKERS["condition"]
    if _contains_marker(quote, condition_markers):
        return "condition"
    requirement_markers = _configured_terms(
        configuration, vocabulary, "requirement_markers"
    ) or _GENERIC_MARKERS["requirement"]
    if _contains_marker(quote, requirement_markers):
        return "requirement"
    decision_markers = _configured_terms(
        configuration, vocabulary, "decision_markers"
    ) or _GENERIC_MARKERS["decision"]
    if _contains_marker(quote, decision_markers):
        return "decision"
    activity_verbs = _configured_terms(configuration, vocabulary, "activity_verbs")
    if any(
        re.search(rf"\b{re.escape(verb)}(?:s|es|ed|ing)?\b", quote, re.IGNORECASE)
        for verb in activity_verbs
    ):
        return "activity"
    return "statement"


def _generic_assertion(
    kind: str,
    quote: str,
    configuration: Mapping[str, Any],
    vocabulary: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if kind == "deadline":
        deadline = _DEADLINE_PATTERN.search(quote)
        if deadline:
            return {
                "subject": "process",
                "predicate": "deadline",
                "operator": "within",
                "value": deadline.group(0),
            }
    if kind == "requirement":
        return {
            "subject": "process",
            "predicate": "requirement",
            "operator": "requires",
            "value": quote,
        }
    if kind == "decision":
        return {
            "subject": "process",
            "predicate": "decision",
            "operator": "requires",
            "value": quote,
        }
    if kind == "condition":
        return {
            "subject": "process",
            "predicate": "condition",
            "operator": "applies_when",
            "value": quote,
        }
    if kind == "exception":
        return {
            "subject": "process",
            "predicate": "exception",
            "operator": "alternate_path",
            "value": quote,
        }
    activity_verbs = _configured_terms(configuration, vocabulary, "activity_verbs")
    if activity_verbs and any(
        re.search(rf"\b{re.escape(verb)}(?:s|es|ed|ing)?\b", quote, re.IGNORECASE)
        for verb in activity_verbs
    ):
        return {
            "subject": "process",
            "predicate": "activity",
            "operator": "performs",
            "value": quote,
        }
    return None


def _generic_actors(
    quote: str,
    configuration: Mapping[str, Any],
    vocabulary: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    actors = _configured_terms(configuration, vocabulary, "actor_labels")
    found = [
        {"label": actor}
        for actor in actors
        if re.search(rf"\b{re.escape(actor)}\b", quote, re.IGNORECASE)
    ]
    if found:
        return found
    by_actor = _ACTOR_BY_PATTERN.search(quote)
    if by_actor and configuration.get("allow_unconfigured_actor_mentions") is True:
        return [{"label": by_actor.group(1).strip()}]
    return []


def _generic_unknowns(quote: str) -> list[dict[str, str]]:
    if re.search(r"\b(?:unknown|unclear|not specified|may vary|depends)\b", quote, re.IGNORECASE):
        return [
            {
                "field": "interpretation",
                "question": "What interpretation applies to this statement?",
                "reason": "The source text is explicitly uncertain.",
            }
        ]
    return []


def _extract_generic_evidence(
    sections: Sequence[Mapping[str, Any]],
    *,
    configuration: Mapping[str, Any],
    vocabulary: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for section in sections:
        text = str(section.get("text", ""))
        for quote, start, end in _sentences(text):
            kind = _generic_kind(quote, configuration, vocabulary)
            assertion = _generic_assertion(kind, quote, configuration, vocabulary)
            item = _base_evidence(section, quote, assertion, kind=kind)
            item["quote_char_start"] = start
            item["quote_char_end"] = end
            source_locations = item.get("source_locations")
            if isinstance(source_locations, list) and source_locations:
                source_locations[0]["char_start"] = start
                source_locations[0]["char_end"] = end
                if "line_start" in source_locations[0]:
                    source_locations[0]["line_start"] = text.count("\n", 0, start) + 1
                    source_locations[0]["line_end"] = text.count("\n", 0, end) + 1
            actors = _generic_actors(quote, configuration, vocabulary)
            if actors:
                item["actors"] = actors
            unknowns = _generic_unknowns(quote)
            if unknowns:
                item["status"] = "unresolved"
                item["unknowns"] = unknowns
            EvidenceItem.model_validate(item)
            evidence.append(item)
    return evidence


def extract_evidence(
    sections: Sequence[Mapping[str, Any]],
    *,
    config: Mapping[str, Any] | None = None,
    process_description: str | None = None,
    vocabulary: Mapping[str, Any] | None = None,
    required_evidence: Sequence[Any] | None = None,
    expected_process_steps: Sequence[Any] | None = None,
    strategy: str | None = None,
) -> list[dict[str, Any]]:
    """Extract evidence through a configurable, process-neutral boundary.

    Calls without a strategy use generic extraction. The scholarship adapter
    remains available through an explicit ``strategy="scholarship_compat"``
    selection.
    Configuration and process descriptions guide extraction only; they are
    never emitted as source-backed evidence.
    """

    configuration = dict(config or {})
    selected_strategy = strategy or configuration.get("extraction_strategy")
    if selected_strategy is None:
        selected_strategy = "generic"
    if selected_strategy in {"scholarship", "scholarship_compat"}:
        return _extract_scholarship_evidence(sections)
    if selected_strategy != "generic":
        raise ValueError(
            "Unsupported evidence extraction strategy. "
            "Use 'generic' or 'scholarship_compat'."
        )
    if process_description:
        configuration = {**configuration, "process_description": process_description}
    if required_evidence is not None:
        configuration = {**configuration, "required_evidence": list(required_evidence)}
    if expected_process_steps is not None:
        configuration = {
            **configuration,
            "expected_process_steps": list(expected_process_steps),
        }
    return _extract_generic_evidence(
        sections,
        configuration=configuration,
        vocabulary=vocabulary,
    )
