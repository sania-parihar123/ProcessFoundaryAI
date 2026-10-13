"""Repository for document section CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import DocumentSection as DocumentSectionORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.document_section import (
    DocumentSectionCreate,
    DocumentSectionRead,
)


class DocumentSectionRepository:
    """Repository for document_sections table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, section: DocumentSectionCreate) -> DocumentSectionRead:
        """Create a new document section.

        Args:
            section: Document section data to create (DocumentSectionCreate model).

        Returns:
            Created section as DocumentSectionRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_section = DocumentSectionORM(
                id=section.id,
                document_id=section.document_id,
                page_number=section.page_number,
                section_title=section.section_title,
                text=section.text,
            )
            session.add(orm_section)
            session.commit()
            session.refresh(orm_section)
            return DocumentSectionRead.model_validate(orm_section)

    def get_by_id(self, section_id: str) -> DocumentSectionRead | None:
        """Get document section by ID.

        Args:
            section_id: Document section ID to retrieve.

        Returns:
            DocumentSectionRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(DocumentSectionORM).where(
                DocumentSectionORM.id == section_id
            )
            orm_section = session.scalars(stmt).first()

            if orm_section is None:
                return None

            return DocumentSectionRead.model_validate(orm_section)

    def list_by_document(self, document_id: str) -> list[DocumentSectionRead]:
        """List all sections for a document ordered by page number and section title.

        Args:
            document_id: Document ID to filter by.

        Returns:
            List of sections for the document as DocumentSectionRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = (
                select(DocumentSectionORM)
                .where(DocumentSectionORM.document_id == document_id)
                .order_by(
                    DocumentSectionORM.page_number, DocumentSectionORM.section_title
                )
            )
            orm_sections = session.scalars(stmt).all()
            return [DocumentSectionRead.model_validate(s) for s in orm_sections]

    def update(self, section_id: str, updates: dict) -> DocumentSectionRead | None:
        """Update a document section by ID.

        Args:
            section_id: Document section ID to update.
            updates: Dictionary of fields and values to update.

        Returns:
            Updated section as DocumentSectionRead model, or None if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_section = session.get(DocumentSectionORM, section_id)
            if orm_section is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_section, field):
                    setattr(orm_section, field, value)

            session.commit()
            session.refresh(orm_section)
            return DocumentSectionRead.model_validate(orm_section)

    def delete(self, section_id: str) -> bool:
        """Delete a document section by ID.

        Args:
            section_id: Document section ID to delete.

        Returns:
            True if deleted, False if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_section = session.get(DocumentSectionORM, section_id)
            if orm_section is None:
                return False
            session.delete(orm_section)
            session.commit()
            return True
