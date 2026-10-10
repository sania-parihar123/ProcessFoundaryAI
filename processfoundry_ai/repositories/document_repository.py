"""Repository for document CRUD operations."""

from __future__ import annotations

import psycopg
from psycopg import Error as PsycopgError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.connection import get_connection
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
            PsycopgError: If database operation fails or foreign key constraint is violated.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO documents
                    (id, project_id, filename, mime_type, checksum, version, storage_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, project_id, filename, mime_type, checksum, version, storage_path
                    """,
                    (
                        document.id,
                        document.project_id,
                        document.filename,
                        document.mime_type,
                        document.checksum,
                        document.version,
                        document.storage_path,
                    ),
                )
                row = cur.fetchone()
            conn.commit()

            if row is None:
                raise PsycopgError("Failed to insert document (no result returned)")

            return DocumentRead(**row)
        except PsycopgError as e:
            if conn:
                conn.rollback()
            raise PsycopgError(f"Failed to create document: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_id(self, document_id: str) -> DocumentRead | None:
        """Get document by ID.

        Args:
            document_id: Document ID to retrieve.

        Returns:
            DocumentRead if found, None otherwise.

        Raises:
            PsycopgError: If database operation fails.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, filename, mime_type, checksum, version, storage_path
                    FROM documents
                    WHERE id = %s
                    """,
                    (document_id,),
                )
                row = cur.fetchone()
            conn.commit()

            if row is None:
                return None

            return DocumentRead(**row)
        except PsycopgError as e:
            raise PsycopgError(f"Failed to retrieve document: {e}") from e
        finally:
            if conn:
                conn.close()

    def list_by_project(self, project_id: str) -> list[DocumentRead]:
        """List all documents for a project.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of documents for the project as DocumentRead models.

        Raises:
            PsycopgError: If database operation fails.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, filename, mime_type, checksum, version, storage_path
                    FROM documents
                    WHERE project_id = %s
                    ORDER BY filename
                    """,
                    (project_id,),
                )
                rows = cur.fetchall()
            conn.commit()

            return [DocumentRead(**row) for row in rows]
        except PsycopgError as e:
            raise PsycopgError(f"Failed to list documents for project: {e}") from e
        finally:
            if conn:
                conn.close()
