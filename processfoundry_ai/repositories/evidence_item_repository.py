"""Repository for evidence item CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import EvidenceItem as EvidenceItemORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.evidence_item import EvidenceItemCreate, EvidenceItemRead


class EvidenceItemRepository:
    """Repository for evidence_items table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, item: EvidenceItemCreate) -> EvidenceItemRead:
        """Create a new evidence item.

        Args:
            item: Evidence item data to create (EvidenceItemCreate model).

        Returns:
            Created evidence item as EvidenceItemRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_item = EvidenceItemORM(
                id=item.id,
                project_id=item.project_id,
                document_section_id=item.document_section_id,
                quote=item.quote,
                claim_type=item.claim_type,
                confidence=item.confidence,
            )
            session.add(orm_item)
            session.commit()
            session.refresh(orm_item)
            return EvidenceItemRead.model_validate(orm_item)

    def get_by_id(self, item_id: str) -> EvidenceItemRead | None:
        """Get evidence item by ID.

        Args:
            item_id: Evidence item ID to retrieve.

        Returns:
            EvidenceItemRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(EvidenceItemORM).where(EvidenceItemORM.id == item_id)
            orm_item = session.scalars(stmt).first()

            if orm_item is None:
                return None

            return EvidenceItemRead.model_validate(orm_item)

    def list_by_project(self, project_id: str) -> list[EvidenceItemRead]:
        """List all evidence items for a project ordered by claim type.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of evidence items for the project as EvidenceItemRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = (
                select(EvidenceItemORM)
                .where(EvidenceItemORM.project_id == project_id)
                .order_by(EvidenceItemORM.claim_type)
            )
            orm_items = session.scalars(stmt).all()
            return [EvidenceItemRead.model_validate(i) for i in orm_items]

    def list_by_document_section(self, section_id: str) -> list[EvidenceItemRead]:
        """List all evidence items for a document section ordered by confidence descending.

        Args:
            section_id: Document section ID to filter by.

        Returns:
            List of evidence items supporting the section as EvidenceItemRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = (
                select(EvidenceItemORM)
                .where(EvidenceItemORM.document_section_id == section_id)
                .order_by(EvidenceItemORM.confidence.desc())
            )
            orm_items = session.scalars(stmt).all()
            return [EvidenceItemRead.model_validate(i) for i in orm_items]

    def update(self, item_id: str, updates: dict) -> EvidenceItemRead | None:
        """Update an evidence item by ID.

        Args:
            item_id: Evidence item ID to update.
            updates: Dictionary of fields to update with their new values.

        Returns:
            Updated evidence item as EvidenceItemRead model, or None if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_item = session.get(EvidenceItemORM, item_id)
            if orm_item is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_item, field):
                    setattr(orm_item, field, value)

            session.commit()
            session.refresh(orm_item)
            return EvidenceItemRead.model_validate(orm_item)

    def delete(self, item_id: str) -> bool:
        """Delete an evidence item by ID.

        Args:
            item_id: Evidence item ID to delete.

        Returns:
            True if the item was deleted, False if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_item = session.get(EvidenceItemORM, item_id)
            if orm_item is None:
                return False
            session.delete(orm_item)
            session.commit()
            return True
