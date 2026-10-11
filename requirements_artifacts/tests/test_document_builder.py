from requirements_artifacts.artifact_schemas import (
    OpenQuestion,
    Requirement,
    RequirementsOutput,
)
from requirements_artifacts.document_builder import build_documents


def _inputs() -> tuple[dict, RequirementsOutput]:
    state = {
        "project_id": "doc-project",
        "extracted_sections": [],
        "evidence_items": [
            {"id": "EVD-1", "quote": "The clerk reviews the form."},
            {"id": "EVD-UNUSED", "quote": "Unused evidence quote."},
        ],
        "as_is_process": [
            {
                "step_id": "STEP-1",
                "name": "Review form",
                "actor": None,
                "evidence_ids": ["EVD-1"],
            },
            {
                "step_id": "STEP-2",
                "name": "Record decision",
                "actor": "clerk",
                "evidence_ids": ["EVD-1"],
            },
        ],
        "candidate_business_rules": [],
    }
    requirements = RequirementsOutput(
        project_id="doc-project",
        requirements=[
            Requirement(
                id="REQ-1",
                project_id="doc-project",
                req_type="workflow",
                title="Review form",
                statement="The process shall include the step: Review form",
                priority="Should",
                rule_ids=[],
                step_ids=["STEP-1"],
                evidence_ids=["EVD-1"],
            ),
            Requirement(
                id="REQ-2",
                project_id="doc-project",
                req_type="workflow",
                title="Record decision",
                statement="The process shall include the step: Record decision performed by clerk",
                priority="Should",
                rule_ids=[],
                step_ids=["STEP-2"],
                evidence_ids=["EVD-1"],
            ),
        ],
        open_questions=[
            OpenQuestion(
                id="Q-1",
                project_id="doc-project",
                question="Who performs this step: Review form?",
                reason="actor not stated in source",
                related_ids=["STEP-1"],
            )
        ],
        warnings=[],
    )
    return state, requirements


def test_all_documents_have_draft_banner_and_no_approval_claims():
    state, requirements = _inputs()

    documents = build_documents(state, requirements)

    assert all(
        document.startswith("Status: DRAFT. AI-generated, not approved.")
        for document in documents.values()
    )
    for document in documents.values():
        assert "Approved" not in document
        assert "Pending. No approvals recorded." not in document or document == documents["BRD"]


def test_empty_goals_use_exact_clarification_text():
    state, requirements = _inputs()

    document = build_documents(state, requirements)["BRD"]

    assert "## Goals\n\nNot stated in the source documents. Needs clarification." in document


def test_step_without_actor_is_labeled_actor_not_stated():
    state, requirements = _inputs()

    documents = build_documents(state, requirements)

    assert "Review form — actor not stated" in documents["BRD"]
    assert "Review form — actor not stated" in documents["FRD"]


def test_coverage_lists_unused_evidence_item():
    state, requirements = _inputs()

    document = build_documents(state, requirements)["TRACEABILITY"]

    assert "- Evidence items not used by any requirement: EVD-UNUSED" in document


def test_every_requirement_id_appears_in_traceability_table():
    state, requirements = _inputs()

    document = build_documents(state, requirements)["TRACEABILITY"]

    for requirement in requirements.requirements:
        assert f"| {requirement.id} |" in document
