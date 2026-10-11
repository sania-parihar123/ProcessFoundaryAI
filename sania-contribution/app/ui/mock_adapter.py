"""Deterministic in-memory demo data for the ProcessFoundry UI."""

from datetime import datetime, timezone

from app.graph.state import LifecycleStatus, ProcessFoundryState, TraceEvent


_DEMO_TIMESTAMP = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


def get_demo_runs() -> list[ProcessFoundryState]:
    """Return independent demo runs for the disconnected UI shell."""

    completed = ProcessFoundryState(
        run_id="demo-run-completed",
        project_id="demo-project-clean",
        process_type="scholarship",
        process_description="Completed demonstration run with no detected issues.",
        lifecycle_status=LifecycleStatus.COMPLETED,
        current_node="finish",
        next_action="end",
        approval_status="pending",
        workflow_proposal={
            "proposal_id": "demo-proposal-clean",
            "status": "draft",
            "steps": ["Review application", "Record decision"],
        },
        config={"data_mode": "demo"},
        trace_events=[
            TraceEvent(
                event_type="node_completed",
                timestamp=_DEMO_TIMESTAMP,
                node="initialize",
                message="Workflow initialized.",
            ),
            TraceEvent(
                event_type="node_completed",
                timestamp=_DEMO_TIMESTAMP,
                node="finish",
                message="Workflow finished.",
            ),
        ],
    )
    unresolved = ProcessFoundryState(
        run_id="demo-run-review",
        project_id="demo-project-review",
        process_type="scholarship",
        process_description="Demo run paused with unresolved analysis findings.",
        lifecycle_status=LifecycleStatus.PAUSED_FOR_HUMAN,
        current_node="pause_for_human",
        next_action="await_human_review",
        gap_issues=[
            {
                "gap_id": "gap-demo-attendance",
                "gap_type": "missing_information",
                "description": "Attendance threshold is not supplied.",
                "status": "open",
                "evidence_refs": ["evidence-demo-1"],
                "source_refs": ["source-demo-policy"],
                "rule_refs": ["rule-demo-attendance"],
            }
        ],
        conflict_issues=[
            {
                "conflict_id": "conflict-demo-income",
                "conflict_type": "evidence_vs_evidence",
                "description": "Income limits differ across supplied evidence.",
                "status": "open",
                "evidence_refs": ["evidence-demo-2", "evidence-demo-3"],
                "source_refs": ["source-demo-a", "source-demo-b"],
                "rule_refs": [],
                "competing_assertions": [
                    {
                        "subject": "family_income",
                        "predicate": "annual_limit",
                        "value": "₹2,50,000",
                        "evidence_id": "evidence-demo-2",
                        "source_id": "source-demo-a",
                    },
                    {
                        "subject": "family_income",
                        "predicate": "annual_limit",
                        "value": "₹3,00,000",
                        "evidence_id": "evidence-demo-3",
                        "source_id": "source-demo-b",
                    },
                ],
            }
        ],
        config={
            "data_mode": "demo",
            "required_fields": {"rules": ["attendance_threshold"]},
        },
        candidate_business_rules=[
            {
                "rule_id": "rule-demo-attendance",
                "condition": "eligibility",
                "source_refs": ["source-demo-policy"],
            }
        ],
        evidence_items=[
            {
                "evidence_id": "evidence-demo-2",
                "source_refs": ["source-demo-a"],
                "assertion": {
                    "subject": "family_income",
                    "predicate": "annual_limit",
                    "value": "₹2,50,000",
                },
            },
            {
                "evidence_id": "evidence-demo-3",
                "source_refs": ["source-demo-b"],
                "assertion": {
                    "subject": "family_income",
                    "predicate": "annual_limit",
                    "value": "₹3,00,000",
                },
            },
        ],
        trace_events=[
            TraceEvent(
                event_type="route_boundary",
                timestamp=_DEMO_TIMESTAMP,
                node="pause_for_human",
                message="Workflow paused for human review.",
            )
        ],
    )
    return [completed, unresolved]


def get_demo_run(run_id: str) -> ProcessFoundryState:
    """Return one demo run by ID or raise ``KeyError`` when it is unknown."""

    for run in get_demo_runs():
        if run.run_id == run_id:
            return run
    raise KeyError(f"Unknown demo run: {run_id}")
