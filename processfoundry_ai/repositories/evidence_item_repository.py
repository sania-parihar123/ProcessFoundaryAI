"""Repository for evidence item CRUD operations."""

from __future__ import annotations

import psycopg
from psycopg import Error as PsycopgError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.connection import get_connection
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
            PsycopgError: If database operation fails or foreign key constraint is violated.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO evidence_items
                    (id, project_id, document_section_id, quote, claim_type, confidence)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, project_id, document_section_id, quote, claim_type, confidence
                    """,
                    (
                        item.id,
                        item.project_id,
                        item.document_section_id,
                        item.quote,
                        item.claim_type,
                        item.confidence,
                    ),
                )
                row = cur.fetchone()
            conn.commit()

            if row is None:
                raise PsycopgError("Failed to insert evidence item (no result returned)")

            return EvidenceItemRead(**row)
        except PsycopgError as e:
            if conn:
                conn.rollback()
            raise PsycopgError(f"Failed to create evidence item: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_id(self, item_id: str) -> EvidenceItemRead | None:
        """Get evidence item by ID.

        Args:
            item_id: Evidence item ID to retrieve.

        Returns:
            EvidenceItemRead if found, None otherwise.

        Raises:
            PsycopgError: If database operation fails.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, document_section_id, quote, claim_type, confidence
                    FROM evidence_items
                    WHERE id = %s
                    """,
                    (item_id,),
                )
                row = cur.fetchone()
            conn.commit()

            if row is None:
                return None

            return EvidenceItemRead(**row)
        except PsycopgError as e:
            raise PsycopgError(f"Failed to retrieve evidence item: {e}") from e
        finally:
            if conn:
                conn.close()

    def list_by_project(self, project_id: str) -> list[EvidenceItemRead]:
        """List all evidence items for a project.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of evidence items for the project as EvidenceItemRead models.

        Raises:
            PsycopgError: If database operation fails.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, document_section_id, quote, claim_type, confidence
                    FROM evidence_items
                    WHERE project_id = %s
                    ORDER BY claim_type
                    """,
                    (project_id,),
                )
                rows = cur.fetchall()
            conn.commit()

            return [EvidenceItemRead(**row) for row in rows]
        except PsycopgError as e:
            raise PsycopgError(f"Failed to list evidence items for project: {e}") from e
        finally:
            if conn:
                conn.close()

    def list_by_document_section(self, section_id: str) -> list[EvidenceItemRead]:
        """List all evidence items for a document section (traceability).

        Args:
            section_id: Document section ID to filter by.

        Returns:
            List of evidence items supporting the section as EvidenceItemRead models.

        Raises:
            PsycopgError: If database operation fails.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, document_section_id, quote, claim_type, confidence
                    FROM evidence_items
                    WHERE document_section_id = %s
                    ORDER BY confidence DESC
                    """,
                    (section_id,),
                )
                rows = cur.fetchall()
            conn.commit()

            return [EvidenceItemRead(**row) for row in rows]
        except PsycopgError as e:
            raise PsycopgError(f"Failed to list evidence items for section: {e}") from e
        finally:
            if conn:
                conn.close()
