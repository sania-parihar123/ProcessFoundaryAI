from datetime import datetime, timezone

import pytest
from langgraph.graph.state import CompiledStateGraph

from app.graph.build_graph import build_graph
from app.graph.nodes import (
    analyze_gaps_node,
    finish_node,
    initialize_node,
    route_after_conflicts,
    retry_decision,
)
from app.graph.state import LifecycleStatus, ProcessFoundryState


def _new_state(**overrides: object) -> ProcessFoundryState:
    values: dict[str, object] = {
        "run_id": "run-001",
        "project_id": "project-001",
        "process_type": "generic-process",
    }
    values.update(overrides)
    return ProcessFoundryState(**values)


def test_build_graph_returns_compiled_graph() -> None:
    graph = build_graph()

    assert isinstance(graph, CompiledStateGraph)


def test_graph_executes_analysis_nodes_in_order() -> None:
    graph = build_graph()

    result = graph.invoke(_new_state())

    assert result["lifecycle_status"] is LifecycleStatus.COMPLETED
    assert result["current_node"] == "finish"
    assert result["next_action"] == "end"
    assert [event.node for event in result["trace_events"]] == [
        "initialize",
        "analyze_gaps",
        "analyze_conflicts",
        "finish",
    ]
    assert all(
        event.timestamp.tzinfo is not None
        and event.timestamp.utcoffset() == timezone.utc.utcoffset(
            datetime.now(timezone.utc)
        )
        for event in result["trace_events"]
    )


def test_graph_stores_gap_and_conflict_analysis_results() -> None:
    state = _new_state()
    state.config = {
        "required_fields": {"rules": ["attendance_threshold"]},
    }
    state.candidate_business_rules = [
        {"rule_id": "attendance-rule", "condition": "eligibility"},
    ]
    state.evidence_items = [
        {
            "evidence_id": "income-a",
            "source_id": "document-a",
            "assertion": {
                "subject": "scholarship.eligibility",
                "predicate": "family_income_limit",
                "operator": "equals",
                "value": 250000,
            },
        },
        {
            "evidence_id": "income-b",
            "source_id": "document-b",
            "assertion": {
                "subject": "scholarship.eligibility",
                "predicate": "family_income_limit",
                "operator": "equals",
                "value": 300000,
            },
        },
    ]

    result = build_graph().invoke(state)

    assert len(result["gap_issues"]) == 1
    assert result["gap_issues"][0]["gap_type"] == "missing_information"
    assert len(result["conflict_issues"]) == 1
    assert result["conflict_issues"][0]["conflict_type"] == "evidence_vs_evidence"


def test_route_without_blocking_policy_preserves_finish_behavior() -> None:
    state = _new_state()

    assert route_after_conflicts(state) == "finish"
    result = build_graph().invoke(state)

    assert result["lifecycle_status"] is LifecycleStatus.COMPLETED
    assert result["gap_issues"] == []
    assert result["conflict_issues"] == []


def test_unresolved_issues_without_blocking_policy_pause_for_human() -> None:
    state = _new_state(
        config={
            "required_fields": {"rules": ["attendance_threshold"]},
        },
        candidate_business_rules=[
            {"rule_id": "attendance-rule", "condition": "eligibility"},
        ],
    )

    result = build_graph().invoke(state)

    assert result["lifecycle_status"] is LifecycleStatus.PAUSED_FOR_HUMAN
    assert result["gap_issues"][0]["gap_type"] == "missing_information"


def test_configured_blocking_gap_pauses_for_human() -> None:
    state = _new_state()
    state.config = {
        "blocking_policy": {
            "route": "pause_for_human",
            "conditions": [
                {"field": "gap_type", "values": ["missing_information"]},
            ],
        },
        "required_fields": {"rules": ["attendance_threshold"]},
    }
    state.candidate_business_rules = [
        {"rule_id": "attendance-rule", "condition": "eligibility"},
    ]

    result = build_graph().invoke(state)

    assert result["lifecycle_status"] is LifecycleStatus.PAUSED_FOR_HUMAN
    assert result["current_node"] == "pause_for_human"
    assert result["gap_issues"][0]["gap_type"] == "missing_information"


def test_configured_blocking_conflict_routes_to_blocked() -> None:
    state = _new_state()
    state.config = {
        "blocking_policy": {
            "route": "blocked",
            "conditions": [
                {"field": "conflict_type", "values": ["evidence_vs_evidence"]},
            ],
        }
    }
    state.evidence_items = [
        {
            "evidence_id": "income-a",
            "assertion": {
                "subject": "eligibility",
                "predicate": "limit",
                "operator": "equals",
                "value": 250000,
            },
        },
        {
            "evidence_id": "income-b",
            "assertion": {
                "subject": "eligibility",
                "predicate": "limit",
                "operator": "equals",
                "value": 300000,
            },
        },
    ]

    result = build_graph().invoke(state)

    assert result["lifecycle_status"] is LifecycleStatus.BLOCKED
    assert result["current_node"] == "blocked"
    assert result["conflict_issues"][0]["evidence_refs"] == ["income-a", "income-b"]


