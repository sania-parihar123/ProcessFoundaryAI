"""Repository for artifact CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import Artifact as ArtifactORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.artifact import ArtifactCreate, ArtifactRead


class ArtifactRepository:
    """Repository for artifacts table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, artifact: ArtifactCreate) -> ArtifactRead:
        """Create a new artifact.

        Args:
            artifact: Artifact data to create (ArtifactCreate model).

        Returns:
            Created artifact as ArtifactRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_artifact = ArtifactORM(
                id=artifact.id,
                project_id=artifact.project_id,
                artifact_type=artifact.artifact_type,
                version=artifact.version,
                content_json=artifact.content_json,
                markdown=artifact.markdown,
                status=artifact.status,
            )
            session.add(orm_artifact)
            session.commit()
            session.refresh(orm_artifact)
            return ArtifactRead.model_validate(orm_artifact)

    def get_by_id(self, artifact_id: str) -> ArtifactRead | None:
        """Get artifact by ID.

        Args:
            artifact_id: Artifact ID to retrieve.

        Returns:
            ArtifactRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ArtifactORM).where(ArtifactORM.id == artifact_id)
            orm_artifact = session.scalars(stmt).first()

            if orm_artifact is None:
                return None

            return ArtifactRead.model_validate(orm_artifact)

    def list_by_project(self, project_id: str) -> list[ArtifactRead]:
        """List all artifacts for a project.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of artifacts for the project as ArtifactRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ArtifactORM).where(ArtifactORM.project_id == project_id)
            orm_artifacts = session.scalars(stmt).all()
            return [ArtifactRead.model_validate(a) for a in orm_artifacts]

    def update(self, artifact_id: str, updates: dict) -> ArtifactRead | None:
        """Update an artifact by ID.

        Args:
            artifact_id: Artifact ID to update.
            updates: Dictionary of fields and values to update.

        Returns:
            Updated artifact as ArtifactRead model, or None if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_artifact = session.get(ArtifactORM, artifact_id)
            if orm_artifact is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_artifact, field):
                    setattr(orm_artifact, field, value)

            session.commit()
            session.refresh(orm_artifact)
            return ArtifactRead.model_validate(orm_artifact)

    def delete(self, artifact_id: str) -> bool:
        """Delete an artifact by ID.

        Args:
            artifact_id: Artifact ID to delete.

        Returns:
            True if deleted, False if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_artifact = session.get(ArtifactORM, artifact_id)
            if orm_artifact is None:
                return False
            session.delete(orm_artifact)
            session.commit()
            return True
