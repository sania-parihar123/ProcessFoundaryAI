"""Deterministic in-memory demo data for the ProcessFoundry UI."""

from datetime import datetime, timezone

from app.graph.state import LifecycleStatus, ProcessFoundryState, TraceEvent


_DEMO_TIMESTAMP = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


def get_demo_runs() -> list[ProcessFoundryState]:
    """Return the original scholarship compatibility demos."""

    return _scholarship_demo_runs()


def _scholarship_demo_runs() -> list[ProcessFoundryState]:
    """Return explicitly named legacy scholarship fixtures."""

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
        config={
            "data_mode": "demo",
            "demo_label": "Scholarship compatibility (synthetic)",
        },
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
            "demo_label": "Scholarship compatibility (synthetic)",
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


def get_generic_demo_runs() -> list[ProcessFoundryState]:
    """Return synthetic demos for process-neutral UI rendering."""

    purchase = ProcessFoundryState(
        run_id="demo-run-purchase-approval",
        project_id="demo-project-purchase",
        process_type="purchase-approval",
        process_description="Synthetic purchase approval process demonstration.",
        lifecycle_status=LifecycleStatus.PAUSED_FOR_HUMAN,
        current_node="pause_for_human",
        next_action="await_human_review",
        evidence_items=[
            {
                "evidence_id": "demo-purchase-activity",
                "kind": "activity",
                "status": "extracted",
                "quote": "Employees submit purchase requests through the portal.",
                "source_refs": ["demo-purchase-policy"],
                "source_locations": [
                    {
                        "document_id": "demo-purchase-policy",
                        "filename": "purchase-policy.txt",
                        "line_start": 1,
                        "line_end": 1,
                    }
                ],
            },
            {
                "evidence_id": "demo-purchase-conflict-a",
                "kind": "requirement",
                "status": "extracted",
                "quote": "Requests above USD 5,000 require department approval.",
                "source_refs": ["demo-purchase-policy"],
                "source_locations": [
                    {
                        "document_id": "demo-purchase-policy",
                        "filename": "purchase-policy.txt",
                        "line_start": 2,
                        "line_end": 2,
                    }
                ],
                "assertion": {
                    "subject": "purchase.request",
                    "predicate": "approval_threshold",
                    "operator": "equals",
                    "value": 5000,
                    "unit": "USD",
                },
            },
            {
                "evidence_id": "demo-purchase-conflict-b",
                "kind": "requirement",
                "status": "extracted",
                "quote": "Requests above USD 7,000 require department approval.",
                "source_refs": ["demo-purchase-amendment"],
                "source_locations": [
                    {
                        "document_id": "demo-purchase-amendment",
                        "filename": "purchase-amendment.docx",
                        "section": 1,
                    }
                ],
                "assertion": {
                    "subject": "purchase.request",
                    "predicate": "approval_threshold",
                    "operator": "equals",
                    "value": 7000,
                    "unit": "USD",
                },
            },
        ],
        conflict_issues=[
            {
                "conflict_id": "conflict-demo-purchase-threshold",
                "conflict_type": "evidence_vs_evidence",
                "description": "Approval thresholds differ across synthetic sources.",
                "status": "open",
                "evidence_refs": [
                    "demo-purchase-conflict-a",
                    "demo-purchase-conflict-b",
                ],
                "source_refs": [
                    "demo-purchase-policy",
                    "demo-purchase-amendment",
                ],
                "competing_assertions": [
                    {
                        "subject": "purchase.request",
                        "predicate": "approval_threshold",
                        "value": 5000,
                        "unit": "USD",
                        "evidence_id": "demo-purchase-conflict-a",
                    },
                    {
                        "subject": "purchase.request",
                        "predicate": "approval_threshold",
                        "value": 7000,
                        "unit": "USD",
                        "evidence_id": "demo-purchase-conflict-b",
                    },
                ],
            }
        ],
        workflow_proposal={
            "proposal_id": "demo-proposal-purchase",
            "process_type": "purchase-approval",
            "status": "draft",
            "steps": [
                {
                    "step_id": "demo-purchase-activity",
                    "title": "Submit purchase requests",
                    "description": "Employees submit purchase requests through the portal.",
                    "evidence_refs": ["demo-purchase-activity"],
                    "source_refs": ["demo-purchase-policy"],
                }
            ],
            "requirements": [
                {
                    "description": "Requests above USD 5,000 require department approval.",
                    "evidence_refs": ["demo-purchase-conflict-a"],
                    "source_refs": ["demo-purchase-policy"],
                },
                {
                    "description": "Requests above USD 7,000 require department approval.",
                    "evidence_refs": ["demo-purchase-conflict-b"],
                    "source_refs": ["demo-purchase-amendment"],
                },
            ],
            "conflicts": [
                {
                    "conflict_id": "conflict-demo-purchase-threshold",
                    "description": "Approval thresholds differ across synthetic sources.",
                    "evidence_refs": [
                        "demo-purchase-conflict-a",
                        "demo-purchase-conflict-b",
                    ],
                    "source_refs": [
                        "demo-purchase-policy",
                        "demo-purchase-amendment",
                    ],
                }
            ],
            "unresolved_questions": [
                {
                    "issue_id": "conflict-demo-purchase-threshold",
                    "description": "Which threshold is currently in force?",
                    "evidence_refs": [
                        "demo-purchase-conflict-a",
                        "demo-purchase-conflict-b",
                    ],
                    "source_refs": [
                        "demo-purchase-policy",
                        "demo-purchase-amendment",
                    ],
                }
            ],
            "source_refs": [
                "demo-purchase-policy",
                "demo-purchase-amendment",
            ],
            "explanation": "Synthetic evidence is shown for demonstration only; no threshold was selected.",
        },
        config={
            "data_mode": "demo",
            "demo_label": "Purchase approval (synthetic)",
        },
        source_document_ids=[
            "demo-purchase-policy",
            "demo-purchase-amendment",
        ],
        source_index={
            "demo-purchase-policy": {
                "document_id": "demo-purchase-policy",
                "filename": "purchase-policy.txt",
            },
            "demo-purchase-amendment": {
                "document_id": "demo-purchase-amendment",
                "filename": "purchase-amendment.docx",
            },
        },
    )
    onboarding = ProcessFoundryState(
        run_id="demo-run-employee-onboarding",
        project_id="demo-project-onboarding",
        process_type="employee-onboarding",
        process_description="Synthetic employee onboarding process demonstration.",
        lifecycle_status=LifecycleStatus.PAUSED_FOR_HUMAN,
        current_node="pause_for_human",
        next_action="await_human_review",
        gap_issues=[
            {
                "gap_id": "gap-demo-onboarding-equipment",
                "gap_type": "missing_step",
                "description": "The required equipment-issue step is not documented.",
                "status": "open",
                "evidence_refs": [],
                "source_refs": [],
            }
        ],
        evidence_items=[
            {
                "evidence_id": "demo-onboarding-hr",
                "kind": "activity",
                "status": "extracted",
                "quote": "Human Resources creates the employee record.",
                "actors": [{"label": "Human Resources"}],
                "source_refs": ["demo-onboarding-guide"],
                "source_locations": [
                    {
                        "document_id": "demo-onboarding-guide",
                        "filename": "onboarding-guide.docx",
                        "section": 1,
                        "heading": "Employee record",
                    }
                ],
            },
            {
                "evidence_id": "demo-onboarding-it",
                "kind": "responsibility",
                "status": "extracted",
                "quote": "IT provisions access before the start date.",
                "actors": [{"label": "IT"}],
                "source_refs": ["demo-onboarding-guide"],
                "source_locations": [
                    {
                        "document_id": "demo-onboarding-guide",
                        "filename": "onboarding-guide.docx",
                        "section": 2,
                        "heading": "Access",
                    }
                ],
            },
        ],
        workflow_proposal={
            "proposal_id": "demo-proposal-onboarding",
            "process_type": "employee-onboarding",
            "status": "draft",
            "steps": [
                {
                    "step_id": "demo-onboarding-hr",
                    "title": "Create the employee record",
                    "description": "Human Resources creates the employee record.",
                    "actors": [{"label": "Human Resources"}],
                    "evidence_refs": ["demo-onboarding-hr"],
                    "source_refs": ["demo-onboarding-guide"],
                },
                {
                    "step_id": "demo-onboarding-it",
                    "title": "Provision access",
                    "description": "IT provisions access before the start date.",
                    "actors": [{"label": "IT"}],
                    "evidence_refs": ["demo-onboarding-it"],
                    "source_refs": ["demo-onboarding-guide"],
                },
            ],
            "responsibilities": [
                {
                    "description": "IT provisions access before the start date.",
                    "actors": [{"label": "IT"}],
                    "evidence_refs": ["demo-onboarding-it"],
                    "source_refs": ["demo-onboarding-guide"],
                }
            ],
            "unresolved_questions": [
                {
                    "issue_id": "gap-demo-onboarding-equipment",
                    "description": "The required equipment-issue step is not documented.",
                    "evidence_refs": [],
                    "source_refs": [],
                }
            ],
            "source_refs": ["demo-onboarding-guide"],
            "explanation": "Synthetic evidence is shown for demonstration only; the missing step remains unresolved.",
        },
        source_document_ids=["demo-onboarding-guide"],
        source_index={
            "demo-onboarding-guide": {
                "document_id": "demo-onboarding-guide",
                "filename": "onboarding-guide.docx",
            }
        },
        config={
            "data_mode": "demo",
            "demo_label": "Employee onboarding (synthetic)",
            "required_process_steps": ["issue equipment"],
        },
    )
    return [purchase, onboarding]


def get_all_demo_runs() -> list[ProcessFoundryState]:
    """Return compatibility scholarship and generic synthetic fixtures."""

    return [*get_demo_runs(), *get_generic_demo_runs()]


def get_demo_run(run_id: str) -> ProcessFoundryState:
    """Return one demo run by ID or raise ``KeyError`` when it is unknown."""

    for run in get_demo_runs():
        if run.run_id == run_id:
            return run
    raise KeyError(f"Unknown demo run: {run_id}")
