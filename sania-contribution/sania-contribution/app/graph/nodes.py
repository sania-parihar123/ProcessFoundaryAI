"""Minimal LangGraph nodes for the initial ProcessFoundry workflow."""

from datetime import datetime, timezone
from typing import Any, Literal

from app.agents.analysis import analyze_conflicts, analyze_gaps

from .state import LifecycleStatus, ProcessFoundryState, TraceEvent

Route = Literal["finish", "pause_for_human", "blocked"]
RetryDecision = Literal["retry", "fail"]
_RESOLVED_STATUSES = frozenset({"resolved_by_human"})
_TERMINAL_STATUSES = frozenset(
    {LifecycleStatus.COMPLETED, LifecycleStatus.FAILED}
)
_BLOCKING_FIELDS = frozenset(
    {"gap_type", "conflict_type", "severity", "priority", "status"}
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _state_value(state: ProcessFoundryState | dict[str, Any], field: str) -> Any:
    if isinstance(state, ProcessFoundryState):
        return getattr(state, field)
    return state[field]


def _require_lifecycle(
    state: ProcessFoundryState | dict[str, Any],
    *,
    allowed: frozenset[LifecycleStatus],
    node: str,
) -> None:
    current = _state_value(state, "lifecycle_status")
    if current in _TERMINAL_STATUSES:
        raise RuntimeError(
            f"Cannot execute '{node}' for terminal lifecycle status "
            f"{current!r}."
        )
    if current not in allowed:
        allowed_values = ", ".join(status.value for status in allowed)
        raise RuntimeError(
            f"Cannot execute '{node}' from lifecycle status {current!r}; "
            f"expected one of: {allowed_values}."
        )


def _unresolved_issues(
    state: ProcessFoundryState | dict[str, Any],
) -> list[dict[str, Any]]:
    issues = [
        *(_state_value(state, "gap_issues") or []),
        *(_state_value(state, "conflict_issues") or []),
    ]
    return [
        issue
        for issue in issues
        if isinstance(issue, dict)
        and issue.get("status") not in _RESOLVED_STATUSES
    ]


def retry_decision(
    *,
    retry_count: int,
    max_retries: int,
    failure_retryable: bool,
    lifecycle_status: LifecycleStatus,
) -> RetryDecision:
    """Return a retry decision without mutating workflow state.

    ``max_retries`` is supplied explicitly because the state contract does not
    define a default retry limit. Only an explicitly classified retryable
    failure can produce a retry decision.
    """

    if isinstance(max_retries, bool) or not isinstance(max_retries, int):
        raise TypeError("max_retries must be a nonnegative integer.")
    if max_retries < 0:
        raise ValueError("max_retries must be nonnegative.")
    if isinstance(retry_count, bool) or not isinstance(retry_count, int):
        raise TypeError("retry_count must be a nonnegative integer.")
    if retry_count < 0:
        raise ValueError("retry_count must be nonnegative.")
    if not isinstance(failure_retryable, bool):
        raise TypeError("failure_retryable must be an explicit boolean.")
    if lifecycle_status in _TERMINAL_STATUSES:
        return "fail"
    if not failure_retryable or retry_count >= max_retries:
        return "fail"
    return "retry"


def initialize_node(
    state: ProcessFoundryState | dict[str, Any],
) -> dict[str, Any]:
    """Mark a new run as active and route it to gap analysis."""

    _require_lifecycle(
        state,
        allowed=frozenset({LifecycleStatus.CREATED}),
        node="initialize",
    )
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
        "next_action": "analyze_gaps",
        "trace_events": trace_events,
        "updated_at": timestamp,
    }


def analyze_gaps_node(
    state: ProcessFoundryState | dict[str, Any],
) -> dict[str, Any]:
    """Run deterministic gap analysis and record node completion."""

    _require_lifecycle(
        state,
        allowed=frozenset({LifecycleStatus.RUNNING}),
        node="analyze_gaps",
    )
    timestamp = _now()
    update = analyze_gaps(state)
    trace_events = list(_state_value(state, "trace_events"))
    trace_events.append(
        TraceEvent(
            event_type="node_completed",
            timestamp=timestamp,
            node="analyze_gaps",
            message="Gap analysis completed.",
        )
    )
    return {
        **update,
        "current_node": "analyze_gaps",
        "next_action": "analyze_conflicts",
        "trace_events": trace_events,
        "updated_at": timestamp,
    }


