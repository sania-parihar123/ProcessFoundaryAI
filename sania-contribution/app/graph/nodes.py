"""Minimal LangGraph nodes for the initial ProcessFoundry workflow."""

from datetime import datetime, timezone
from typing import Any

from .state import LifecycleStatus, ProcessFoundryState, TraceEvent


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _state_value(state: ProcessFoundryState | dict[str, Any], field: str) -> Any:
    if isinstance(state, ProcessFoundryState):
        return getattr(state, field)
    return state[field]


def initialize_node(
    state: ProcessFoundryState | dict[str, Any],
) -> dict[str, Any]:
    """Mark a new run as active and route it to the finish node."""

    timestamp = _now()
    trace_events = list(_state_value(state, "trace_events"))
    trace_events.append(
        TraceEvent(
            event_type="node_completed",
            timestamp=timestamp,
            node="initialize",
            message="Workflow initialized.",
        )
    )
    return {
        "lifecycle_status": LifecycleStatus.RUNNING,
        "current_node": "initialize",
        "next_action": "finish",
        "trace_events": trace_events,
        "updated_at": timestamp,
    }


def finish_node(state: ProcessFoundryState | dict[str, Any]) -> dict[str, Any]:
    """Mark the minimal workflow as completed."""

    timestamp = _now()
    trace_events = list(_state_value(state, "trace_events"))
    trace_events.append(
        TraceEvent(
            event_type="node_completed",
            timestamp=timestamp,
            node="finish",
            message="Workflow finished.",
        )
    )
    return {
        "lifecycle_status": LifecycleStatus.COMPLETED,
        "current_node": "finish",
        "next_action": "end",
        "trace_events": trace_events,
        "updated_at": timestamp,
    }
