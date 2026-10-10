"""Repository for project CRUD operations."""

from __future__ import annotations

from datetime import datetime

import psycopg
from psycopg import Error as PsycopgError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.connection import get_connection
from processfoundry_ai.models.project import ProjectCreate, ProjectRead


class ProjectRepository:
    """Repository for projects table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, project: ProjectCreate) -> ProjectRead:
        """Create a new project.

        Args:
            project: Project data to create (ProjectCreate model).

        Returns:
            Created project as ProjectRead model.

        Raises:
            PsycopgError: If database operation fails.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO projects
                    (id, name, process_type, description, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, name, process_type, description, status, created_at, updated_at
                    """,
                    (
                        project.id,
                        project.name,
                        project.process_type,
                        project.description,
                        project.status,
                        project.created_at,
                        project.updated_at,
                    ),
                )
                row = cur.fetchone()
            conn.commit()

            if row is None:
                raise PsycopgError("Failed to insert project (no result returned)")

            return ProjectRead(**row)
        except PsycopgError as e:
            if conn:
                conn.rollback()
            raise PsycopgError(f"Failed to create project: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_id(self, project_id: str) -> ProjectRead | None:
        """Get project by ID.

        Args:
            project_id: Project ID to retrieve.

        Returns:
            ProjectRead if found, None otherwise.

        Raises:
            PsycopgError: If database operation fails.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, process_type, description, status, created_at, updated_at
                    FROM projects
                    WHERE id = %s
                    """,
                    (project_id,),
                )
                row = cur.fetchone()
            conn.commit()

            if row is None:
                return None

            return ProjectRead(**row)
        except PsycopgError as e:
            raise PsycopgError(f"Failed to retrieve project: {e}") from e
        finally:
            if conn:
                conn.close()

    def list_projects(self) -> list[ProjectRead]:
        """List all projects.

        Returns:
            List of all projects as ProjectRead models.

        Raises:
            PsycopgError: If database operation fails.
        """
        conn = None
        try:
            conn = get_connection(self.config)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, process_type, description, status, created_at, updated_at
                    FROM projects
                    ORDER BY created_at DESC
                    """
                )
                rows = cur.fetchall()
            conn.commit()

            return [ProjectRead(**row) for row in rows]
        except PsycopgError as e:
            raise PsycopgError(f"Failed to list projects: {e}") from e
        finally:
            if conn:
                conn.close()
