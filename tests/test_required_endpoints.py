"""Comprehensive automated test suite for all 15 required ProcessFoundry AI endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from processfoundry_ai.api.routes import documents as documents_module
from processfoundry_ai.database.base import Base
from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.session import dispose_engine, get_engine
from processfoundry_ai.main import app


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Provide a TestClient backed by SQLite memory DB and temporary upload dir."""
    dispose_engine()
    config = DatabaseConfig(dsn="sqlite:///:memory:")
    engine = get_engine(config)
    Base.metadata.create_all(engine)

    monkeypatch.setattr(DatabaseConfig, "from_env", staticmethod(lambda: config))
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(documents_module, "UPLOAD_DIR", upload_dir)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(engine)
    dispose_engine()


# Helper utilities for populating resources
def create_test_project(client, name="Scholarship Workflow", process_type="scholarship"):
    res = client.post(
        "/api/projects",
        json={
            "name": name,
            "process_type": process_type,
            "description": "Redesign student scholarship process.",
            "status": "draft",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


# ---------------------------------------------------------------------------
# Endpoint 1: POST /api/projects
# ---------------------------------------------------------------------------
def test_endpoint_1_create_project(client):
    res = client.post(
        "/api/projects",
        json={
            "name": "Hostel Allocation",
            "process_type": "accommodation",
            "description": "Room allocation workflow",
            "status": "draft",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Hostel Allocation"
    assert data["process_type"] == "accommodation"
    assert data["id"]
    assert data["created_at"]
    assert data["updated_at"]

    # Validation: empty name rejected
    bad_res = client.post(
        "/api/projects",
        json={"name": "   ", "process_type": "accommodation", "description": "test"},
    )
    assert bad_res.status_code == 422


# ---------------------------------------------------------------------------
# Endpoint 2: GET /api/projects
# ---------------------------------------------------------------------------
def test_endpoint_2_list_projects(client):
    create_test_project(client, name="Project Alpha")
    create_test_project(client, name="Project Beta")

    res = client.get("/api/projects?limit=10&offset=0")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    names = [p["name"] for p in items]
    assert "Project Alpha" in names
    assert "Project Beta" in names


# ---------------------------------------------------------------------------
# Endpoint 3: GET /api/projects/{project_id}
# ---------------------------------------------------------------------------
def test_endpoint_3_get_project_by_id(client):
    project = create_test_project(client, name="Admissions Process")
    res = client.get(f"/api/projects/{project['id']}")
    assert res.status_code == 200
    assert res.json()["name"] == "Admissions Process"

    # Missing project
    missing_res = client.get("/api/projects/missing-project-id")
    assert missing_res.status_code == 404
    assert missing_res.json()["detail"] == "Project not found."


# ---------------------------------------------------------------------------
# Endpoint 4: POST /api/projects/{project_id}/documents
# ---------------------------------------------------------------------------
def test_endpoint_4_upload_document(client):
    project = create_test_project(client)

    # 1. PDF upload
    pdf_res = client.post(
        f"/api/projects/{project['id']}/documents",
        files={"file": ("policy.pdf", b"%PDF-1.4 sample content", "application/pdf")},
    )
    assert pdf_res.status_code == 201
    assert pdf_res.json()["filename"] == "policy.pdf"
    assert pdf_res.json()["mime_type"] == "application/pdf"

    # 2. TXT upload (Official design requirement)
    txt_res = client.post(
        f"/api/projects/{project['id']}/documents",
        files={"file": ("guidelines.txt", b"Scholarship rules and deadlines text.", "text/plain")},
    )
    assert txt_res.status_code == 201
    assert txt_res.json()["filename"] == "guidelines.txt"
    assert txt_res.json()["mime_type"] == "text/plain"

    # 3. Unsupported file type rejected with 415
    bad_type = client.post(
        f"/api/projects/{project['id']}/documents",
        files={"file": ("app.exe", b"binary content", "application/octet-stream")},
    )
    assert bad_type.status_code == 415

    # 4. Empty file rejected with 400
    empty_res = client.post(
        f"/api/projects/{project['id']}/documents",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert empty_res.status_code == 400

    # 5. Missing project returns 404
    missing_res = client.post(
        "/api/projects/missing-project-id/documents",
        files={"file": ("notes.txt", b"some notes", "text/plain")},
    )
    assert missing_res.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint 5: GET /api/projects/{project_id}/documents
# ---------------------------------------------------------------------------
def test_endpoint_5_list_documents(client):
    project = create_test_project(client)
    client.post(
        f"/api/projects/{project['id']}/documents",
        files={"file": ("doc1.pdf", b"%PDF-1.4 file 1", "application/pdf")},
    )
    client.post(
        f"/api/projects/{project['id']}/documents",
        files={"file": ("doc2.txt", b"plain text 2", "text/plain")},
    )

    res = client.get(f"/api/projects/{project['id']}/documents")
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) == 2
    filenames = [d["filename"] for d in docs]
    assert "doc1.pdf" in filenames
    assert "doc2.txt" in filenames

    # Missing project
    missing_res = client.get("/api/projects/missing-project-id/documents")
    assert missing_res.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint 6: POST /api/projects/{project_id}/runs
# ---------------------------------------------------------------------------
def test_endpoint_6_start_project_run(client):
    project = create_test_project(client)

    # Start run with default payload
    res = client.post(f"/api/projects/{project['id']}/runs", json={})
    assert res.status_code == 201
    run = res.json()
    assert run["project_id"] == project["id"]
    assert run["status"] == "in_progress"
    assert run["node_name"] == "orchestrator"
    assert run["id"]

    # Start run with custom node_name
    custom_res = client.post(
        f"/api/projects/{project['id']}/runs",
        json={"node_name": "discovery", "input_summary": "Initial SOP analysis"},
    )
    assert custom_res.status_code == 201
    assert custom_res.json()["node_name"] == "discovery"
    assert custom_res.json()["input_summary"] == "Initial SOP analysis"

    # Missing project returns 404
    missing_res = client.post("/api/projects/missing-project/runs", json={})
    assert missing_res.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint 7: GET /api/runs/{run_id}
# ---------------------------------------------------------------------------
def test_endpoint_7_get_run_status(client):
    project = create_test_project(client)
    create_res = client.post(f"/api/projects/{project['id']}/runs", json={"node_name": "discovery"})
    run_id = create_res.json()["id"]

    res = client.get(f"/api/runs/{run_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == run_id
    assert data["project_id"] == project["id"]
    assert data["node_name"] == "discovery"

    # Missing run returns 404
    missing_res = client.get("/api/runs/nonexistent-run-id")
    assert missing_res.status_code == 404
    assert missing_res.json()["detail"] == "Run not found."


# ---------------------------------------------------------------------------
# Endpoint 8: GET /api/projects/{project_id}/questions
# ---------------------------------------------------------------------------
def test_endpoint_8_list_project_questions(client):
    project = create_test_project(client)

    # Seed clarification questions via existing route
    client.post(
        f"/api/projects/{project['id']}/clarification-items",
        json={
            "question": "What is the minimum GPA requirement?",
            "reason": "Contradiction in page 3 vs page 5",
            "status": "open",
        },
    )
    client.post(
        f"/api/projects/{project['id']}/clarification-items",
        json={
            "question": "Who signs the financial hardship form?",
            "reason": "Role unassigned",
            "status": "open",
        },
    )

    # Required endpoint: GET /api/projects/{project_id}/questions
    res = client.get(f"/api/projects/{project['id']}/questions")
    assert res.status_code == 200
    questions = res.json()
    assert len(questions) == 2
    assert questions[0]["question"] == "What is the minimum GPA requirement?"

    # Optional status filter
    filter_res = client.get(f"/api/projects/{project['id']}/questions?status=answered")
    assert filter_res.status_code == 200
    assert len(filter_res.json()) == 0

    # Missing project returns 404
    missing_res = client.get("/api/projects/missing-project/questions")
    assert missing_res.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint 9: POST /api/questions/{question_id}/answer
# ---------------------------------------------------------------------------
def test_endpoint_9_answer_question(client):
    project = create_test_project(client)
    item_res = client.post(
        f"/api/projects/{project['id']}/clarification-items",
        json={
            "question": "Are part-time students eligible?",
            "reason": "Policy missing part-time criteria",
            "status": "open",
        },
    )
    question_id = item_res.json()["id"]

    # Required endpoint: POST /api/questions/{question_id}/answer
    res = client.post(
        f"/api/questions/{question_id}/answer",
        json={
            "answer": "No, only full-time students enrolled in >= 12 credits.",
            "answered_by": "Dean of Students",
        },
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["status"] == "answered"
    assert updated["answer"] == "No, only full-time students enrolled in >= 12 credits."
    assert updated["answered_by"] == "Dean of Students"

    # Validation: empty answer rejected with 422
    bad_res = client.post(
        f"/api/questions/{question_id}/answer",
        json={"answer": "", "answered_by": "Dean"},
    )
    assert bad_res.status_code == 422

    # Missing question returns 404
    missing_res = client.post(
        "/api/questions/nonexistent-question/answer",
        json={"answer": "yes", "answered_by": "admin"},
    )
    assert missing_res.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint 10: POST /api/process-versions/{version_id}/decision
# ---------------------------------------------------------------------------
def test_endpoint_10_process_version_decision(client):
    project = create_test_project(client)
    v_res = client.post(
        f"/api/projects/{project['id']}/process-versions",
        json={
            "version": "1.0",
            "as_is_json": {"steps": ["apply", "review"]},
            "to_be_json": {"steps": ["apply", "auto_check", "human_review"]},
            "status": "draft",
        },
    )
    version_id = v_res.json()["id"]

    # 1. Approve decision
    dec_res = client.post(
        f"/api/process-versions/{version_id}/decision",
        json={
            "decision": "approved",
            "reviewer": "Process Owner (Prof. Sharma)",
            "comment": "To-Be flow correctly includes automated eligibility check.",
        },
    )
    assert dec_res.status_code == 200
    data = dec_res.json()
    assert data["process_version"]["status"] == "approved"
    assert data["approval"]["decision"] == "approved"
    assert data["approval"]["target_type"] == "process_version"
    assert data["approval"]["target_id"] == version_id
    assert data["approval"]["reviewer"] == "Process Owner (Prof. Sharma)"

    # Verify version status persisted
    get_v = client.get(f"/api/projects/{project['id']}/process-versions/{version_id}")
    assert get_v.status_code == 200
    assert get_v.json()["status"] == "approved"

    # 2. Request changes decision
    changes_res = client.post(
        f"/api/process-versions/{version_id}/decision",
        json={
            "decision": "changes_requested",
            "reviewer": "Quality Auditor",
            "comment": "Please add exception handling for late submissions.",
        },
    )
    assert changes_res.status_code == 200
    assert changes_res.json()["process_version"]["status"] == "changes_requested"

    # 3. Invalid decision string returns 422
    bad_dec = client.post(
        f"/api/process-versions/{version_id}/decision",
        json={"decision": "maybe", "reviewer": "Reviewer"},
    )
    assert bad_dec.status_code == 422

    # 4. Missing process version returns 404
    missing_res = client.post(
        "/api/process-versions/missing-version-id/decision",
        json={"decision": "approved", "reviewer": "Reviewer"},
    )
    assert missing_res.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint 11: GET /api/projects/{project_id}/artifacts
# ---------------------------------------------------------------------------
def test_endpoint_11_list_artifacts(client):
    project = create_test_project(client)
    client.post(
        f"/api/projects/{project['id']}/artifacts",
        json={
            "artifact_type": "brd",
            "version": "1.0",
            "content_json": {"title": "Business Requirements Document"},
            "markdown": "# BRD\n\nContent",
            "status": "draft",
        },
    )

    res = client.get(f"/api/projects/{project['id']}/artifacts")
    assert res.status_code == 200
    artifacts = res.json()
    assert len(artifacts) == 1
    assert artifacts[0]["artifact_type"] == "brd"

    # Missing project returns 404
    missing_res = client.get("/api/projects/missing-project/artifacts")
    assert missing_res.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint 12: GET /api/artifacts/{artifact_id}
# ---------------------------------------------------------------------------
def test_endpoint_12_get_artifact_by_id(client):
    project = create_test_project(client)
    art_res = client.post(
        f"/api/projects/{project['id']}/artifacts",
        json={
            "artifact_type": "prd",
            "version": "1.0",
            "content_json": {"goals": ["automate triage"]},
            "markdown": "# PRD Content",
            "status": "draft",
        },
    )
    artifact_id = art_res.json()["id"]

    # Required top-level endpoint
    res = client.get(f"/api/artifacts/{artifact_id}")
    assert res.status_code == 200
    assert res.json()["id"] == artifact_id
    assert res.json()["artifact_type"] == "prd"

    # Missing artifact returns 404
    missing_res = client.get("/api/artifacts/nonexistent-artifact")
    assert missing_res.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint 13: PATCH /api/artifacts/{artifact_id}
# ---------------------------------------------------------------------------
def test_endpoint_13_patch_artifact_new_version(client):
    project = create_test_project(client)
    art_res = client.post(
        f"/api/projects/{project['id']}/artifacts",
        json={
            "artifact_type": "frd",
            "version": "1.0",
            "content_json": {"feature": "login"},
            "markdown": "# FRD v1.0",
            "status": "approved",
        },
    )
    artifact_id = art_res.json()["id"]

    # Required endpoint: PATCH saves human edit as a new version
    patch_res = client.patch(
        f"/api/artifacts/{artifact_id}",
        json={
            "markdown": "# FRD v1.1 Updated with 2FA",
            "status": "needs_review",
        },
    )
    assert patch_res.status_code == 200
    new_art = patch_res.json()
    assert new_art["id"] != artifact_id  # New version record created
    assert new_art["version"] == "1.1"   # Bumped version
    assert new_art["markdown"] == "# FRD v1.1 Updated with 2FA"
    assert new_art["status"] == "needs_review"

    # Original version remains intact in history
    orig_res = client.get(f"/api/artifacts/{artifact_id}")
    assert orig_res.status_code == 200
    assert orig_res.json()["version"] == "1.0"

    # Empty update body returns 422
    bad_res = client.patch(f"/api/artifacts/{artifact_id}", json={})
    assert bad_res.status_code == 422

    # Missing artifact returns 404
    missing_res = client.patch("/api/artifacts/missing-art", json={"markdown": "x"})
    assert missing_res.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint 14: GET /api/artifacts/{artifact_id}/download
# ---------------------------------------------------------------------------
def test_endpoint_14_download_artifact(client):
    project = create_test_project(client)
    art_res = client.post(
        f"/api/projects/{project['id']}/artifacts",
        json={
            "artifact_type": "test_plan",
            "version": "2.0",
            "content_json": {"cases": 15},
            "markdown": "# Complete Test Plan\n- Case 1: Pass\n- Case 2: Fail",
            "status": "draft",
        },
    )
    artifact_id = art_res.json()["id"]

    # 1. Download as Markdown
    md_res = client.get(f"/api/artifacts/{artifact_id}/download?format=markdown")
    assert md_res.status_code == 200
    assert "text/markdown" in md_res.headers["content-type"]
    assert 'attachment; filename="test_plan_2.0.md"' in md_res.headers["content-disposition"]
    assert md_res.text.startswith("# Complete Test Plan")

    # 2. Download as JSON
    json_res = client.get(f"/api/artifacts/{artifact_id}/download?format=json")
    assert json_res.status_code == 200
    assert "application/json" in json_res.headers["content-type"]
    assert 'attachment; filename="test_plan_2.0.json"' in json_res.headers["content-disposition"]
    assert json_res.json() == {"cases": 15}

    # 3. Invalid format returns 400
    bad_res = client.get(f"/api/artifacts/{artifact_id}/download?format=pdf")
    assert bad_res.status_code == 400

    # 4. Missing artifact returns 404
    missing_res = client.get("/api/artifacts/missing-artifact/download")
    assert missing_res.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint 15: GET /api/projects/{project_id}/traceability
# ---------------------------------------------------------------------------
def test_endpoint_15_project_traceability(client):
    project = create_test_project(client)
    pid = project["id"]

    # Setup linked chain: document -> section -> evidence -> rule -> requirement -> step -> test
    doc = client.post(
        f"/api/projects/{pid}/documents",
        files={"file": ("sop.pdf", b"%PDF-1.4 SOP content", "application/pdf")},
    ).json()

    sec = client.post(
        f"/api/projects/{pid}/documents/{doc['id']}/sections",
        json={"page_number": 1, "section_title": "Eligibility", "text": "Minimum credits 60"},
    ).json()

    evd = client.post(
        f"/api/projects/{pid}/evidence-items",
        json={"document_section_id": sec["id"], "quote": "Minimum credits 60", "claim_type": "rule", "confidence": 0.95},
    ).json()

    rule = client.post(
        f"/api/projects/{pid}/business-rules",
        json={"rule_key": "BR-CREDIT-60", "description": "Student must have 60 credits", "status": "draft"},
    ).json()

    req = client.post(
        f"/api/projects/{pid}/requirements",
        json={"requirement_key": "REQ-CREDIT-VALIDATION", "type": "functional", "statement": "Verify 60 credits", "priority": "high", "status": "draft"},
    ).json()

    pv = client.post(
        f"/api/projects/{pid}/process-versions",
        json={"version": "1.0", "as_is_json": {}, "to_be_json": {}, "status": "draft"},
    ).json()

    step = client.post(
        f"/api/projects/{pid}/process-versions/{pv['id']}/steps",
        json={"step_key": "VERIFY_CREDITS", "name": "Verify Credits", "actor": "system", "step_type": "automated", "sequence": 1},
    ).json()

    tc = client.post(
        f"/api/projects/{pid}/test-cases",
        json={"test_key": "TC-01", "requirement_id": req["id"], "scenario": "Student with 59 credits rejected", "expected_result": "Rejection notification"},
    ).json()

    client.post(
        f"/api/projects/{pid}/business-rules/{rule['id']}/evidence",
        json={"evidence_id": evd["id"]},
    )
    client.post(
        f"/api/projects/{pid}/requirements/{req['id']}/links",
        json={"target_id": rule["id"], "link_type": "derived_from"},
    )

    # Required endpoint: GET /api/projects/{project_id}/traceability
    res = client.get(f"/api/projects/{pid}/traceability")
    assert res.status_code == 200
    trace = res.json()

    assert trace["project_id"] == pid
    assert len(trace["documents"]) >= 1
    assert len(trace["evidence_items"]) >= 1
    assert len(trace["business_rules"]) >= 1
    assert len(trace["requirements"]) >= 1
    assert len(trace["test_cases"]) >= 1
    assert len(trace["process_versions"]) >= 1
    assert len(trace["process_steps"]) >= 1
    assert len(trace["rule_evidence_links"]) >= 1
    assert len(trace["requirement_links"]) >= 1

    # Verify entities match seeded data
    assert trace["test_cases"][0]["test_key"] == "TC-01"
    assert trace["process_steps"][0]["step_key"] == "VERIFY_CREDITS"
    assert trace["documents"][0]["filename"] == "sop.pdf"

    # Missing project returns 404
    missing_res = client.get("/api/projects/missing-project/traceability")
    assert missing_res.status_code == 404
