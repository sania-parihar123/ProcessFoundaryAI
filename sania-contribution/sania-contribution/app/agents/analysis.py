"""Deterministic gap and conflict analysis over provisional input records.

The Member 2 boundary fields are still provisional, so this module accepts
mapping records and uses only explicitly supplied fields and configuration.
It never selects an authoritative claim or infers missing business policy.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from app.graph.state import ProcessFoundryState


Record = Mapping[str, Any]
Configuration = Mapping[str, Any]

_DETECTOR_VERSION = "analysis-v1"
_MISSING = object()


def _value(record: Record, *names: str, default: Any = _MISSING) -> Any:
    for name in names:
        if name in record:
            return record[name]
    if default is _MISSING:
        return None
    return default


def _text(value: Any) -> str:
    return str(value).strip().casefold() if value is not None else ""


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, set):
        canonical_items = [_canonical(item) for item in value]
        return sorted(
            canonical_items,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ),
        )
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _canonical(payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _refs(record: Record, field: str) -> list[str]:
    value = record.get(field, [])
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        elif isinstance(item, Mapping):
            identifier = _value(item, "evidence_id", "rule_id", "source_id", "id")
            if identifier is not None and str(identifier).strip():
                result.append(str(identifier).strip())
    return sorted(set(result))


def _issue_metadata(
    configuration: Configuration,
    issue_type: str,
) -> dict[str, Any]:
    severity = configuration.get("severity")
    if isinstance(severity, Mapping):
        severity = severity.get(issue_type)
    metadata: dict[str, Any] = {
        "status": "open",
        "detector_version": _DETECTOR_VERSION,
    }
    if severity is not None:
        metadata["severity"] = str(severity)
    priority = configuration.get("priority")
    if isinstance(priority, Mapping):
        priority = priority.get(issue_type)
    if priority is not None:
        metadata["priority"] = priority
    return metadata


def _make_gap(
    *,
    process_type: str,
    gap_type: str,
    subject: str,
    description: str,
    configuration: Configuration,
    evidence_refs: Sequence[str] = (),
    source_refs: Sequence[str] = (),
    rule_refs: Sequence[str] = (),
    step_refs: Sequence[str] = (),
) -> dict[str, Any]:
    refs = {
        "evidence_refs": sorted(set(evidence_refs)),
        "source_refs": sorted(set(source_refs)),
        "rule_refs": sorted(set(rule_refs)),
        "step_refs": sorted(set(step_refs)),
    }
    identifier_payload = {
        "process_type": process_type,
        "gap_type": gap_type,
        "subject": _text(subject),
        "references": refs,
        "detector_version": _DETECTOR_VERSION,
    }
    issue = {
        "gap_id": _stable_id("gap", identifier_payload),
        "gap_type": gap_type,
        "description": description,
        "affected_subject": subject,
        **refs,
        **_issue_metadata(configuration, gap_type),
    }
    if configuration.get("suggest_questions") is True:
        issue["suggested_question"] = f"Please clarify {subject}."
    return issue


def _configured_required_fields(
    configuration: Configuration,
    record_kind: str,
) -> list[str]:
    fields = configuration.get("required_fields", {})
    if not isinstance(fields, Mapping):
        return []
    selected = fields.get(record_kind, [])
    if isinstance(selected, str):
        return [selected]
    if isinstance(selected, Sequence):
        return [str(field) for field in selected]
    return []


def detect_gaps(
    *,
    process_type: str,
    evidence_items: Sequence[Record] = (),
    as_is_process: Sequence[Record] = (),
    candidate_business_rules: Sequence[Record] = (),
    configuration: Configuration | None = None,
) -> list[dict[str, Any]]:
    """Return deterministic gaps supported by records or explicit config."""

    config = configuration or {}
    gaps: list[dict[str, Any]] = []

    for kind, records, identifier in (
        ("evidence", evidence_items, "evidence_id"),
        ("process", as_is_process, "step_id"),
        ("rules", candidate_business_rules, "rule_id"),
    ):
        for record in records:
            missing = [
                field
                for field in _configured_required_fields(config, kind)
                if record.get(field) is None
                or (isinstance(record.get(field), str) and not record[field].strip())
                or (isinstance(record.get(field), (list, dict)) and not record[field])
            ]
            for field in missing:
                record_id = str(record.get(identifier, "unknown"))
                gaps.append(
                    _make_gap(
                        process_type=process_type,
                        gap_type="missing_information",
                        subject=f"{kind}.{record_id}.{field}",
                        description=f"Required {kind} field '{field}' is missing.",
                        configuration=config,
                        evidence_refs=(
                            ([record_id] if kind == "evidence" else [])
                            + _refs(record, "evidence_refs")
                        ),
                        source_refs=_refs(record, "source_refs"),
                        rule_refs=[record_id] if kind == "rules" else (),
                        step_refs=[record_id] if kind == "process" else (),
                    )
                )

    required_steps = config.get("required_process_steps", [])
    observed_step_names = {
        _text(_value(step, "step_id", "name", "key"))
        for step in as_is_process
        if isinstance(step, Mapping)
    }
    if isinstance(required_steps, Sequence) and not isinstance(
        required_steps, (str, bytes, bytearray)
    ):
        for required in required_steps:
            required_name = (
                _value(required, "step_id", "name", "key")
                if isinstance(required, Mapping)
                else required
            )
            if required_name is None or _text(required_name) in observed_step_names:
                continue
            gaps.append(
                _make_gap(
                    process_type=process_type,
                    gap_type="missing_step",
                    subject=str(required_name),
                    description=f"Required process step '{required_name}' is missing.",
                    configuration=config,
                )
            )

    if config.get("require_confidence") is True:
        for record in [*evidence_items, *candidate_business_rules]:
            if record.get("confidence") is None:
                record_id = str(
                    _value(record, "evidence_id", "rule_id", default="unknown")
                )
                gaps.append(
                    _make_gap(
                        process_type=process_type,
                        gap_type="missing_information",
                        subject=f"confidence.{record_id}",
                        description=f"Confidence is required for record '{record_id}'.",
                        configuration=config,
                        evidence_refs=(
                            (
                                [record_id]
                                if record.get("evidence_id") is not None
                                else []
                            )
                            + _refs(record, "evidence_refs")
                        ),
                        source_refs=_refs(record, "source_refs"),
                        rule_refs=[record_id]
                        if record.get("rule_id") is not None
                        else (),
                    )
                )

    for kind, records, identifier in (
        ("evidence", evidence_items, "evidence_id"),
        ("process", as_is_process, "step_id"),
        ("rules", candidate_business_rules, "rule_id"),
    ):
        for record in records:
            if record.get("ambiguous") is True or (
                isinstance(record.get("alternatives"), Sequence)
                and len(record["alternatives"]) > 1
            ):
                record_id = str(record.get(identifier, "unknown"))
                gaps.append(
                    _make_gap(
                        process_type=process_type,
                        gap_type="ambiguous_information",
                        subject=f"{kind}.{record_id}",
                        description=f"Record '{record_id}' contains unresolved alternatives.",
                        configuration=config,
                        evidence_refs=(
                            ([record_id] if kind == "evidence" else [])
                            + _refs(record, "evidence_refs")
                        ),
                        source_refs=_refs(record, "source_refs"),
                        rule_refs=[record_id] if kind == "rules" else (),
                        step_refs=[record_id] if kind == "process" else (),
                    )
                )

    if not evidence_items and config.get("require_evidence") is True:
        gaps.append(
            _make_gap(
                process_type=process_type,
                gap_type="data_availability",
                subject="evidence",
                description="Required evidence is unavailable.",
                configuration=config,
            )
        )
    if not as_is_process and config.get("require_process") is True:
        gaps.append(
            _make_gap(
                process_type=process_type,
                gap_type="data_availability",
                subject="as_is_process",
                description="Required As-Is process information is unavailable.",
                configuration=config,
            )
        )
    if not candidate_business_rules and config.get("require_rules") is True:
        gaps.append(
            _make_gap(
                process_type=process_type,
                gap_type="data_availability",
                subject="candidate_business_rules",
                description="Required business rules are unavailable.",
                configuration=config,
            )
        )

    return sorted(gaps, key=lambda issue: issue["gap_id"])


def _assertion(record: Record) -> Record | None:
    assertion = record.get("assertion")
    if isinstance(assertion, Mapping):
        return assertion
    if all(key in record for key in ("subject", "predicate", "value")):
        return record
    return None


def _assertion_key(assertion: Record) -> tuple[str, str]:
    return (
        _text(_value(assertion, "subject", "field")),
        _text(_value(assertion, "predicate", "attribute")),
    )


def _claims_conflict(left: Record, right: Record) -> bool:
    if _assertion_key(left) != _assertion_key(right):
        return False
    left_scope = _canonical(left.get("scope"))
    right_scope = _canonical(right.get("scope"))
    if (left_scope is None) != (right_scope is None):
        return False
    if left_scope is not None and right_scope is not None and left_scope != right_scope:
        return False
    left_context = _canonical(left.get("effective_context"))
    right_context = _canonical(right.get("effective_context"))
    if (left_context is None) != (right_context is None):
        return False
    if (
        left_context is not None
        and right_context is not None
        and left_context != right_context
    ):
        return False
    left_operator = _text(left.get("operator", "equals"))
    right_operator = _text(right.get("operator", "equals"))
    left_value = _canonical(left.get("value"))
    right_value = _canonical(right.get("value"))
    return left_value != right_value and left_operator == right_operator == "equals"


def _make_conflict(
    *,
    process_type: str,
    conflict_type: str,
    left_record: Record,
    right_record: Record,
    left_assertion: Record,
    right_assertion: Record,
    configuration: Configuration,
) -> dict[str, Any]:
    evidence_refs = sorted(
        set(_refs(left_record, "evidence_refs"))
        | set(_refs(right_record, "evidence_refs"))
        | {
            str(identifier)
            for identifier in (
                left_record.get("evidence_id"),
                right_record.get("evidence_id"),
            )
            if identifier is not None
        }
    )
    rule_refs = sorted(
        set(_refs(left_record, "rule_refs"))
        | set(_refs(right_record, "rule_refs"))
        | {
            str(identifier)
            for identifier in (left_record.get("rule_id"), right_record.get("rule_id"))
            if identifier is not None
        }
    )
    source_refs = sorted(
        set(_refs(left_record, "source_refs"))
        | set(_refs(right_record, "source_refs"))
        | {
            str(identifier)
            for identifier in (left_record.get("source_id"), right_record.get("source_id"))
            if identifier is not None
        }
    )
    assertions = [_canonical(left_assertion), _canonical(right_assertion)]
    payload = {
        "process_type": process_type,
        "conflict_type": conflict_type,
        "assertions": sorted(
            assertions,
            key=lambda assertion: json.dumps(assertion, sort_keys=True),
        ),
        "evidence_refs": evidence_refs,
        "rule_refs": rule_refs,
        "source_refs": source_refs,
        "detector_version": _DETECTOR_VERSION,
    }
    subject = _value(left_assertion, "subject", "field", default="claim")
    description = (
        f"Conflicting claims for '{subject}': "
        f"{left_assertion.get('value')!r} versus {right_assertion.get('value')!r}."
    )
    return {
        "conflict_id": _stable_id("conflict", payload),
        "conflict_type": conflict_type,
        "description": description,
        "evidence_refs": evidence_refs,
        "rule_refs": rule_refs,
        "source_refs": source_refs,
        "competing_assertions": assertions,
        **_issue_metadata(configuration, conflict_type),
    }


def detect_conflicts(
    *,
    process_type: str,
    evidence_items: Sequence[Record] = (),
    candidate_business_rules: Sequence[Record] = (),
    configuration: Configuration | None = None,
) -> list[dict[str, Any]]:
    """Return deterministic conflicts without selecting an authoritative claim."""

    config = configuration or {}
    conflicts: list[dict[str, Any]] = []

    def compare(
        left_items: Sequence[Record],
        right_items: Sequence[Record],
        conflict_type: str,
        same_collection: bool = False,
    ) -> None:
        for left_index, left_record in enumerate(left_items):
            left_assertion = _assertion(left_record)
            if left_assertion is None:
                continue
            right_start = left_index + 1 if same_collection else 0
            for right_record in right_items[right_start:]:
                right_assertion = _assertion(right_record)
                if right_assertion is None or not _claims_conflict(
                    left_assertion, right_assertion
                ):
                    continue
                conflicts.append(
                    _make_conflict(
                        process_type=process_type,
                        conflict_type=conflict_type,
                        left_record=left_record,
                        right_record=right_record,
                        left_assertion=left_assertion,
                        right_assertion=right_assertion,
                        configuration=config,
                    )
                )

    compare(evidence_items, evidence_items, "evidence_vs_evidence", True)
    compare(
        candidate_business_rules,
        candidate_business_rules,
        "rule_vs_rule",
        True,
    )
    compare(candidate_business_rules, evidence_items, "rule_vs_evidence")
    return sorted(
        {issue["conflict_id"]: issue for issue in conflicts}.values(),
        key=lambda issue: issue["conflict_id"],
    )


def _state_value(state: ProcessFoundryState | Mapping[str, Any], field: str) -> Any:
    return getattr(state, field) if isinstance(state, ProcessFoundryState) else state[field]


def analyze_gaps(
    state: ProcessFoundryState | Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Analyze state inputs and return an update for ``gap_issues``."""

    return {
        "gap_issues": detect_gaps(
            process_type=_state_value(state, "process_type"),
            evidence_items=_state_value(state, "evidence_items"),
            as_is_process=_state_value(state, "as_is_process"),
            candidate_business_rules=_state_value(state, "candidate_business_rules"),
            configuration=_state_value(state, "config"),
        )
    }


def analyze_conflicts(
    state: ProcessFoundryState | Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Analyze state inputs and return an update for ``conflict_issues``."""

    return {
        "conflict_issues": detect_conflicts(
            process_type=_state_value(state, "process_type"),
            evidence_items=_state_value(state, "evidence_items"),
            candidate_business_rules=_state_value(state, "candidate_business_rules"),
            configuration=_state_value(state, "config"),
        )
    }
