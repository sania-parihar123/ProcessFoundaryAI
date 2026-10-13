"""Repository for requirement link CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import RequirementLink as RequirementLinkORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.requirement_link import (
    RequirementLinkCreate,
    RequirementLinkRead,
)


class RequirementLinkRepository:
    """Repository for requirement_links table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, requirement_link: RequirementLinkCreate) -> RequirementLinkRead:
        """Create a new requirement link.

        Args:
            requirement_link: Requirement link data to create (RequirementLinkCreate model).

        Returns:
            Created requirement link as RequirementLinkRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_requirement_link = RequirementLinkORM(
                source_requirement_id=requirement_link.source_requirement_id,
                target_id=requirement_link.target_id,
                link_type=requirement_link.link_type,
            )
            session.add(orm_requirement_link)
            session.commit()
            session.refresh(orm_requirement_link)
            return RequirementLinkRead.model_validate(orm_requirement_link)

    def get_by_source_target_and_link_type(
        self, source_requirement_id: str, target_id: str, link_type: str
    ) -> RequirementLinkRead | None:
        """Get requirement link by composite primary key.

        Args:
            source_requirement_id: Source requirement ID.
            target_id: Target entity ID.
            link_type: Relationship type.

        Returns:
            RequirementLinkRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(RequirementLinkORM).where(
                (RequirementLinkORM.source_requirement_id == source_requirement_id)
                & (RequirementLinkORM.target_id == target_id)
                & (RequirementLinkORM.link_type == link_type)
            )
            orm_requirement_link = session.scalars(stmt).first()

            if orm_requirement_link is None:
                return None

            return RequirementLinkRead.model_validate(orm_requirement_link)

    def list_by_source_requirement(self, source_requirement_id: str) -> list[RequirementLinkRead]:
        """List all links from a source requirement.

        Args:
            source_requirement_id: Source requirement ID to filter by.

        Returns:
            List of requirement links as RequirementLinkRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(RequirementLinkORM).where(
                RequirementLinkORM.source_requirement_id == source_requirement_id
            )
            orm_requirement_links = session.scalars(stmt).all()
            return [RequirementLinkRead.model_validate(rl) for rl in orm_requirement_links]

    def list_by_target_id(self, target_id: str) -> list[RequirementLinkRead]:
        """List all requirement links pointing to a target entity ID.

        Args:
            target_id: Target entity identifier.

        Returns:
            List of requirement links as RequirementLinkRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(RequirementLinkORM).where(
                RequirementLinkORM.target_id == target_id
            )
            orm_requirement_links = session.scalars(stmt).all()
            return [RequirementLinkRead.model_validate(rl) for rl in orm_requirement_links]