def test_missing_severity_does_not_match_severity_policy() -> None:
    state = _new_state(
        config={
            "blocking_policy": {
                "route": "blocked",
                "conditions": [{"field": "severity", "values": ["critical"]}],
            }
        },
        gap_issues=[{"gap_id": "gap-1", "status": "open"}],
    )

    assert route_after_conflicts(state) == "pause_for_human"


def test_unknown_status_remains_unresolved_for_configured_blocking() -> None:
    state = _new_state(
        config={
            "blocking_policy": {
                "route": "blocked",
                "conditions": [{"field": "severity", "values": ["critical"]}],
            }
        },
        conflict_issues=[
            {
                "conflict_id": "conflict-1",
                "conflict_type": "rule_vs_rule",
                "severity": "critical",
                "status": "unknown",
            }
        ],
    )

    assert route_after_conflicts(state) == "blocked"


def test_resolved_issue_does_not_match_configured_blocking_policy() -> None:
    state = _new_state(
        config={
            "blocking_policy": {
                "route": "blocked",
                "conditions": [{"field": "severity", "values": ["critical"]}],
            }
        },
        gap_issues=[
            {"gap_id": "gap-1", "severity": "critical", "status": "resolved_by_human"}
        ],
    )

    assert route_after_conflicts(state) == "finish"


def test_graph_preserves_existing_state_fields() -> None:
    state = _new_state()
    state.source_document_ids.append("source-001")
    state.input_bundle["request"] = "demo"

    result = build_graph().invoke(state)

    assert result["run_id"] == "run-001"
    assert result["project_id"] == "project-001"
    assert result["source_document_ids"] == ["source-001"]
    assert result["input_bundle"] == {"request": "demo"}


def test_valid_lifecycle_transition_from_created_to_running() -> None:
    state = _new_state()

    update = initialize_node(state)

    assert update["lifecycle_status"] is LifecycleStatus.RUNNING


@pytest.mark.parametrize("terminal_status", [
    LifecycleStatus.COMPLETED,
    LifecycleStatus.FAILED,
])
def test_terminal_state_cannot_be_reexecuted(
    terminal_status: LifecycleStatus,
) -> None:
    state = _new_state(lifecycle_status=terminal_status)

    with pytest.raises(RuntimeError, match="terminal lifecycle status"):
        build_graph().invoke(state)


def test_invalid_transition_to_finish_with_unresolved_issue_is_rejected() -> None:
    state = _new_state(
        lifecycle_status=LifecycleStatus.RUNNING,
        gap_issues=[{"gap_id": "gap-1", "status": "unknown"}],
    )

    with pytest.raises(RuntimeError, match="unresolved"):
        finish_node(state)


def test_analysis_node_rejects_non_running_transition() -> None:
    state = _new_state(lifecycle_status=LifecycleStatus.CREATED)

    with pytest.raises(RuntimeError, match="analyze_gaps"):
        analyze_gaps_node(state)


def test_retry_decision_allows_explicit_retryable_failure() -> None:
    assert retry_decision(
        retry_count=0,
        max_retries=2,
        failure_retryable=True,
        lifecycle_status=LifecycleStatus.RUNNING,
    ) == "retry"


def test_retry_decision_fails_when_limit_is_exhausted() -> None:
    assert retry_decision(
        retry_count=2,
        max_retries=2,
        failure_retryable=True,
        lifecycle_status=LifecycleStatus.RUNNING,
    ) == "fail"


def test_retry_decision_fails_when_zero_retries_are_allowed() -> None:
    assert retry_decision(
        retry_count=0,
        max_retries=0,
        failure_retryable=True,
        lifecycle_status=LifecycleStatus.RUNNING,
    ) == "fail"


def test_retry_decision_rejects_non_retryable_failure() -> None:
    assert retry_decision(
        retry_count=0,
        max_retries=2,
        failure_retryable=False,
        lifecycle_status=LifecycleStatus.RUNNING,
    ) == "fail"


@pytest.mark.parametrize(
    "terminal_status",
    [LifecycleStatus.COMPLETED, LifecycleStatus.FAILED],
)
def test_retry_decision_rejects_terminal_state(
    terminal_status: LifecycleStatus,
) -> None:
    assert retry_decision(
        retry_count=0,
        max_retries=2,
        failure_retryable=True,
        lifecycle_status=terminal_status,
    ) == "fail"


@pytest.mark.parametrize(
    ("max_retries", "expected_exception"),
    [(-1, ValueError), (1.5, TypeError), (True, TypeError)],
)
def test_retry_decision_rejects_invalid_limits(
    max_retries: object,
    expected_exception: type[Exception],
) -> None:
    with pytest.raises(expected_exception, match="max_retries"):
        retry_decision(
            retry_count=0,
            max_retries=max_retries,  # type: ignore[arg-type]
            failure_retryable=True,
            lifecycle_status=LifecycleStatus.RUNNING,
        )
