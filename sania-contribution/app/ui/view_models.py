"""UI-safe projections of ProcessFoundry workflow state."""

from typing import Any

from app.graph.state import ApprovalStatus, ProcessFoundryState, TraceEvent


def _references(issue: dict[str, Any], field: str) -> list[str]:
    value = issue.get(field, [])
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _issue_view(issue: object) -> dict[str, Any]:
    if not isinstance(issue, dict):
        return {
            "issue_id": None,
            "description": str(issue),
            "status": "unknown",
            "evidence_refs": [],
            "source_refs": [],
            "rule_refs": [],
            "claims": [],
        }
    issue_id = issue.get("gap_id", issue.get("conflict_id"))
    competing_assertions = issue.get("competing_assertions", [])
    claims = (
        [dict(assertion) for assertion in competing_assertions]
        if isinstance(competing_assertions, list)
        and all(isinstance(assertion, dict) for assertion in competing_assertions)
        else []
    )
    return {
        "issue_id": issue_id,
        "issue_type": issue.get("gap_type", issue.get("conflict_type")),
        "description": issue.get("description", ""),
        "severity": issue.get("severity"),
        "priority": issue.get("priority"),
        "status": issue.get("status", "unknown"),
        "evidence_refs": _references(issue, "evidence_refs"),
        "source_refs": _references(issue, "source_refs"),
        "rule_refs": _references(issue, "rule_refs"),
        "claims": claims,
    }


def _trace_view(event: object) -> dict[str, Any]:
    if isinstance(event, TraceEvent):
        return {
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "node": event.node,
            "message": event.message,
        }
    if isinstance(event, dict):
        return {
            "event_type": event.get("event_type"),
            "timestamp": event.get("timestamp"),
            "node": event.get("node"),
            "message": event.get("message", ""),
        }
    return {
        "event_type": None,
        "timestamp": None,
        "node": None,
        "message": str(event),
    }


def workflow_view_model(state: ProcessFoundryState) -> dict[str, Any]:
    """Project workflow state into values safe for rendering."""

    approval_status = state.approval_status.value
    proposal = dict(state.workflow_proposal)
    proposal_status = proposal.get("status")
    proposal_is_approved = (
        approval_status == ApprovalStatus.APPROVED.value
        or proposal_status == ApprovalStatus.APPROVED.value
    )
    return {
        "project_id": state.project_id,
        "run_id": state.run_id,
        "process_type": state.process_type,
        "lifecycle_status": state.lifecycle_status.value,
        "current_node": state.current_node,
        "next_action": state.next_action,
        "human_review_required": (
            state.lifecycle_status.value == "paused_for_human"
            or state.next_action == "await_human_review"
        ),
        "issues_unresolved": any(
            issue.get("status", "unknown") not in {"resolved", "closed"}
            for issue in [*state.gap_issues, *state.conflict_issues]
            if isinstance(issue, dict)
        ),
        "retry_count": state.retry_count,
        "last_error": dict(state.last_error),
        "gap_issues": [_issue_view(issue) for issue in state.gap_issues],
        "conflict_issues": [
            _issue_view(issue) for issue in state.conflict_issues
        ],
        "trace_events": [_trace_view(event) for event in state.trace_events],
        "workflow_proposal": proposal,
        "proposal_label": (
            "Approved" if proposal_is_approved else "Unapproved proposal"
        ),
        "is_demo": state.config.get("data_mode") == "demo",
    }


def ingestion_view_model(result: Any) -> dict[str, Any]:
    """Project an ingestion result into values suitable for the upload page."""

    return {
        "message": result.message,
        "documents": [dict(document) for document in result.documents],
        "sections": [dict(section) for section in result.sections],
        "evidence_items": [dict(item) for item in result.evidence_items],
        "errors": [
            {
                "filename": error.filename,
                "code": error.code,
                "message": error.message,
            }
            for error in result.errors
        ],
    }
