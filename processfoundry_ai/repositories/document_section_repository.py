"""Repository for document section CRUD operations."""

from __future__ import annotations

import psycopg
from psycopg import Error as PsycopgError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.connection import get_connection
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
            PsycopgError: If database operation fails or foreign key constraint is violated.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO document_sections
                    (id, document_id, page_number, section_title, text)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, document_id, page_number, section_title, text
                    """,
                    (
                        section.id,
                        section.document_id,
                        section.page_number,
                        section.section_title,
                        section.text,
                    ),
                )
                row = cur.fetchone()
            conn.commit()

            if row is None:
                raise PsycopgError("Failed to insert document section (no result returned)")

            return DocumentSectionRead(**row)
        except PsycopgError as e:
            if conn:
                conn.rollback()
            raise PsycopgError(f"Failed to create document section: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_id(self, section_id: str) -> DocumentSectionRead | None:
        """Get document section by ID.

        Args:
            section_id: Document section ID to retrieve.

        Returns:
            DocumentSectionRead if found, None otherwise.

        Raises:
            PsycopgError: If database operation fails.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, document_id, page_number, section_title, text
                    FROM document_sections
                    WHERE id = %s
                    """,
                    (section_id,),
                )
                row = cur.fetchone()
            conn.commit()

            if row is None:
                return None

            return DocumentSectionRead(**row)
        except PsycopgError as e:
            raise PsycopgError(f"Failed to retrieve document section: {e}") from e
        finally:
            if conn:
                conn.close()

    def list_by_document(self, document_id: str) -> list[DocumentSectionRead]:
        """List all sections for a document.

        Args:
            document_id: Document ID to filter by.

        Returns:
            List of sections for the document as DocumentSectionRead models.

        Raises:
            PsycopgError: If database operation fails.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, document_id, page_number, section_title, text
                    FROM document_sections
                    WHERE document_id = %s
                    ORDER BY page_number, section_title
                    """,
                    (document_id,),
                )
                rows = cur.fetchall()
            conn.commit()

            return [DocumentSectionRead(**row) for row in rows]
        except PsycopgError as e:
            raise PsycopgError(f"Failed to list document sections: {e}") from e
        finally:
            if conn:
                conn.close()
