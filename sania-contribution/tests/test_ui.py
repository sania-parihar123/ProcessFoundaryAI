from app.graph.state import ProcessFoundryState
from app.ui.mock_adapter import (
    get_all_demo_runs,
    get_demo_run,
    get_demo_runs,
    get_generic_demo_runs,
)
from app.ui.streamlit_app import _format_locations
from app.ui.view_models import ingestion_view_model, workflow_view_model


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


def test_generic_demos_are_named_synthetic_and_preserve_provenance() -> None:
    runs = get_generic_demo_runs()

    assert [run.process_type for run in runs] == [
        "purchase-approval",
        "employee-onboarding",
    ]
    assert all(run.config["data_mode"] == "demo" for run in runs)
    assert all("synthetic" in run.config["demo_label"].lower() for run in runs)
    assert all(run.workflow_proposal["status"] == "draft" for run in runs)
    purchase = workflow_view_model(runs[0])
    assert purchase["evidence_items"][0]["source_refs"] == [
        "demo-purchase-policy"
    ]
    assert purchase["conflict_issues"][0]["status"] == "open"
    assert purchase["proposal_label"] == "Unapproved proposal"


def test_all_demo_runs_keep_legacy_scholarship_fixtures() -> None:
    assert [run.run_id for run in get_all_demo_runs()[:2]] == [
        "demo-run-completed",
        "demo-run-review",
    ]
    assert get_demo_runs()[1].process_type == "scholarship"


def test_provenance_formatter_shows_available_locations_only() -> None:
    formatted = _format_locations(
        [
            {
                "filename": "policy.pdf",
                "page": 3,
                "line_start": 4,
                "line_end": 6,
                "worksheet_name": "Requests",
                "cell_coordinates": ["B4", "C4"],
            }
        ]
    )

    assert "page=3" in formatted
    assert "line_start=4" in formatted
    assert "worksheet_name=Requests" in formatted
    assert "cells=B4,C4" in formatted
    assert "paragraph=" not in formatted


def test_uploaded_view_model_does_not_add_demo_content() -> None:
    class Result:
        message = "Uploaded"
        documents = [{"document_id": "uploaded-1"}]
        sections = []
        evidence_items = [
            {
                "evidence_id": "uploaded-evidence-1",
                "kind": "activity",
                "quote": "Requests are submitted.",
                "source_refs": ["uploaded-1"],
            }
        ]
        errors = []

    view = ingestion_view_model(Result())

    assert view["documents"] == [{"document_id": "uploaded-1"}]
    assert view["evidence_items"][0]["evidence_id"] == "uploaded-evidence-1"
    assert "demo-purchase-policy" not in str(view)
