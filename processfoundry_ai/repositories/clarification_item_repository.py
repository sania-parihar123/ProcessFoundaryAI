"""Repository for clarification item CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import ClarificationItem as ClarificationItemORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.clarification_item import (
    ClarificationItemCreate,
    ClarificationItemRead,
)


class ClarificationItemRepository:
    """Repository for clarification_items table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, clarification_item: ClarificationItemCreate) -> ClarificationItemRead:
        """Create a new clarification item.

        Args:
            clarification_item: Clarification item data to create (ClarificationItemCreate model).

        Returns:
            Created clarification item as ClarificationItemRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_clarification_item = ClarificationItemORM(
                id=clarification_item.id,
                project_id=clarification_item.project_id,
                question=clarification_item.question,
                reason=clarification_item.reason,
                status=clarification_item.status,
                answer=clarification_item.answer,
                answered_by=clarification_item.answered_by,
            )
            session.add(orm_clarification_item)
            session.commit()
            session.refresh(orm_clarification_item)
            return ClarificationItemRead.model_validate(orm_clarification_item)

    def get_by_id(self, clarification_item_id: str) -> ClarificationItemRead | None:
        """Get clarification item by ID.

        Args:
            clarification_item_id: Clarification item ID to retrieve.

        Returns:
            ClarificationItemRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ClarificationItemORM).where(
                ClarificationItemORM.id == clarification_item_id
            )
            orm_clarification_item = session.scalars(stmt).first()

            if orm_clarification_item is None:
                return None

            return ClarificationItemRead.model_validate(orm_clarification_item)

    def list_by_project(self, project_id: str) -> list[ClarificationItemRead]:
        """List all clarification items for a project.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of clarification items for the project as ClarificationItemRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ClarificationItemORM).where(
                ClarificationItemORM.project_id == project_id
            )
            orm_clarification_items = session.scalars(stmt).all()
            return [ClarificationItemRead.model_validate(ci) for ci in orm_clarification_items]

    def update(self, clarification_item_id: str, updates: dict) -> ClarificationItemRead | None:
        """Update a clarification item by ID.

        Args:
            clarification_item_id: Clarification item ID to update.
            updates: Dictionary of fields and values to update.

        Returns:
            Updated clarification item as ClarificationItemRead model, or None if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_clarification_item = session.get(ClarificationItemORM, clarification_item_id)
            if orm_clarification_item is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_clarification_item, field):
                    setattr(orm_clarification_item, field, value)

            session.commit()
            session.refresh(orm_clarification_item)
            return ClarificationItemRead.model_validate(orm_clarification_item)

    def delete(self, clarification_item_id: str) -> bool:
        """Delete a clarification item by ID.

        Args:
            clarification_item_id: Clarification item ID to delete.

        Returns:
            True if deletion was successful, False if item was not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_clarification_item = session.get(ClarificationItemORM, clarification_item_id)
            if orm_clarification_item is None:
                return False
            session.delete(orm_clarification_item)
            session.commit()
            return True
