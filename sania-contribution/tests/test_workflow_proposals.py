from app.agents.generic_workflow_proposal import build_generic_workflow_proposal
from app.agents.ingestion_service import _proposal_id
from app.graph.state import ProcessFoundryState


def _state(process_type: str = "purchase-approval") -> ProcessFoundryState:
    return ProcessFoundryState(
        run_id="run-1",
        project_id="project-1",
        process_type=process_type,
    )


def _evidence(
    evidence_id: str,
    kind: str,
    quote: str,
    *,
    value: str | None = None,
    refs: list[str] | None = None,
    status: str = "extracted",
) -> dict[str, object]:
    assertion = {"subject": "process", "predicate": kind}
    if value is not None:
        assertion["value"] = value
    return {
        "evidence_id": evidence_id,
        "kind": kind,
        "status": status,
        "quote": quote,
        "assertion": assertion,
        "source_refs": refs or ["document-1"],
        "source_locations": [{"document_id": "document-1", "section": 1}],
    }


def test_generic_proposal_projects_process_evidence_without_scholarship_labels() -> None:
    evidence = [
        _evidence("activity-1", "activity", "Employees submit purchase requests.", value="submit purchase requests."),
        _evidence("activity-2", "activity", "Employees submit purchase requests.", value="submit purchase requests.", refs=["document-2"]),
        _evidence("requirement-1", "requirement", "Requests require department approval."),
        _evidence("condition-1", "condition", "If the amount exceeds the limit, approval is required."),
        _evidence("deadline-1", "deadline", "Finance reviews requests within three business days."),
        _evidence("exception-1", "exception", "Except for emergencies, normal approval applies."),
        _evidence("unknown-1", "statement", "The escalation owner is unclear.", status="unresolved"),
    ]
    state = _state()
    proposal = build_generic_workflow_proposal(
        evidence,
        state,
        proposal_id=_proposal_id(evidence, state),
    )

    assert proposal["status"] == "draft"
    assert len(proposal["steps"]) == 1
    assert proposal["steps"][0]["evidence_refs"] == ["activity-1", "activity-2"]
    assert proposal["steps"][0]["source_refs"] == ["document-1", "document-2"]
    assert proposal["requirements"]
    assert proposal["conditions"]
    assert proposal["deadlines"]
    assert proposal["exceptions"]
    assert proposal["unresolved_questions"]
    assert "scholarship" not in str(proposal).lower()


def test_generic_proposal_does_not_invent_steps_or_approval() -> None:
    evidence = [
        _evidence("statement-1", "statement", "The process is documented here."),
        _evidence("actor-1", "actor", "The service owner is named."),
    ]
    state = _state("facilities-service")
    proposal = build_generic_workflow_proposal(
        evidence,
        state,
        proposal_id=_proposal_id(evidence, state),
    )

    assert proposal["steps"] == []
    assert proposal["status"] == "draft"
    assert proposal["decisions"] == []
    assert proposal["required_inputs"] == []
    assert proposal["produced_outputs"] == []


def test_generic_data_without_direction_is_not_invented_as_input_or_output() -> None:
    evidence = [_evidence("data-1", "data", "The request record is retained.")]
    state = _state("service-request")
    proposal = build_generic_workflow_proposal(
        evidence,
        state,
        proposal_id=_proposal_id(evidence, state),
    )

    assert proposal["required_inputs"] == []
    assert proposal["produced_outputs"] == []
    assert proposal["data_evidence"][0]["evidence_refs"] == ["data-1"]


def test_generic_proposal_id_is_stable_for_duplicate_inputs() -> None:
    evidence = [
        _evidence("activity-1", "activity", "Create the record.", value="create record"),
        _evidence("activity-2", "activity", "Create the record.", value="create record"),
    ]
    first = _proposal_id(evidence, _state("onboarding"))
    second = _proposal_id(list(reversed(evidence)), _state("onboarding"))

    assert first == second
