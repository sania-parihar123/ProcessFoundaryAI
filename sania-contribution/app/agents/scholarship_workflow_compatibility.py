"""Legacy scholarship workflow proposal projection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def build_scholarship_workflow_proposal(
    evidence_items: Sequence[Mapping[str, Any]],
    state: Any,
    *,
    proposal_id: str,
) -> dict[str, Any]:
    """Preserve the pre-generic proposal labels for scholarship callers."""

    steps: list[dict[str, Any]] = []
    roles: list[str] = []
    inputs: list[dict[str, Any]] = []
    decision_points: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    source_refs: set[str] = set()

    for item in evidence_items:
        assertion = item.get("assertion", {})
        predicate = assertion.get("predicate")
        refs = list(item.get("source_refs", []))
        evidence_id = item["evidence_id"]
        quote = str(item.get("quote", "")).strip()
        source_refs.update(refs)
        if predicate == "enrollment_requirement":
            steps.append({
                "step": "Verify the applicant's enrollment.",
                "description": f"Confirm that the applicant meets the stated enrollment requirement: {quote}",
                "supported_by": [evidence_id],
                "source_refs": refs,
                "source_locations": list(item.get("source_locations", [])),
                "requirement": assertion.get("value"),
            })
        elif predicate == "academic_threshold":
            description = f"Check the academic threshold stated in the source: {quote}"
            decision_points.append({
                "check": "Academic eligibility",
                "description": description,
                "evidence_refs": [evidence_id],
                "source_refs": refs,
                "source_locations": list(item.get("source_locations", [])),
            })
            steps.append({
                "step": "Check academic eligibility.",
                "description": description,
                "supported_by": [evidence_id],
                "source_refs": refs,
                "source_locations": list(item.get("source_locations", [])),
            })
        elif predicate == "family_income_limit":
            description = f"Check the family or household income limit stated in the source: {quote}"
            decision_points.append({
                "check": "Family or household income eligibility",
                "description": description,
                "claim": str(assertion.get("value", "")),
                "evidence_refs": [evidence_id],
                "source_refs": refs,
                "source_locations": list(item.get("source_locations", [])),
            })
            steps.append({
                "step": "Check family or household income eligibility.",
                "description": description,
                "supported_by": [evidence_id],
                "source_refs": refs,
                "source_locations": list(item.get("source_locations", [])),
            })
        elif predicate == "required_supporting_document":
            inputs.append({
                "document": assertion.get("value"),
                "description": f"Verify the required document: {quote}",
                "evidence_refs": [evidence_id],
                "source_refs": refs,
            })
            steps.append({
                "step": "Collect and verify supporting documents.",
                "description": f"Verify the required document: {quote}",
                "supported_by": [evidence_id],
                "source_refs": refs,
            })
        elif predicate == "human_review_responsibility":
            role = str(assertion.get("value", "")).strip()
            if role and role not in roles:
                roles.append(role)
            steps.append({
                "step": "Conduct human review or final decision.",
                "description": f"Follow the responsibility stated in the source: {quote}",
                "supported_by": [evidence_id],
                "source_refs": refs,
                "source_locations": list(item.get("source_locations", [])),
                "responsible_role": role,
            })
        if assertion.get("exception"):
            exceptions.append({
                "description": assertion["exception"],
                "evidence_refs": [evidence_id],
                "source_refs": refs,
                "source_locations": list(item.get("source_locations", [])),
            })

    unresolved_questions = [
        {
            "issue_id": issue.get("gap_id", issue.get("conflict_id")),
            "description": issue.get("description", ""),
            "evidence_refs": list(issue.get("evidence_refs", [])),
            "source_refs": list(issue.get("source_refs", [])),
        }
        for issue in [*state.gap_issues, *state.conflict_issues]
        if isinstance(issue, Mapping) and issue.get("status") != "resolved_by_human"
    ]
    conflicts = [
        {
            "conflict_id": issue.get("conflict_id"),
            "description": issue.get("description", ""),
            "competing_assertions": issue.get("competing_assertions", []),
            "evidence_refs": issue.get("evidence_refs", []),
            "source_refs": issue.get("source_refs", []),
        }
        for issue in state.conflict_issues
        if isinstance(issue, Mapping) and issue.get("status") != "resolved_by_human"
    ]
    return {
        "proposal_id": proposal_id,
        "project_id": state.project_id,
        "process_type": state.process_type,
        "status": "draft",
        "steps": steps,
        "requirements": [
            {
                "description": str(item.get("quote", "")).strip(),
                "evidence_refs": [item["evidence_id"]],
                "source_refs": list(item.get("source_refs", [])),
                "source_locations": list(item.get("source_locations", [])),
            }
            for item in evidence_items
        ],
        "roles": roles,
        "required_inputs": inputs,
        "decision_points": decision_points,
        "exceptions": exceptions,
        "unresolved_questions": unresolved_questions,
        "conflicts": conflicts,
        "source_refs": sorted(source_refs),
        "explanation": (
            "Workflow steps are supported by extracted evidence and remain subject to review."
            if steps or decision_points or inputs
            else "A workflow cannot yet be reliably proposed because no supported process requirements were extracted."
        ),
    }
