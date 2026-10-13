"""Repository for requirement CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import Requirement as RequirementORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.requirement import RequirementCreate, RequirementRead


class RequirementRepository:
    """Repository for requirements table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, requirement: RequirementCreate) -> RequirementRead:
        """Create a new requirement.

        Args:
            requirement: Requirement data to create (RequirementCreate model).

        Returns:
            Created requirement as RequirementRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_requirement = RequirementORM(
                id=requirement.id,
                project_id=requirement.project_id,
                requirement_key=requirement.requirement_key,
                type=requirement.type,
                statement=requirement.statement,
                priority=requirement.priority,
                status=requirement.status,
            )
            session.add(orm_requirement)
            session.commit()
            session.refresh(orm_requirement)
            return RequirementRead.model_validate(orm_requirement)

    def get_by_id(self, requirement_id: str) -> RequirementRead | None:
        """Get requirement by ID.

        Args:
            requirement_id: Requirement ID to retrieve.

        Returns:
            RequirementRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(RequirementORM).where(RequirementORM.id == requirement_id)
            orm_requirement = session.scalars(stmt).first()

            if orm_requirement is None:
                return None

            return RequirementRead.model_validate(orm_requirement)

    def list_by_project(self, project_id: str) -> list[RequirementRead]:
        """List all requirements for a project.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of requirements for the project as RequirementRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(RequirementORM).where(RequirementORM.project_id == project_id)
            orm_requirements = session.scalars(stmt).all()
            return [RequirementRead.model_validate(r) for r in orm_requirements]

    def update(self, requirement_id: str, updates: dict) -> RequirementRead | None:
        """Update a requirement by ID."""
        with session_context(self.config) as session:
            orm_requirement = session.get(RequirementORM, requirement_id)
            if orm_requirement is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_requirement, field):
                    setattr(orm_requirement, field, value)

            session.commit()
            session.refresh(orm_requirement)
            return RequirementRead.model_validate(orm_requirement)

    def delete(self, requirement_id: str) -> bool:
        """Delete a requirement by ID."""
        with session_context(self.config) as session:
            orm_requirement = session.get(RequirementORM, requirement_id)
            if orm_requirement is None:
                return False
            session.delete(orm_requirement)
            session.commit()
            return True
