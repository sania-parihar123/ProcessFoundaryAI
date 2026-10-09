from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.graph.state import (
    ApprovalStatus,
    LifecycleStatus,
    ProcessFoundryState,
    TraceEvent,
)


def test_valid_state_creation() -> None:
    state = ProcessFoundryState(
        run_id="run-001",
        project_id="project-001",
        process_type="scholarship",
        process_description="Scholarship application processing",
        source_document_ids=["source-001"],
    )

    assert state.run_id == "run-001"
    assert state.source_document_ids == ["source-001"]
    assert state.approval_status is ApprovalStatus.PENDING
    assert state.lifecycle_status is LifecycleStatus.CREATED


def test_default_values_are_safe_for_a_new_run() -> None:
    state = ProcessFoundryState(
        run_id="run-001",
        project_id="project-001",
        process_type="generic-process",
    )

    assert state.process_description == ""
    assert state.current_node is None
    assert state.next_action == "initialize"
    assert state.retry_count == 0
    assert state.approval_status is ApprovalStatus.PENDING
    assert state.lifecycle_status is LifecycleStatus.CREATED
    assert state.created_at.tzinfo == timezone.utc
    assert state.updated_at.tzinfo == timezone.utc


def test_mutable_defaults_are_independent_between_instances() -> None:
    first = ProcessFoundryState(
        run_id="run-001",
        project_id="project-001",
        process_type="generic-process",
    )
    second = ProcessFoundryState(
        run_id="run-002",
        project_id="project-001",
        process_type="generic-process",
    )

    first.source_document_ids.append("source-001")
    first.trace_events.append(
        TraceEvent(event_type="test", message="First instance event")
    )

    assert second.source_document_ids == []
    assert second.trace_events == []


@pytest.mark.parametrize("field", ["run_id", "project_id", "process_type"])
def test_missing_required_identifiers_are_rejected(field: str) -> None:
    values = {
        "run_id": "run-001",
        "project_id": "project-001",
        "process_type": "generic-process",
    }
    del values[field]

    with pytest.raises(ValidationError):
        ProcessFoundryState(**values)


def test_blank_identifier_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProcessFoundryState(
            run_id=" ",
            project_id="project-001",
            process_type="generic-process",
        )


def test_negative_retry_count_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProcessFoundryState(
            run_id="run-001",
            project_id="project-001",
            process_type="generic-process",
            retry_count=-1,
        )


def test_invalid_status_values_are_rejected() -> None:
    values = {
        "run_id": "run-001",
        "project_id": "project-001",
        "process_type": "generic-process",
    }

    with pytest.raises(ValidationError):
        ProcessFoundryState(**values, lifecycle_status="unknown")

    with pytest.raises(ValidationError):
        ProcessFoundryState(**values, approval_status="auto_approved")
