"""Repository for project CRUD operations."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import Project as ProjectORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.project import ProjectCreate, ProjectRead


class ProjectRepository:
    """Repository for projects table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, project: ProjectCreate) -> ProjectRead:
        """Create a new project.

        Args:
            project: Project data to create (ProjectCreate model).

        Returns:
            Created project as ProjectRead model.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_project = ProjectORM(
                id=project.id,
                name=project.name,
                process_type=project.process_type,
                description=project.description,
                status=project.status,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
            session.add(orm_project)
            session.commit()
            session.refresh(orm_project)
            return ProjectRead.model_validate(orm_project)

    def get_by_id(self, project_id: str) -> ProjectRead | None:
        """Get project by ID.

        Args:
            project_id: Project ID to retrieve.

        Returns:
            ProjectRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ProjectORM).where(ProjectORM.id == project_id)
            orm_project = session.scalars(stmt).first()

            if orm_project is None:
                return None

            return ProjectRead.model_validate(orm_project)

    def list_projects(self) -> list[ProjectRead]:
        """List all projects ordered by creation date descending.

        Returns:
            List of all projects as ProjectRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ProjectORM).order_by(ProjectORM.created_at.desc())
            orm_projects = session.scalars(stmt).all()
            return [ProjectRead.model_validate(p) for p in orm_projects]

    def list_all(self, limit: int | None = None, offset: int = 0) -> list[ProjectRead]:
        """List projects with optional pagination."""
        with session_context(self.config) as session:
            stmt = select(ProjectORM).order_by(ProjectORM.created_at.desc())
            if offset:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)
            orm_projects = session.scalars(stmt).all()
            return [ProjectRead.model_validate(p) for p in orm_projects]

    def update(self, project_id: str, updates: dict) -> ProjectRead | None:
        """Update a project by ID."""
        with session_context(self.config) as session:
            orm_project = session.get(ProjectORM, project_id)
            if orm_project is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_project, field):
                    setattr(orm_project, field, value)

            orm_project.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(orm_project)
            return ProjectRead.model_validate(orm_project)

    def delete(self, project_id: str) -> bool:
        """Delete a project by ID."""
        with session_context(self.config) as session:
            orm_project = session.get(ProjectORM, project_id)
            if orm_project is None:
                return False
            session.delete(orm_project)
            session.commit()
            return True
