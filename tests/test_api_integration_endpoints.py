"""Integration tests for the FastAPI project endpoints."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from processfoundry_ai.api.routes import documents as documents_module
from processfoundry_ai.database.base import Base
from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.session import dispose_engine, get_engine
from processfoundry_ai.main import app


@pytest.fixture
def api_client(monkeypatch, tmp_path):
    """Create a temporary SQLite-backed app client for endpoint integration tests."""
    dispose_engine()
    config = DatabaseConfig(dsn="sqlite:///:memory:")
    engine = get_engine(config)
    Base.metadata.create_all(engine)

    monkeypatch.setattr(DatabaseConfig, "from_env", staticmethod(lambda: config))
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(documents_module, "UPLOAD_DIR", upload_dir)

    with TestClient(app) as client:
        yield client

    Base.metadata.drop_all(engine)
    dispose_engine()


def create_project(client, *, name="Alpha Project", process_type="finance", description="Sample process", status="draft"):
    response = client.post(
        "/api/projects",
        json={
            "name": name,
            "process_type": process_type,
            "description": description,
            "status": status,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_document(client, project_id, *, filename="sample.pdf", content=b"%PDF-1.4\n" + b"test"):
    response = client.post(
        f"/api/projects/{project_id}/documents",
        files={"file": (filename, content, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_document_section(client, project_id, document_id, *, text="Section text", page_number=1, title="Overview"):
    response = client.post(
        f"/api/projects/{project_id}/documents/{document_id}/sections",
        json={
            "page_number": page_number,
            "section_title": title,
            "text": text,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_evidence_item(client, project_id, section_id, *, quote="A requirement requires 120 credits.", claim_type="requirement", confidence=0.94):
    response = client.post(
        f"/api/projects/{project_id}/evidence-items",
        json={
            "document_section_id": section_id,
            "quote": quote,
            "claim_type": claim_type,
            "confidence": confidence,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_process_version(client, project_id, *, version="v1", status="draft"):
    response = client.post(
        f"/api/projects/{project_id}/process-versions",
        json={
            "version": version,
            "as_is_json": {"steps": ["capture"]},
            "to_be_json": {"steps": ["capture", "validate"]},
            "status": status,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_process_step(client, project_id, process_version_id, *, name="Capture request", step_key="capture"):
    response = client.post(
        f"/api/projects/{project_id}/process-versions/{process_version_id}/steps",
        json={
            "step_key": step_key,
            "name": name,
            "actor": "analyst",
            "step_type": "processing",
            "sequence": 1,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_business_rule(client, project_id, *, rule_key="BR-01"):
    response = client.post(
        f"/api/projects/{project_id}/business-rules",
        json={
            "rule_key": rule_key,
            "description": "All applications require an intake review.",
            "condition_json": {"requires_review": True},
            "status": "draft",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_clarification_item(client, project_id, *, question="What evidence confirms the rule?", reason="Need basis"):
    response = client.post(
        f"/api/projects/{project_id}/clarification-items",
        json={
            "question": question,
            "reason": reason,
            "status": "open",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_requirement(client, project_id, *, requirement_key="REQ-01", requirement_type="functional", statement="System must retain audit logs."):
    response = client.post(
        f"/api/projects/{project_id}/requirements",
        json={
            "requirement_key": requirement_key,
            "type": requirement_type,
            "statement": statement,
            "priority": "high",
            "status": "draft",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_artifact(client, project_id, *, artifact_type="process_diagram", version="1.0"):
    response = client.post(
        f"/api/projects/{project_id}/artifacts",
        json={
            "artifact_type": artifact_type,
            "version": version,
            "content_json": {"nodes": 2},
            "markdown": "# Diagram",
            "status": "draft",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_approval(client, project_id, *, target_type="requirement", target_id=None, decision="approved"):
    response = client.post(
        f"/api/projects/{project_id}/approvals",
        json={
            "target_type": target_type,
            "target_id": target_id,
            "decision": decision,
            "reviewer": "ops-reviewer",
            "comment": "Looks good.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_agent_run(client, project_id, *, node_name="intake-node", status="completed"):
    response = client.post(
        f"/api/projects/{project_id}/agent-runs",
        json={
            "node_name": node_name,
            "status": status,
            "input_summary": "intake form analyzed",
            "output_ref": "artifact://intake",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_test_case(client, project_id, requirement_id, *, test_key="TC-01"):
    response = client.post(
        f"/api/projects/{project_id}/test-cases",
        json={
            "test_key": test_key,
            "requirement_id": requirement_id,
            "scenario": "Verify the user receives the acknowledgement email.",
            "expected_result": "Email is sent with the correct content.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_projects_endpoints(api_client):
    client = api_client
    project = create_project(client)

    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/projects/{project['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == project["id"]

    patch_response = client.patch(
        f"/api/projects/{project['id']}",
        json={"status": "active", "description": "Updated description"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "active"

    delete_response = client.delete(f"/api/projects/{project['id']}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/projects/{project['id']}")
    assert missing_response.status_code == 404

    invalid_response = client.post(
        "/api/projects",
        json={
            "name": "   ",
            "process_type": "finance",
            "description": "Bad project",
        },
    )
    assert invalid_response.status_code == 422


def test_documents_endpoint_group(api_client):
    client = api_client
    project = create_project(client)

    document = create_document(client, project["id"], filename="sample.pdf")
    assert document["filename"] == "sample.pdf"

    documents_response = client.get(f"/api/projects/{project['id']}/documents")
    assert documents_response.status_code == 200
    assert len(documents_response.json()) == 1

    bad_type_response = client.post(
        f"/api/projects/{project['id']}/documents",
        files={"file": ("bad.txt", b"not-a-pdf", "text/plain")},
    )
    assert bad_type_response.status_code == 415

    missing_project_response = client.get("/api/projects/missing/documents")
    assert missing_project_response.status_code == 404


def test_document_sections_endpoint_group(api_client):
    client = api_client
    project = create_project(client)
    document = create_document(client, project["id"])

    section = create_document_section(client, project["id"], document["id"], text="Requirements section")

    list_response = client.get(f"/api/projects/{project['id']}/documents/{document['id']}/sections")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/projects/{project['id']}/documents/{document['id']}/sections/{section['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["text"] == "Requirements section"

    patch_response = client.patch(
        f"/api/projects/{project['id']}/documents/{document['id']}/sections/{section['id']}",
        json={
            "page_number": 2,
            "section_title": "Updated section",
            "text": "Updated section text",
        },
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["section_title"] == "Updated section"

    delete_response = client.delete(f"/api/projects/{project['id']}/documents/{document['id']}/sections/{section['id']}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/projects/{project['id']}/documents/{document['id']}/sections/{section['id']}")
    assert missing_response.status_code == 404


def test_evidence_items_endpoint_group(api_client):
    client = api_client
    project = create_project(client)
    document = create_document(client, project["id"])
    section = create_document_section(client, project["id"], document["id"])

    evidence = create_evidence_item(client, project["id"], section["id"], claim_type="credit requirement")

    list_response = client.get(f"/api/projects/{project['id']}/evidence-items")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/projects/{project['id']}/evidence-items/{evidence['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["claim_type"] == "credit requirement"

    patch_response = client.patch(
        f"/api/projects/{project['id']}/evidence-items/{evidence['id']}",
        json={
            "document_section_id": section["id"],
            "quote": "Updated quote",
            "claim_type": "updated claim",
            "confidence": 0.88,
        },
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["quote"] == "Updated quote"

    delete_response = client.delete(f"/api/projects/{project['id']}/evidence-items/{evidence['id']}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/projects/{project['id']}/evidence-items/{evidence['id']}")
    assert missing_response.status_code == 404

    invalid_foreign_key = client.post(
        f"/api/projects/{project['id']}/evidence-items",
        json={
            "document_section_id": "missing-section",
            "quote": "broken evidence",
            "claim_type": "unsupported",
            "confidence": 0.5,
        },
    )
    assert invalid_foreign_key.status_code == 404


def test_process_versions_and_steps_endpoint_groups(api_client):
    client = api_client
    project = create_project(client)

    version = create_process_version(client, project["id"], version="v2")

    list_versions_response = client.get(f"/api/projects/{project['id']}/process-versions")
    assert list_versions_response.status_code == 200
    assert len(list_versions_response.json()) == 1

    version_get = client.get(f"/api/projects/{project['id']}/process-versions/{version['id']}")
    assert version_get.status_code == 200
    assert version_get.json()["version"] == "v2"

    version_patch = client.patch(
        f"/api/projects/{project['id']}/process-versions/{version['id']}",
        json={
            "version": "v2.1",
            "status": "approved",
            "as_is_json": {"steps": ["capture", "validate"]},
            "to_be_json": {"steps": ["capture", "validate", "approve"]},
        },
    )
    assert version_patch.status_code == 200
    assert version_patch.json()["status"] == "approved"

    step = create_process_step(client, project["id"], version["id"], name="Validate intake", step_key="validate")

    steps_response = client.get(f"/api/projects/{project['id']}/process-versions/{version['id']}/steps")
    assert steps_response.status_code == 200
    assert len(steps_response.json()) == 1

    step_get = client.get(f"/api/projects/{project['id']}/process-versions/{version['id']}/steps/{step['id']}")
    assert step_get.status_code == 200
    assert step_get.json()["name"] == "Validate intake"

    step_patch = client.patch(
        f"/api/projects/{project['id']}/process-versions/{version['id']}/steps/{step['id']}",
        json={
            "step_key": "validate",
            "name": "Updated validation",
            "actor": "manager",
            "step_type": "review",
            "sequence": 2,
        },
    )
    assert step_patch.status_code == 200
    assert step_patch.json()["name"] == "Updated validation"

    step_delete = client.delete(f"/api/projects/{project['id']}/process-versions/{version['id']}/steps/{step['id']}")
    assert step_delete.status_code == 204

    version_delete = client.delete(f"/api/projects/{project['id']}/process-versions/{version['id']}")
    assert version_delete.status_code == 204

    missing_version = client.get(f"/api/projects/{project['id']}/process-versions/{version['id']}")
    assert missing_version.status_code == 404


def test_business_rules_and_clarification_items_endpoint_groups(api_client):
    client = api_client
    project = create_project(client)

    rule = create_business_rule(client, project["id"], rule_key="BR-02")
    rules_list = client.get(f"/api/projects/{project['id']}/business-rules")
    assert rules_list.status_code == 200
    assert len(rules_list.json()) == 1

    rule_get = client.get(f"/api/projects/{project['id']}/business-rules/{rule['id']}")
    assert rule_get.status_code == 200
    assert rule_get.json()["rule_key"] == "BR-02"

    rule_patch = client.patch(
        f"/api/projects/{project['id']}/business-rules/{rule['id']}",
        json={
            "rule_key": "BR-02A",
            "description": "Updated rule description",
            "condition_json": {"requires_review": False},
            "status": "approved",
        },
    )
    assert rule_patch.status_code == 200
    assert rule_patch.json()["rule_key"] == "BR-02A"

    clarification = create_clarification_item(client, project["id"], question="Who approves the rule?")
    clarification_list = client.get(f"/api/projects/{project['id']}/clarification-items")
    assert clarification_list.status_code == 200
    assert len(clarification_list.json()) == 1

    clarification_get = client.get(f"/api/projects/{project['id']}/clarification-items/{clarification['id']}")
    assert clarification_get.status_code == 200
    assert clarification_get.json()["question"] == "Who approves the rule?"

    clarification_answer = client.patch(
        f"/api/projects/{project['id']}/clarification-items/{clarification['id']}/answer",
        json={
            "answer": "The compliance officer approves it.",
            "answered_by": "legal-team",
            "status": "answered",
        },
    )
    assert clarification_answer.status_code == 200
    assert clarification_answer.json()["answer"] == "The compliance officer approves it."

    clarification_delete = client.delete(f"/api/projects/{project['id']}/clarification-items/{clarification['id']}")
    assert clarification_delete.status_code == 204

    rule_delete = client.delete(f"/api/projects/{project['id']}/business-rules/{rule['id']}")
    assert rule_delete.status_code == 204

    missing_rule = client.get(f"/api/projects/{project['id']}/business-rules/{rule['id']}")
    assert missing_rule.status_code == 404

    invalid_rule = client.post(
        f"/api/projects/{project['id']}/business-rules",
        json={"rule_key": "", "description": "bad", "status": "draft"},
    )
    assert invalid_rule.status_code == 422


def test_requirements_and_related_link_endpoints(api_client):
    client = api_client
    project = create_project(client)

    requirement = create_requirement(client, project["id"], requirement_key="REQ-100")

    list_response = client.get(f"/api/projects/{project['id']}/requirements")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/projects/{project['id']}/requirements/{requirement['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["requirement_key"] == "REQ-100"

    patch_response = client.patch(
        f"/api/projects/{project['id']}/requirements/{requirement['id']}",
        json={
            "requirement_key": "REQ-100A",
            "type": "nonfunctional",
            "statement": "Updated requirement statement.",
            "priority": "medium",
            "status": "approved",
        },
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["priority"] == "medium"

    requirement_link_response = client.post(
        f"/api/projects/{project['id']}/requirements/{requirement['id']}/links",
        json={
            "target_id": "rule-123",
            "link_type": "derived_from",
        },
    )
    assert requirement_link_response.status_code == 201

    requirement_links = client.get(f"/api/projects/{project['id']}/requirements/{requirement['id']}/links")
    assert requirement_links.status_code == 200
    assert len(requirement_links.json()) == 1

    requirement_delete = client.delete(f"/api/projects/{project['id']}/requirements/{requirement['id']}")
    assert requirement_delete.status_code == 204

    invalid_requirement = client.post(
        f"/api/projects/{project['id']}/requirements",
        json={"requirement_key": "", "type": "functional", "statement": "bad", "priority": "high"},
    )
    assert invalid_requirement.status_code == 422


def test_artifacts_and_links_and_approvals_and_agent_runs(api_client):
    client = api_client
    project = create_project(client)

    artifact = create_artifact(client, project["id"], artifact_type="workflow")
    artifacts_list = client.get(f"/api/projects/{project['id']}/artifacts")
    assert artifacts_list.status_code == 200
    assert len(artifacts_list.json()) == 1

    artifact_get = client.get(f"/api/projects/{project['id']}/artifacts/{artifact['id']}")
    assert artifact_get.status_code == 200
    assert artifact_get.json()["artifact_type"] == "workflow"

    artifact_patch = client.patch(
        f"/api/projects/{project['id']}/artifacts/{artifact['id']}",
        json={
            "artifact_type": "workflow",
            "version": "2.0",
            "content_json": {"nodes": 4},
            "markdown": "# Updated workflow",
            "status": "approved",
        },
    )
    assert artifact_patch.status_code == 200
    assert artifact_patch.json()["status"] == "approved"

    requirement = create_requirement(client, project["id"], requirement_key="REQ-ART-1")
    artifact_link = client.post(
        f"/api/projects/{project['id']}/artifacts/{artifact['id']}/links",
        json={
            "target_type": "requirement",
            "target_id": requirement["id"],
            "link_type": "generated_from",
        },
    )
    assert artifact_link.status_code == 201

    artifact_links = client.get(f"/api/projects/{project['id']}/artifacts/{artifact['id']}/links")
    assert artifact_links.status_code == 200
    assert len(artifact_links.json()) == 1

    approval = create_approval(client, project["id"], target_id=requirement["id"])
    approvals_list = client.get(f"/api/projects/{project['id']}/approvals")
    assert approvals_list.status_code == 200
    assert len(approvals_list.json()) == 1

    approval_get = client.get(f"/api/projects/{project['id']}/approvals/{approval['id']}")
    assert approval_get.status_code == 200
    assert approval_get.json()["decision"] == "approved"

    approval_patch = client.patch(
        f"/api/projects/{project['id']}/approvals/{approval['id']}",
        json={
            "target_type": "requirement",
            "target_id": requirement["id"],
            "decision": "rejected",
            "reviewer": "control-reviewer",
            "comment": "Needs more evidence.",
        },
    )
    assert approval_patch.status_code == 200
    assert approval_patch.json()["decision"] == "rejected"

    agent_run = create_agent_run(client, project["id"], node_name="workflow-node")
    agent_runs_list = client.get(f"/api/projects/{project['id']}/agent-runs")
    assert agent_runs_list.status_code == 200
    assert len(agent_runs_list.json()) == 1

    agent_get = client.get(f"/api/projects/{project['id']}/agent-runs/{agent_run['id']}")
    assert agent_get.status_code == 200
    assert agent_get.json()["node_name"] == "workflow-node"

    agent_patch = client.patch(
        f"/api/projects/{project['id']}/agent-runs/{agent_run['id']}",
        json={
            "node_name": "workflow-node-updated",
            "status": "failed",
            "input_summary": "updated summary",
            "output_ref": "artifact://updated",
            "error": "temporary timeout",
        },
    )
    assert agent_patch.status_code == 200
    assert agent_patch.json()["status"] == "failed"

    agent_delete = client.delete(f"/api/projects/{project['id']}/agent-runs/{agent_run['id']}")
    assert agent_delete.status_code == 204

    approval_delete = client.delete(f"/api/projects/{project['id']}/approvals/{approval['id']}")
    assert approval_delete.status_code == 204

    artifact_delete = client.delete(f"/api/projects/{project['id']}/artifacts/{artifact['id']}")
    assert artifact_delete.status_code == 204

    invalid_approval = client.post(
        f"/api/projects/{project['id']}/approvals",
        json={"target_type": "requirement", "target_id": "missing-target", "decision": "approved", "reviewer": "ops"},
    )
    assert invalid_approval.status_code == 201


def test_test_cases_and_rule_evidence_traceability(api_client):
    client = api_client
    project = create_project(client)
    document = create_document(client, project["id"])
    section = create_document_section(client, project["id"], document["id"])
    evidence = create_evidence_item(client, project["id"], section["id"])
    rule = create_business_rule(client, project["id"], rule_key="BR-TRACE")
    requirement = create_requirement(client, project["id"], requirement_key="REQ-TRACE")
    version = create_process_version(client, project["id"], version="v-trace")
    step = create_process_step(client, project["id"], version["id"], name="Review requirement", step_key="review")

    rule_evidence_response = client.post(
        f"/api/projects/{project['id']}/business-rules/{rule['id']}/evidence",
        json={"evidence_id": evidence["id"]},
    )
    assert rule_evidence_response.status_code == 201

    rule_evidence_list = client.get(f"/api/projects/{project['id']}/business-rules/{rule['id']}/evidence")
    assert rule_evidence_list.status_code == 200
    assert len(rule_evidence_list.json()) == 1

    test_case = create_test_case(client, project["id"], requirement["id"], test_key="TC-TRACE")
    test_cases_response = client.get(f"/api/projects/{project['id']}/test-cases")
    assert test_cases_response.status_code == 200
    assert len(test_cases_response.json()) == 1

    traceability_response = client.get(f"/api/projects/{project['id']}/traceability")
    assert traceability_response.status_code == 200
    payload = traceability_response.json()
    assert payload["project_id"] == project["id"]
    assert payload["rule_evidence_links"]
    assert payload["requirements"]

    missing_project_traceability = client.get("/api/projects/missing-project/traceability")
    assert missing_project_traceability.status_code == 404

    invalid_rule_evidence = client.post(
        f"/api/projects/{project['id']}/business-rules/{rule['id']}/evidence",
        json={"evidence_id": "missing-evidence"},
    )
    assert invalid_rule_evidence.status_code == 404

    test_case_patch = client.patch(
        f"/api/projects/{project['id']}/test-cases/{test_case['id']}",
        json={
            "test_key": "TC-TRACE-UPDATED",
            "requirement_id": requirement["id"],
            "scenario": "Updated scenario",
            "expected_result": "Updated result",
        },
    )
    assert test_case_patch.status_code == 200
    assert test_case_patch.json()["test_key"] == "TC-TRACE-UPDATED"

    test_case_delete = client.delete(f"/api/projects/{project['id']}/test-cases/{test_case['id']}")
    assert test_case_delete.status_code == 204

    # Confirm the route path is the traceability endpoint, not the project detail route.
    project_detail = client.get(f"/api/projects/{project['id']}")
    assert project_detail.status_code == 200
