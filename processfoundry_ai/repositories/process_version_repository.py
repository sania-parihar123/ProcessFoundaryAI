"""Repository for process version CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import ProcessVersion as ProcessVersionORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.process_version import (
    ProcessVersionCreate,
    ProcessVersionRead,
)


class ProcessVersionRepository:
    """Repository for process_versions table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, process_version: ProcessVersionCreate) -> ProcessVersionRead:
        """Create a new process version.

        Args:
            process_version: Process version data to create (ProcessVersionCreate model).

        Returns:
            Created process version as ProcessVersionRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_process_version = ProcessVersionORM(
                id=process_version.id,
                project_id=process_version.project_id,
                version=process_version.version,
                as_is_json=process_version.as_is_json,
                to_be_json=process_version.to_be_json,
                status=process_version.status,
            )
            session.add(orm_process_version)
            session.commit()
            session.refresh(orm_process_version)
            return ProcessVersionRead.model_validate(orm_process_version)

    def get_by_id(self, process_version_id: str) -> ProcessVersionRead | None:
        """Get process version by ID.

        Args:
            process_version_id: Process version ID to retrieve.

        Returns:
            ProcessVersionRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ProcessVersionORM).where(ProcessVersionORM.id == process_version_id)
            orm_process_version = session.scalars(stmt).first()

            if orm_process_version is None:
                return None

            return ProcessVersionRead.model_validate(orm_process_version)

    def list_by_project(self, project_id: str) -> list[ProcessVersionRead]:
        """List all process versions for a project ordered by version descending.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of process versions for the project as ProcessVersionRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = (
                select(ProcessVersionORM)
                .where(ProcessVersionORM.project_id == project_id)
                .order_by(ProcessVersionORM.version.desc())
            )
            orm_process_versions = session.scalars(stmt).all()
            return [ProcessVersionRead.model_validate(pv) for pv in orm_process_versions]

    def update(self, process_version_id: str, updates: dict) -> ProcessVersionRead | None:
        """Update a process version by ID."""
        with session_context(self.config) as session:
            orm_process_version = session.get(ProcessVersionORM, process_version_id)
            if orm_process_version is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_process_version, field):
                    setattr(orm_process_version, field, value)

            session.commit()
            session.refresh(orm_process_version)
            return ProcessVersionRead.model_validate(orm_process_version)

    def delete(self, process_version_id: str) -> bool:
        """Delete a process version by ID."""
        with session_context(self.config) as session:
            orm_process_version = session.get(ProcessVersionORM, process_version_id)
            if orm_process_version is None:
                return False
            session.delete(orm_process_version)
            session.commit()
            return True
