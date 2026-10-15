"""FastAPI routes for artifact operations and downloads."""

from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.artifact import ArtifactCreate, ArtifactRead
from processfoundry_ai.repositories.artifact_repository import ArtifactRepository

artifacts_api_router = APIRouter()


def get_db_config() -> DatabaseConfig:
    return DatabaseConfig.from_env()


class ArtifactUpdateRequest(BaseModel):
    """Payload to save an edit to an artifact."""

    content_json: dict | None = None
    markdown: str | None = None
    status: str | None = None
    version: str | None = None


def _next_version(current_version: str) -> str:
    """Helper to bump version string (e.g. '1.0' -> '1.1' or '1' -> '2')."""
    try:
        parts = current_version.split(".")
        if len(parts) == 2:
            return f"{parts[0]}.{int(parts[1]) + 1}"
        if len(parts) == 1:
            return str(int(parts[0]) + 1)
    except Exception:
        pass
    return f"{current_version}.1"


@artifacts_api_router.get("/{artifact_id}", response_model=ArtifactRead)
def get_artifact_by_id(artifact_id: str):
    """Read artifact content and status by artifact ID."""
    config = get_db_config()
    artifact = ArtifactRepository(config).get_by_id(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return artifact


@artifacts_api_router.patch("/{artifact_id}", response_model=ArtifactRead)
def update_artifact_version(artifact_id: str, item: ArtifactUpdateRequest):
    """Save a human edit as a new version of the artifact."""
    config = get_db_config()
    repo = ArtifactRepository(config)
    current = repo.get_by_id(artifact_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")

    updates = item.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=422,
            detail="At least one field must be provided for update.",
        )

    # Determine new version string according to design: "Save a human edit as a new version"
    new_version = item.version if item.version else _next_version(current.version)

    new_payload = ArtifactCreate(
        id=str(uuid4()),
        project_id=current.project_id,
        artifact_type=current.artifact_type,
        version=new_version,
        content_json=item.content_json if item.content_json is not None else current.content_json,
        markdown=item.markdown if item.markdown is not None else current.markdown,
        status=item.status if item.status is not None else "needs_review",
    )
    new_artifact = repo.create(new_payload)
    return new_artifact


@artifacts_api_router.get("/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    format: str = Query(default="markdown", description="Format: markdown or json"),
):
    """Download an artifact as Markdown or JSON file."""
    config = get_db_config()
    artifact = ArtifactRepository(config).get_by_id(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")

    fmt = format.lower().strip()
    if fmt in {"markdown", "md"}:
        content = artifact.markdown or ""
        filename = f"{artifact.artifact_type}_{artifact.version}.md"
        return Response(
            content=content,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    elif fmt == "json":
        content = json.dumps(artifact.content_json or {}, indent=2)
        filename = f"{artifact.artifact_type}_{artifact.version}.json"
        return Response(
            content=content,
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Supported download formats are 'markdown' and 'json'.",
        )
