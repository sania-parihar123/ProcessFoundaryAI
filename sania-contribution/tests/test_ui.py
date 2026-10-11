from app.graph.state import ProcessFoundryState
from app.ui.mock_adapter import get_demo_run, get_demo_runs
from app.ui.view_models import workflow_view_model


def test_demo_adapter_returns_completed_and_unresolved_runs() -> None:
    runs = get_demo_runs()

    assert [run.run_id for run in runs] == [
        "demo-run-completed",
        "demo-run-review",
    ]
    assert runs[0].gap_issues == []
    assert runs[0].conflict_issues == []
    assert runs[1].gap_issues
    assert runs[1].conflict_issues
    assert runs[0].config["data_mode"] == "demo"
    assert runs[1].config["data_mode"] == "demo"
    assert runs[1].config["required_fields"]["rules"] == ["attendance_threshold"]
    assert get_demo_run("demo-run-review").run_id == "demo-run-review"


def test_view_model_preserves_issue_ids_and_references() -> None:
    view = workflow_view_model(get_demo_run("demo-run-review"))

    gap = view["gap_issues"][0]
    conflict = view["conflict_issues"][0]
    assert gap["issue_id"] == "gap-demo-attendance"
    assert gap["evidence_refs"] == ["evidence-demo-1"]
    assert gap["source_refs"] == ["source-demo-policy"]
    assert gap["rule_refs"] == ["rule-demo-attendance"]
    assert conflict["issue_id"] == "conflict-demo-income"
    assert conflict["evidence_refs"] == ["evidence-demo-2", "evidence-demo-3"]
    assert conflict["source_refs"] == ["source-demo-a", "source-demo-b"]
    assert [claim["value"] for claim in conflict["claims"]] == [
        "₹2,50,000",
        "₹3,00,000",
    ]
    assert [claim["source_id"] for claim in conflict["claims"]] == [
        "source-demo-a",
        "source-demo-b",
    ]
    assert view["human_review_required"] is True
    assert view["issues_unresolved"] is True
    assert view["proposal_label"] == "Unapproved proposal"
    assert [event["event_type"] for event in view["trace_events"]] == [
        "route_boundary"
    ]


def test_view_model_handles_empty_optional_values() -> None:
    state = ProcessFoundryState(
        run_id="run-empty",
        project_id="project-empty",
        process_type="generic-process",
    )

    view = workflow_view_model(state)

    assert view["current_node"] is None
    assert view["gap_issues"] == []
    assert view["conflict_issues"] == []
    assert view["trace_events"] == []
    assert view["last_error"] == {}
    assert view["workflow_proposal"] == {}


def test_proposal_is_not_labeled_approved_without_explicit_approval() -> None:
    state = ProcessFoundryState(
        run_id="run-draft",
        project_id="project-draft",
        process_type="generic-process",
        workflow_proposal={"status": "draft", "steps": ["Review"]},
    )

    view = workflow_view_model(state)

    assert view["proposal_label"] == "Unapproved proposal"
    assert view["is_demo"] is False


def test_explicit_approval_is_reflected_without_approving_in_ui() -> None:
    state = ProcessFoundryState(
        run_id="run-approved",
        project_id="project-approved",
        process_type="generic-process",
        approval_status="approved",
        workflow_proposal={"status": "draft"},
    )

    assert workflow_view_model(state)["proposal_label"] == "Approved"
