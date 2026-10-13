"""Process-neutral workflow proposal projection from extracted evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _refs(item: Mapping[str, Any]) -> list[str]:
    return [str(ref) for ref in item.get("source_refs", []) if str(ref).strip()]


def _locations(item: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(location)
        for location in item.get("source_locations", [])
        if isinstance(location, Mapping)
    ]


def _evidence_refs(item: Mapping[str, Any]) -> list[str]:
    evidence_id = _text(item.get("evidence_id"))
    return [evidence_id] if evidence_id else []


def _assertion(item: Mapping[str, Any]) -> Mapping[str, Any]:
    value = item.get("assertion")
    return value if isinstance(value, Mapping) else {}


def _actors(item: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(actor)
        for actor in item.get("actors", [])
        if isinstance(actor, Mapping) and _text(actor.get("label"))
    ]


def _merge_refs(target: dict[str, Any], item: Mapping[str, Any]) -> None:
    target["evidence_refs"] = sorted(
        set(target.get("evidence_refs", [])) | set(_evidence_refs(item))
    )
    target["source_refs"] = sorted(
        set(target.get("source_refs", [])) | set(_refs(item))
    )
    locations = target.setdefault("source_locations", [])
    for location in _locations(item):
        if location not in locations:
            locations.append(location)


def _step_for(item: Mapping[str, Any]) -> dict[str, Any]:
    assertion = _assertion(item)
    quote = _text(item.get("quote"))
    value = _text(assertion.get("value"))
    title = value or _text(assertion.get("predicate")) or quote
    step = {
        "step_id": _text(item.get("evidence_id")),
        "title": title,
        "description": quote,
        "actors": _actors(item),
        "evidence_refs": _evidence_refs(item),
        "source_refs": _refs(item),
        "source_locations": _locations(item),
    }
    if assertion.get("predicate"):
        step["predicate"] = assertion["predicate"]
    return step


def _issues(state: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    unresolved: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for issue in [*state.gap_issues, *state.conflict_issues]:
        if not isinstance(issue, Mapping) or issue.get("status") == "resolved_by_human":
            continue
        common = {
            "issue_id": issue.get("gap_id", issue.get("conflict_id")),
            "description": _text(issue.get("description")),
            "evidence_refs": list(issue.get("evidence_refs", [])),
            "source_refs": list(issue.get("source_refs", [])),
        }
        unresolved.append(common)
        if issue.get("conflict_id"):
            conflicts.append(
                {
                    **common,
                    "conflict_id": issue.get("conflict_id"),
                    "competing_assertions": list(
                        issue.get("competing_assertions", [])
                    ),
                }
            )
    return unresolved, conflicts


def build_generic_workflow_proposal(
    evidence_items: Sequence[Mapping[str, Any]],
    state: Any,
    *,
    proposal_id: str,
) -> dict[str, Any]:
    """Build an unapproved proposal without process-specific terminology."""

    steps: list[dict[str, Any]] = []
    step_by_key: dict[str, dict[str, Any]] = {}
    requirements: list[dict[str, Any]] = []
    conditions: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    deadlines: list[dict[str, Any]] = []
    responsibilities: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    data_evidence: list[dict[str, Any]] = []
    related: list[dict[str, Any]] = []
    unresolved_evidence: list[dict[str, Any]] = []
    source_refs: set[str] = set()

    for item in evidence_items:
        kind = _text(item.get("kind")).lower()
        assertion = _assertion(item)
        quote = _text(item.get("quote"))
        refs = _refs(item)
        source_refs.update(refs)
        evidence_refs = _evidence_refs(item)
        if kind == "activity":
            key = _text(assertion.get("value")) or quote.casefold()
            step = step_by_key.get(key)
            if step is None:
                step = _step_for(item)
                step_by_key[key] = step
                steps.append(step)
            else:
                _merge_refs(step, item)
        elif kind == "requirement":
            requirements.append(
                {
                    "description": quote,
                    "assertion": dict(assertion),
                    "evidence_refs": evidence_refs,
                    "source_refs": refs,
                    "source_locations": _locations(item),
                }
            )
        elif kind == "condition":
            conditions.append(
                {
                    "description": quote,
                    "assertion": dict(assertion),
                    "evidence_refs": evidence_refs,
                    "source_refs": refs,
                    "source_locations": _locations(item),
                }
            )
        elif kind == "decision":
            decision = {
                "description": quote,
                "assertion": dict(assertion),
                "evidence_refs": evidence_refs,
                "source_refs": refs,
                "source_locations": _locations(item),
            }
            decisions.append(decision)
        elif kind == "exception":
            exceptions.append(
                {
                    "description": quote,
                    "assertion": dict(assertion),
                    "evidence_refs": evidence_refs,
                    "source_refs": refs,
                    "source_locations": _locations(item),
                }
            )
        elif kind == "deadline":
            deadlines.append(
                {
                    "description": quote,
                    "assertion": dict(assertion),
                    "evidence_refs": evidence_refs,
                    "source_refs": refs,
                    "source_locations": _locations(item),
                }
            )
        elif kind == "responsibility":
            responsibilities.append(
                {
                    "description": quote,
                    "actors": _actors(item),
                    "assertion": dict(assertion),
                    "evidence_refs": evidence_refs,
                    "source_refs": refs,
                    "source_locations": _locations(item),
                }
            )
        elif kind == "data":
            data_item = {
                "description": quote,
                "assertion": dict(assertion),
                "evidence_refs": evidence_refs,
                "source_refs": refs,
                "source_locations": _locations(item),
            }
            operator = _text(assertion.get("operator")).casefold()
            if operator in {"produces", "outputs", "creates"}:
                outputs.append(data_item)
            elif operator in {"requires", "consumes", "uses", "inputs"}:
                inputs.append(data_item)
            else:
                data_evidence.append(data_item)
        elif kind == "relationship":
            related.append(
                {
                    "description": quote,
                    "assertion": dict(assertion),
                    "evidence_refs": evidence_refs,
                    "source_refs": refs,
                    "source_locations": _locations(item),
                }
            )
        if item.get("status") in {"unresolved", "ambiguous"} or item.get("unknowns") or item.get("ambiguity"):
            unresolved_evidence.append(
                {
                    "issue_id": _text(item.get("evidence_id")),
                    "description": quote,
                    "evidence_refs": evidence_refs,
                    "source_refs": refs,
                    "source_locations": _locations(item),
                    "unknowns": list(item.get("unknowns", [])),
                    "ambiguity": item.get("ambiguity"),
                }
            )

    unresolved, conflicts = _issues(state)
    unresolved.extend(unresolved_evidence)
    has_supported_content = any(
        (steps, requirements, conditions, decisions, exceptions, deadlines, responsibilities, inputs, outputs)
    )
    return {
        "proposal_id": proposal_id,
        "project_id": state.project_id,
        "process_type": state.process_type,
        "status": "draft",
        "steps": steps,
        "requirements": requirements,
        "conditions": conditions,
        "decisions": decisions,
        "decision_points": decisions,
        "exceptions": exceptions,
        "deadlines": deadlines,
        "responsibilities": responsibilities,
        "required_inputs": inputs,
        "produced_outputs": outputs,
        "data_evidence": data_evidence,
        "related_evidence": related,
        "unresolved_questions": unresolved,
        "conflicts": conflicts,
        "source_refs": sorted(source_refs),
        "explanation": (
            "Workflow steps are supported by extracted evidence and remain subject to review."
            if has_supported_content
            else "A workflow cannot yet be reliably proposed because no supported process evidence was extracted."
        ),
    }
