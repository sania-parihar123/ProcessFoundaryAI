"""FastAPI routes for project operations."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.project import ProjectCreate, ProjectRead
from processfoundry_ai.repositories.project_repository import ProjectRepository

router = APIRouter()


class ProjectCreateRequest(BaseModel):
    """Fields the client must provide when creating a project."""

    name: str
    process_type: str
    description: str
    status: str = "draft"

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Project name must not be empty")
        return value.strip()


class ProjectUpdateRequest(BaseModel):
    """Fields that may be edited on an existing project."""

    name: str | None = None
    process_type: str | None = None
    description: str | None = None
    status: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Project name must not be empty")
        return value.strip()


def get_project_repository() -> ProjectRepository:
    config = DatabaseConfig.from_env()
    return ProjectRepository(config)


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(project_data: ProjectCreateRequest):
    """Create a project and save it to PostgreSQL."""

    now = datetime.now(timezone.utc)

    project = ProjectCreate(
        id=str(uuid4()),
        name=project_data.name,
        process_type=project_data.process_type,
        description=project_data.description,
        status=project_data.status,
        created_at=now,
        updated_at=now,
    )

    try:
        return get_project_repository().create(project)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="A project with conflicting data already exists.",
        )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Could not save the project to the database.",
        )


@router.get("", response_model=list[ProjectRead])
def list_projects(
    limit: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
):
    """Return all projects."""

    repo = get_project_repository()
    try:
        if hasattr(repo, "list_all"):
            return repo.list_all(limit=limit, offset=offset)
        if hasattr(repo, "list_projects"):
            return repo.list_projects()
        raise AttributeError("Project repository does not implement a list method.")
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve projects from the database.",
        )


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str):
    """Return one project by its ID."""

    try:
        project = get_project_repository().get_by_id(project_id)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve the project from the database.",
        )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: str, project_data: ProjectUpdateRequest):
    """Update fields on an existing project."""

    updates = project_data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=422,
            detail="At least one project field must be provided for update.",
        )

    try:
        project = get_project_repository().update(project_id, updates)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Could not update the project in the database.",
        )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str):
    """Delete a project by ID."""

    try:
        deleted = get_project_repository().delete(project_id)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Could not delete the project from the database.",
        )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    return None
