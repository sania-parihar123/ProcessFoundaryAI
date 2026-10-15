from io import BytesIO

from app.agents.ingestion_service import ingest_documents
from app.agents.generic_workflow_proposal import build_generic_workflow_proposal
from app.agents.ingestion_service import _proposal_id
from app.graph.build_graph import build_graph
from app.graph.state import LifecycleStatus
from app.graph.state import ProcessFoundryState


class Upload(BytesIO):
    def __init__(self, name: str, content: bytes):
        super().__init__(content)
        self.name = name


def test_purchase_approval_configured_gap_reaches_analysis_and_proposal() -> None:
    config = {
        "required_fields": {"evidence": ["normalized_interpretation"]},
        "vocabulary": {"activity_verbs": ["submit", "review"]},
    }
    result = ingest_documents(
        [
            Upload(
                "purchase-a.txt",
                b"Requests above USD 5000 require department approval.",
            ),
            Upload(
                "purchase-b.txt",
                b"Requests above USD 7000 require department approval.",
            ),
        ],
        project_id="purchase-project",
        process_type="purchase-approval",
        config=config,
    )

    assert result.state is not None
    state = result.state
    assert state.process_type == "purchase-approval"
    assert state.config == config
    assert len(state.extracted_sections) == 2
    assert set(state.source_index) == set(state.source_document_ids)
    assert all(item["source_locations"] for item in state.evidence_items)
    assert state.gap_issues
    assert all(issue["evidence_refs"] for issue in state.gap_issues)
    assert state.conflict_issues == []
    assert state.lifecycle_status is LifecycleStatus.PAUSED_FOR_HUMAN
    assert state.current_node == "pause_for_human"
    assert state.approval_status.value == "pending"
    proposal = state.workflow_proposal
    assert proposal["status"] == "draft"
    assert "authoritative" not in proposal


def test_facilities_conflict_reaches_graph_and_remains_in_draft_proposal() -> None:
    evidence = [
        {
            "evidence_id": "service-a",
            "kind": "requirement",
            "quote": "Safety requests require response within 2 hours.",
            "assertion": {
                "subject": "service.request",
                "predicate": "response_limit",
                "operator": "equals",
                "value": "2 hours",
            },
            "source_id": "facilities-a",
            "source_refs": ["facilities-a"],
            "source_locations": [
                {"document_id": "facilities-a", "section": 1}
            ],
        },
        {
            "evidence_id": "service-b",
            "kind": "requirement",
            "quote": "Safety requests require response within 4 hours.",
            "assertion": {
                "subject": "service.request",
                "predicate": "response_limit",
                "operator": "equals",
                "value": "4 hours",
            },
            "source_id": "facilities-b",
            "source_refs": ["facilities-b"],
            "source_locations": [
                {"document_id": "facilities-b", "section": 1}
            ],
        },
    ]
    state = ProcessFoundryState(
        run_id="facilities-run",
        project_id="facilities-project",
        process_type="facilities-service",
        evidence_items=evidence,
        source_document_ids=["facilities-a", "facilities-b"],
        source_index={
            "facilities-a": {"document_id": "facilities-a"},
            "facilities-b": {"document_id": "facilities-b"},
        },
    )

    result = build_graph().invoke(state)
    graph_state = ProcessFoundryState.model_validate(result)
    proposal = build_generic_workflow_proposal(
        graph_state.evidence_items,
        graph_state,
        proposal_id=_proposal_id(graph_state.evidence_items, graph_state),
    )

    assert graph_state.lifecycle_status is LifecycleStatus.PAUSED_FOR_HUMAN
    assert len(graph_state.conflict_issues) == 1
    conflict = graph_state.conflict_issues[0]
    assert conflict["status"] == "open"
    assert conflict["evidence_refs"] == ["service-a", "service-b"]
    assert conflict["source_refs"] == ["facilities-a", "facilities-b"]
    assert proposal["status"] == "draft"
    assert proposal["conflicts"][0]["conflict_id"] == conflict["conflict_id"]
    assert proposal["unresolved_questions"]
    assert "authoritative" not in proposal


def test_employee_onboarding_configured_missing_step_remains_unresolved() -> None:
    config = {
        "required_process_steps": ["issue equipment"],
        "vocabulary": {
            "activity_verbs": ["create", "provision"],
            "actor_labels": ["Human Resources", "IT"],
        },
    }
    result = ingest_documents(
        [
            Upload(
                "onboarding.txt",
                (
                    b"Human Resources creates the employee record. "
                    b"IT provisions access."
                ),
            )
        ],
        project_id="onboarding-project",
        process_type="employee-onboarding",
        config=config,
    )

    assert result.state is not None
    state = result.state
    assert state.lifecycle_status is LifecycleStatus.PAUSED_FOR_HUMAN
    assert state.current_node == "pause_for_human"
    assert len(state.gap_issues) == 1
    gap = state.gap_issues[0]
    assert gap["gap_type"] == "missing_step"
    assert gap["affected_subject"] == "issue equipment"
    assert gap["status"] == "open"
    assert gap["evidence_refs"] == []
    assert gap["source_refs"] == []
    assert state.workflow_proposal["status"] == "draft"
    assert state.workflow_proposal["steps"]
    assert state.workflow_proposal["unresolved_questions"][0]["issue_id"] == gap["gap_id"]


def test_generic_issue_ids_and_provenance_are_stable_across_identical_runs() -> None:
    uploads = [
        Upload("request.txt", b"Requests require review."),
    ]
    first = ingest_documents(
        uploads,
        project_id="stable-project",
        process_type="service-request",
        config={"required_fields": {"evidence": ["confidence"]}},
    )
    second = ingest_documents(
        [Upload("request.txt", b"Requests require review.")],
        project_id="stable-project",
        process_type="service-request",
        config={"required_fields": {"evidence": ["confidence"]}},
    )

    assert first.state is not None
    assert second.state is not None
    assert first.documents == second.documents
    assert first.evidence_items == second.evidence_items
    assert first.state.gap_issues == second.state.gap_issues
    assert first.state.workflow_proposal["proposal_id"] == second.state.workflow_proposal["proposal_id"]
    assert first.state.workflow_proposal["status"] == "draft"
