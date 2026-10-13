"""Repository for document CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import Document as DocumentORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.document import DocumentCreate, DocumentRead


class DocumentRepository:
    """Repository for documents table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, document: DocumentCreate) -> DocumentRead:
        """Create a new document.

        Args:
            document: Document data to create (DocumentCreate model).

        Returns:
            Created document as DocumentRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_document = DocumentORM(
                id=document.id,
                project_id=document.project_id,
                filename=document.filename,
                mime_type=document.mime_type,
                checksum=document.checksum,
                version=document.version,
                storage_path=document.storage_path,
            )
            session.add(orm_document)
            session.commit()
            session.refresh(orm_document)
            return DocumentRead.model_validate(orm_document)

    def get_by_id(self, document_id: str) -> DocumentRead | None:
        """Get document by ID.

        Args:
            document_id: Document ID to retrieve.

        Returns:
            DocumentRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(DocumentORM).where(DocumentORM.id == document_id)
            orm_document = session.scalars(stmt).first()

            if orm_document is None:
                return None

            return DocumentRead.model_validate(orm_document)

    def list_by_project(
        self, project_id: str, limit: int | None = None, offset: int = 0
    ) -> list[DocumentRead]:
        """List all documents for a project ordered by filename.

        Args:
            project_id: Project ID to filter by.
            limit: Maximum number of documents to return (for pagination).
            offset: Number of documents to skip before starting to collect the result set (for pagination).

        Returns:
            List of documents for the project as DocumentRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = (
                select(DocumentORM)
                .where(DocumentORM.project_id == project_id)
                .order_by(DocumentORM.filename)
            )
            if offset:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)
            orm_documents = session.scalars(stmt).all()
            return [DocumentRead.model_validate(d) for d in orm_documents]

    def update(self, document_id: str, updates: dict) -> DocumentRead | None:
        """Update a document by ID.

        Args:
            document_id: Document ID to update.
            updates: Dictionary of fields and values to update.

        Returns:
            Updated document as DocumentRead model, or None if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_document = session.get(DocumentORM, document_id)
            if orm_document is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_document, field):
                    setattr(orm_document, field, value)

            session.commit()
            session.refresh(orm_document)
            return DocumentRead.model_validate(orm_document)

    def delete(self, document_id: str) -> bool:
        """Delete a document by ID.

        Args:
            document_id: Document ID to delete.

        Returns:
            True if the document was deleted, False if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_document = session.get(DocumentORM, document_id)
            if orm_document is None:
                return False
            session.delete(orm_document)
            session.commit()
            return True
