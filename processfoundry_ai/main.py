from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from processfoundry_ai.database.dependencies import get_db
from processfoundry_ai.api.routes.projects import router as projects_router
from processfoundry_ai.api.routes.documents import router as documents_router
from processfoundry_ai.api.routes.document_sections import (
    document_sections_router,
    evidence_items_router,
)
from processfoundry_ai.api.routes.process_resources import (
    agent_runs_router,
    approvals_router,
    artifacts_router,
    business_rules_router,
    clarification_items_router,
    process_steps_router,
    process_versions_router,
    requirements_router,
    test_cases_router,
)
from processfoundry_ai.api.routes.traceability_links import (
    artifact_links_router,
    requirement_links_router,
    rule_evidence_router,
    traceability_router,
)
from processfoundry_ai.api.routes.questions import (
    project_questions_router,
    questions_router,
)
from processfoundry_ai.api.routes.runs import (
    project_runs_router,
    runs_router,
)
from processfoundry_ai.api.routes.process_decisions import (
    process_decisions_router,
)
from processfoundry_ai.api.routes.artifacts import (
    artifacts_api_router,
)

app = FastAPI(
    title="ProcessFoundry AI API",
    description="API for verified digital workflow processing",
    version="1.0.0",
)

# Register the Projects API router
app.include_router(
    projects_router,
    prefix="/api/projects",
    tags=["Projects"],
)

app.include_router(
    documents_router,
    prefix="/api/projects/{project_id}/documents",
    tags=["Documents"],
)

app.include_router(
    document_sections_router,
    prefix="/api/projects/{project_id}/documents/{document_id}/sections",
    tags=["Document Sections"],
)
app.include_router(
    evidence_items_router,
    prefix="/api/projects/{project_id}/evidence-items",
    tags=["Evidence Items"],
)
app.include_router(
    process_versions_router,
    prefix="/api/projects/{project_id}/process-versions",
    tags=["Process Versions"],
)
app.include_router(
    process_steps_router,
    prefix="/api/projects/{project_id}/process-versions/{process_version_id}/steps",
    tags=["Process Steps"],
)
app.include_router(
    business_rules_router,
    prefix="/api/projects/{project_id}/business-rules",
    tags=["Business Rules"],
)
app.include_router(
    clarification_items_router,
    prefix="/api/projects/{project_id}/clarification-items",
    tags=["Clarification Items"],
)
app.include_router(
    requirements_router,
    prefix="/api/projects/{project_id}/requirements",
    tags=["Requirements"],
)
app.include_router(
    artifacts_router,
    prefix="/api/projects/{project_id}/artifacts",
    tags=["Artifacts"],
)
app.include_router(
    approvals_router,
    prefix="/api/projects/{project_id}/approvals",
    tags=["Approvals"],
)
app.include_router(
    agent_runs_router,
    prefix="/api/projects/{project_id}/agent-runs",
    tags=["Agent Runs"],
)
app.include_router(
    test_cases_router,
    prefix="/api/projects/{project_id}/test-cases",
    tags=["Test Cases"],
)
app.include_router(
    rule_evidence_router,
    prefix="/api/projects/{project_id}/business-rules/{business_rule_id}/evidence",
    tags=["Rule Evidence"],
)
app.include_router(
    requirement_links_router,
    prefix="/api/projects/{project_id}/requirements/{requirement_id}/links",
    tags=["Requirement Links"],
)
app.include_router(
    artifact_links_router,
    prefix="/api/projects/{project_id}/artifacts/{artifact_id}/links",
    tags=["Artifact Links"],
)
app.include_router(
    traceability_router,
    prefix="/api/projects/{project_id}",
    tags=["Traceability"],
)

# Canonical API routes from Design Specification (Section 13)
app.include_router(
    project_questions_router,
    prefix="/api/projects/{project_id}/questions",
    tags=["Clarification Questions"],
)
app.include_router(
    questions_router,
    prefix="/api/questions",
    tags=["Clarification Questions"],
)
app.include_router(
    project_runs_router,
    prefix="/api/projects/{project_id}/runs",
    tags=["AI Runs"],
)
app.include_router(
    runs_router,
    prefix="/api/runs",
    tags=["AI Runs"],
)
app.include_router(
    process_decisions_router,
    prefix="/api/process-versions",
    tags=["Process Approval"],
)
app.include_router(
    artifacts_api_router,
    prefix="/api/artifacts",
    tags=["Artifacts"],
)


@app.get("/")
def root():
    return {"message": "Welcome to ProcessFoundry AI API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/health/database")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "database": "available",
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable",
        )