"""FastAPI routes for orchestrating AI agent runs."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.agent_run import AgentRunCreate, AgentRunRead
from processfoundry_ai.repositories.agent_run_repository import AgentRunRepository
from processfoundry_ai.repositories.project_repository import ProjectRepository

# Router for project runs: POST /api/projects/{project_id}/runs
project_runs_router = APIRouter()

# Router for runs status: GET /api/runs/{run_id}
runs_router = APIRouter()


def get_db_config() -> DatabaseConfig:
    return DatabaseConfig.from_env()


class RunStartRequest(BaseModel):
    """Payload to trigger an AI agent run."""

    node_name: str = Field(default="orchestrator", description="Target orchestrator node or workflow step")
    input_summary: str | None = Field(default=None, description="Optional description of the trigger inputs")


@project_runs_router.post(
    "",
    response_model=AgentRunRead,
    status_code=status.HTTP_201_CREATED,
)
def start_project_run(project_id: str, item: RunStartRequest | None = None):
    """Start discovery/redesign/artifact generation for a project."""
    config = get_db_config()
    project = ProjectRepository(config).get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    node = item.node_name if item and item.node_name else "orchestrator"
    summary = item.input_summary if item and item.input_summary else f"Started AI run for {project.name}"

    now = datetime.now(timezone.utc)
    run_payload = AgentRunCreate(
        id=str(uuid4()),
        project_id=project_id,
        node_name=node,
        status="in_progress",
        input_summary=summary,
        output_ref=None,
        error=None,
        created_at=now,
        updated_at=now,
    )
    return AgentRunRepository(config).create(run_payload)


@runs_router.get("/{run_id}", response_model=AgentRunRead)
def get_run_status(run_id: str):
    """Read run status, outputs, and errors by run ID."""
    config = get_db_config()
    run = AgentRunRepository(config).get_by_id(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return run
