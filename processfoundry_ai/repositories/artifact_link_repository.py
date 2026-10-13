"""Repository for artifact link CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import ArtifactLink as ArtifactLinkORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.artifact_link import ArtifactLinkCreate, ArtifactLinkRead


class ArtifactLinkRepository:
    """Repository for artifact_links table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, artifact_link: ArtifactLinkCreate) -> ArtifactLinkRead:
        """Create a new artifact link.

        Args:
            artifact_link: Artifact link data to create (ArtifactLinkCreate model).

        Returns:
            Created artifact link as ArtifactLinkRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_artifact_link = ArtifactLinkORM(
                artifact_id=artifact_link.artifact_id,
                target_type=artifact_link.target_type,
                target_id=artifact_link.target_id,
                link_type=artifact_link.link_type,
            )
            session.add(orm_artifact_link)
            session.commit()
            session.refresh(orm_artifact_link)
            return ArtifactLinkRead.model_validate(orm_artifact_link)

    def get_by_artifact_target_and_link_type(
        self, artifact_id: str, target_type: str, target_id: str, link_type: str
    ) -> ArtifactLinkRead | None:
        """Get artifact link by composite primary key.

        Args:
            artifact_id: Source artifact ID.
            target_type: Type of target entity.
            target_id: Target entity ID.
            link_type: Relationship type.

        Returns:
            ArtifactLinkRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ArtifactLinkORM).where(
                (ArtifactLinkORM.artifact_id == artifact_id)
                & (ArtifactLinkORM.target_type == target_type)
                & (ArtifactLinkORM.target_id == target_id)
                & (ArtifactLinkORM.link_type == link_type)
            )
            orm_artifact_link = session.scalars(stmt).first()

            if orm_artifact_link is None:
                return None

            return ArtifactLinkRead.model_validate(orm_artifact_link)

    def list_by_artifact_id(self, artifact_id: str) -> list[ArtifactLinkRead]:
        """List all links from a source artifact.

        Args:
            artifact_id: Source artifact ID to filter by.

        Returns:
            List of artifact links as ArtifactLinkRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ArtifactLinkORM).where(
                ArtifactLinkORM.artifact_id == artifact_id
            )
            orm_artifact_links = session.scalars(stmt).all()
            return [ArtifactLinkRead.model_validate(al) for al in orm_artifact_links]

    def list_by_target(
        self, target_type: str, target_id: str
    ) -> list[ArtifactLinkRead]:
        """List all artifact links pointing to a target entity.

        Args:
            target_type: Type of target entity.
            target_id: ID of target entity.

        Returns:
            List of artifact links as ArtifactLinkRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ArtifactLinkORM).where(
                (ArtifactLinkORM.target_type == target_type)
                & (ArtifactLinkORM.target_id == target_id)
            )
            orm_artifact_links = session.scalars(stmt).all()
            return [ArtifactLinkRead.model_validate(al) for al in orm_artifact_links]
