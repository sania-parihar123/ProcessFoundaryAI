import pytest
from pydantic import ValidationError
import json
from pathlib import Path

from requirements_artifacts.artifact_schemas import Requirement
from requirements_artifacts.requirements_builder import build_requirements


def _state_update() -> dict:
    return {
        "project_id": "test-project",
        "candidate_business_rules": [
            {
                "rule_id": "test-project-BR-001",
                "statement": "Applications must include a signed form.",
                "evidence_ids": ["test-project-EVD-001"],
            }
        ],
        "as_is_process": [
            {
                "step_id": "test-project-STEP-001",
                "name": "Review the application",
                "actor": None,
                "evidence_ids": ["test-project-EVD-002"],
                "unknowns": ["actor not stated in source"],
            }
        ],
        "evidence_items": [
            {"id": "test-project-EVD-001"},
            {"id": "test-project-EVD-002"},
        ],
    }


def test_rule_creates_functional_requirement_with_source_ids():
    output = build_requirements(_state_update())

    requirement = output.requirements[0]
    assert requirement.req_type == "functional"
    assert requirement.rule_ids == ["test-project-BR-001"]
    assert requirement.evidence_ids == ["test-project-EVD-001"]
    assert requirement.statement == (
        "The system shall enforce: Applications must include a signed form."
    )


def test_unknown_step_actor_creates_open_question_and_clarification_status():
    output = build_requirements(_state_update())

    requirement = output.requirements[1]
    assert requirement.status == "needs_clarification"
    assert requirement.statement == (
        "The process shall include the step: Review the application"
    )
    assert output.open_questions[0].question == (
        "Who performs this step: Review the application?"
    )
    assert output.open_questions[0].reason == "actor not stated in source"
    assert output.open_questions[0].related_ids == ["test-project-STEP-001"]


def test_unknown_evidence_id_is_dropped_with_warning():
    state = _state_update()
    state["candidate_business_rules"][0]["evidence_ids"].append("missing-EVD")

    output = build_requirements(state)

    assert output.requirements[0].evidence_ids == ["test-project-EVD-001"]
    assert any("missing-EVD" in warning for warning in output.warnings)


def test_no_requirement_has_approved_status():
    output = build_requirements(_state_update())

    assert all(
        requirement.status != "approved"
        for requirement in output.requirements
    )
    requirement_data = output.requirements[0].model_dump()
    requirement_data["status"] = "approved"
    with pytest.raises(ValidationError):
        Requirement.model_validate(requirement_data)


def test_requirement_ids_are_unique_and_count_up():
    output = build_requirements(_state_update())

    ids = [requirement.id for requirement in output.requirements]
    assert ids == ["test-project-REQ-001", "test-project-REQ-002"]
    assert len(set(ids)) == len(ids)


def test_step_with_known_actor_includes_actor_in_statement():
    state = _state_update()
    state["as_is_process"][0]["actor"] = "reviewer"
    state["as_is_process"][0]["unknowns"] = []

    output = build_requirements(state)

    assert output.requirements[1].statement.endswith(" performed by reviewer")
    assert output.requirements[1].status == "draft"


def test_copied_demo_state_matches_requirement_counts_and_evidence_references():
    state_path = (
        Path(__file__).resolve().parents[1]
        / "samples"
        / "demo_state_update.json"
    )
    state_update = json.loads(state_path.read_text(encoding="utf-8"))

    output = build_requirements(state_update)
    functional_requirements = [
        requirement
        for requirement in output.requirements
        if requirement.req_type == "functional"
    ]
    workflow_requirements = [
        requirement
        for requirement in output.requirements
        if requirement.req_type == "workflow"
    ]
    evidence_ids = {
        evidence["id"] for evidence in state_update["evidence_items"]
    }

    assert len(functional_requirements) == len(
        state_update["candidate_business_rules"]
    )
    assert len(workflow_requirements) == len(state_update["as_is_process"])
    assert all(
        evidence_id in evidence_ids
        for requirement in output.requirements
        for evidence_id in requirement.evidence_ids
    )
    assert all(
        requirement.status != "approved"
        for requirement in output.requirements
    )