def analyze_conflicts_node(
    state: ProcessFoundryState | dict[str, Any],
) -> dict[str, Any]:
    """Run deterministic conflict analysis and record node completion."""

    _require_lifecycle(
        state,
        allowed=frozenset({LifecycleStatus.RUNNING}),
        node="analyze_conflicts",
    )
    timestamp = _now()
    update = analyze_conflicts(state)
    trace_events = list(_state_value(state, "trace_events"))
    trace_events.append(
        TraceEvent(
            event_type="node_completed",
            timestamp=timestamp,
            node="analyze_conflicts",
            message="Conflict analysis completed.",
        )
    )
    return {
        **update,
        "current_node": "analyze_conflicts",
        "next_action": "finish",
        "trace_events": trace_events,
        "updated_at": timestamp,
    }


def route_after_conflicts(
    state: ProcessFoundryState | dict[str, Any],
) -> Route:
    """Choose a route from an explicit ``config.blocking_policy`` only.

    The supported policy shape is::

        {
            "blocking_policy": {
                "route": "pause_for_human" | "blocked",
                "conditions": [
                    {"field": "severity", "values": ["critical"]},
                    {"field": "gap_type", "values": ["missing_step"]},
                ],
            }
        }

    A condition matches an unresolved issue when its field value is one of the
    configured values. Missing fields do not match. With no policy or no
    conditions, the existing finish route is preserved.
    """

    config = _state_value(state, "config")
    policy = config.get("blocking_policy", {}) if isinstance(config, dict) else {}
    if not policy:
        return "finish" if not _unresolved_issues(state) else "pause_for_human"
    if not isinstance(policy, dict):
        raise ValueError("config.blocking_policy must be a mapping.")

    route = policy.get("route")
    if route not in {"pause_for_human", "blocked"}:
        raise ValueError(
            "config.blocking_policy.route must be 'pause_for_human' or 'blocked'."
        )
    conditions = policy.get("conditions", [])
    if not isinstance(conditions, list):
        raise ValueError("config.blocking_policy.conditions must be a list.")

    issues = [
        *(_state_value(state, "gap_issues") or []),
        *(_state_value(state, "conflict_issues") or []),
    ]
    for condition in conditions:
        if not isinstance(condition, dict):
            raise ValueError("Each blocking policy condition must be a mapping.")
        field = condition.get("field")
        values = condition.get("values")
        if field not in _BLOCKING_FIELDS:
            raise ValueError(
                f"Unsupported blocking policy field: {field!r}."
            )
        if not isinstance(values, list):
            raise ValueError("Blocking policy condition values must be a list.")
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            if issue.get("status") in _RESOLVED_STATUSES:
                continue
            if issue.get(field) in values:
                return route
    return "finish" if not _unresolved_issues(state) else "pause_for_human"


def pause_for_human_node(
    state: ProcessFoundryState | dict[str, Any],
) -> dict[str, Any]:
    """Pause at the graph boundary without implementing HITL behavior."""

    _require_lifecycle(
        state,
        allowed=frozenset({LifecycleStatus.RUNNING}),
        node="pause_for_human",
    )
    return _route_boundary_update(
        state,
        lifecycle_status=LifecycleStatus.PAUSED_FOR_HUMAN,
        node="pause_for_human",
        next_action="await_human_review",
        message="Workflow paused for human review.",
    )


def blocked_node(
    state: ProcessFoundryState | dict[str, Any],
) -> dict[str, Any]:
    """Mark a configured blocking route without resolving any issue."""

    _require_lifecycle(
        state,
        allowed=frozenset({LifecycleStatus.RUNNING}),
        node="blocked",
    )
    return _route_boundary_update(
        state,
        lifecycle_status=LifecycleStatus.BLOCKED,
        node="blocked",
        next_action="resolve_blocking_issues",
        message="Workflow blocked by configured issues.",
    )


def _route_boundary_update(
    state: ProcessFoundryState | dict[str, Any],
    *,
    lifecycle_status: LifecycleStatus,
    node: str,
    next_action: str,
    message: str,
) -> dict[str, Any]:
    timestamp = _now()
    trace_events = list(_state_value(state, "trace_events"))
    trace_events.append(
        TraceEvent(
            event_type="route_boundary",
            timestamp=timestamp,
            node=node,
            message=message,
        )
    )
    return {
        "lifecycle_status": lifecycle_status,
        "current_node": node,
        "next_action": next_action,
        "trace_events": trace_events,
        "updated_at": timestamp,
    }


def finish_node(state: ProcessFoundryState | dict[str, Any]) -> dict[str, Any]:
    """Mark the analysis workflow as completed."""

    _require_lifecycle(
        state,
        allowed=frozenset({LifecycleStatus.RUNNING}),
        node="finish",
    )
    if _unresolved_issues(state):
        raise RuntimeError(
            "Cannot complete a workflow with unresolved gap or conflict issues."
        )
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
