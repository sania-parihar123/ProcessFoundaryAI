"""Tests for Artifact and ArtifactLink repositories."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import (
    Artifact as ArtifactORM,
    ArtifactLink as ArtifactLinkORM,
)
from processfoundry_ai.models.artifact import ArtifactCreate
from processfoundry_ai.models.artifact_link import ArtifactLinkCreate
from processfoundry_ai.repositories.artifact_link_repository import ArtifactLinkRepository
from processfoundry_ai.repositories.artifact_repository import ArtifactRepository


@pytest.fixture
def db_config() -> DatabaseConfig:
    """Provide a test database configuration."""
    return DatabaseConfig(dsn="postgresql://test:test@localhost:5432/test_db")


@pytest.fixture
def sample_artifact_create() -> ArtifactCreate:
    """Provide a sample ArtifactCreate model."""
    return ArtifactCreate(
        id="ART-001",
        project_id="PRJ-001",
        artifact_type="document",
        version="1.0",
        content_json={"title": "Process Flow Diagram"},
        markdown="# Process Flow",
        status="draft",
    )


@pytest.fixture
def sample_artifact_orm() -> ArtifactORM:
    """Provide a sample ArtifactORM instance."""
    return ArtifactORM(
        id="ART-001",
        project_id="PRJ-001",
        artifact_type="document",
        version="1.0",
        content_json={"title": "Process Flow Diagram"},
        markdown="# Process Flow",
        status="draft",
    )


@pytest.fixture
def sample_artifact_link_create() -> ArtifactLinkCreate:
    """Provide a sample ArtifactLinkCreate model."""
    return ArtifactLinkCreate(
        artifact_id="ART-001",
        target_type="process_version",
        target_id="PV-001",
        link_type="describes",
    )


@pytest.fixture
def sample_artifact_link_orm() -> ArtifactLinkORM:
    """Provide a sample ArtifactLinkORM instance."""
    return ArtifactLinkORM(
        artifact_id="ART-001",
        target_type="process_version",
        target_id="PV-001",
        link_type="describes",
    )


class TestArtifactRepository:
    """Test ArtifactRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.artifact_repository.session_context")
    def test_create_artifact_success(
        self, mock_session_context, db_config, sample_artifact_create
    ) -> None:
        """Test successful artifact creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ArtifactRepository(db_config)
        result = repo.create(sample_artifact_create)

        assert result.id == "ART-001"
        assert result.project_id == "PRJ-001"
        assert result.artifact_type == "document"
        assert result.version == "1.0"
        assert result.status == "draft"
        mock_session.add.assert_called_once()

    @patch("processfoundry_ai.repositories.artifact_repository.session_context")
    def test_get_artifact_by_id_success(
        self, mock_session_context, db_config, sample_artifact_orm
    ) -> None:
        """Test successful artifact retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_artifact_orm

        repo = ArtifactRepository(db_config)
        result = repo.get_by_id("ART-001")

        assert result is not None
        assert result.id == "ART-001"
        assert result.markdown == "# Process Flow"

    @patch("processfoundry_ai.repositories.artifact_repository.session_context")
    def test_list_artifacts_by_project(
        self, mock_session_context, db_config, sample_artifact_orm
    ) -> None:
        """Test listing artifacts for a project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_artifact_orm]

        repo = ArtifactRepository(db_config)
        result = repo.list_by_project("PRJ-001")

        assert len(result) == 1
        assert result[0].id == "ART-001"

    @patch("processfoundry_ai.repositories.artifact_repository.session_context")
    def test_create_artifact_different_types(
        self, mock_session_context, db_config
    ) -> None:
        """Test creating artifacts with different types."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ArtifactRepository(db_config)

        for artifact_type in ["document", "diagram", "model", "spreadsheet"]:
            artifact = ArtifactCreate(
                id=f"ART-{artifact_type}",
                project_id="PRJ-001",
                artifact_type=artifact_type,
                version="1.0",
                content_json={"kind": artifact_type},
                markdown=None,
                status="draft",
            )
            result = repo.create(artifact)
            assert result.artifact_type == artifact_type

    @patch("processfoundry_ai.repositories.artifact_repository.session_context")
    def test_get_artifact_by_id_not_found(
        self, mock_session_context, db_config
    ) -> None:
        """Test artifact retrieval when not found."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = None

        repo = ArtifactRepository(db_config)
        result = repo.get_by_id("NONEXISTENT")

        assert result is None


class TestArtifactLinkRepository:
    """Test ArtifactLinkRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_create_artifact_link_success(
        self, mock_session_context, db_config, sample_artifact_link_create
    ) -> None:
        """Test successful artifact link creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ArtifactLinkRepository(db_config)
        result = repo.create(sample_artifact_link_create)

        assert result.artifact_id == "ART-001"
        assert result.target_type == "process_version"
        assert result.target_id == "PV-001"
        assert result.link_type == "describes"

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_get_artifact_link_by_composite_key_success(
        self, mock_session_context, db_config, sample_artifact_link_orm
    ) -> None:
        """Test successful artifact link retrieval by composite primary key."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_artifact_link_orm

        repo = ArtifactLinkRepository(db_config)
        result = repo.get_by_artifact_target_and_link_type(
            "ART-001", "process_version", "PV-001", "describes"
        )

        assert result is not None
        assert result.artifact_id == "ART-001"
        assert result.target_type == "process_version"

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_get_artifact_link_by_composite_key_not_found(
        self, mock_session_context, db_config
    ) -> None:
        """Test artifact link retrieval when the composite key is missing."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = None

        repo = ArtifactLinkRepository(db_config)
        result = repo.get_by_artifact_target_and_link_type(
            "ART-999", "process_version", "PV-999", "missing"
        )

        assert result is None

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_list_artifact_links_by_artifact(
        self, mock_session_context, db_config, sample_artifact_link_orm
    ) -> None:
        """Test listing artifact links from an artifact."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_artifact_link_orm]

        repo = ArtifactLinkRepository(db_config)
        result = repo.list_by_artifact_id("ART-001")

        assert len(result) == 1
        assert result[0].artifact_id == "ART-001"

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_list_artifact_links_by_target(
        self, mock_session_context, db_config, sample_artifact_link_orm
    ) -> None:
        """Test listing artifact links to a target entity."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_artifact_link_orm]

        repo = ArtifactLinkRepository(db_config)
        result = repo.list_by_target("process_version", "PV-001")

        assert len(result) == 1
        assert result[0].target_type == "process_version"
        assert result[0].target_id == "PV-001"

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_artifact_links_to_different_entity_types(
        self, mock_session_context, db_config
    ) -> None:
        """Test artifact links pointing to different entity types."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ArtifactLinkRepository(db_config)

        entity_targets = [
            ("process_version", "PV-001"),
            ("process_step", "PS-001"),
            ("business_rule", "BR-001"),
            ("requirement", "REQ-001"),
        ]

        links = []
        for target_type, target_id in entity_targets:
            link = ArtifactLinkCreate(
                artifact_id="ART-001",
                target_type=target_type,
                target_id=target_id,
                link_type="relates_to",
            )
            links.append(link)

        assert all(link.artifact_id == "ART-001" for link in links)
        assert len({link.target_type for link in links}) == 4

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_create_artifact_link_invalid_artifact_fk(
        self, mock_session_context, db_config, sample_artifact_link_create
    ) -> None:
        """Test artifact link creation with invalid artifact_id FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Foreign key constraint violation")

        repo = ArtifactLinkRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_artifact_link_create)

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_create_artifact_link_duplicate_composite_key(
        self, mock_session_context, db_config, sample_artifact_link_create
    ) -> None:
        """Test duplicate (artifact_id, target_type, target_id, link_type) is rejected."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "duplicate composite primary key", None, None
        )

        repo = ArtifactLinkRepository(db_config)
        with pytest.raises(IntegrityError):
            repo.create(sample_artifact_link_create)


class TestArtifactAndLinkRelationship:
    """Test Artifact and ArtifactLink relationships."""

    @patch("processfoundry_ai.repositories.artifact_repository.session_context")
    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_link_artifact_to_multiple_entities(
        self, mock_link_session, mock_art_session, db_config
    ) -> None:
        """Test linking an artifact to multiple target entities."""
        mock_art = MagicMock()
        mock_art_session.return_value.__enter__.return_value = mock_art
        mock_art_session.return_value.__exit__.return_value = None

        mock_link = MagicMock()
        mock_link_session.return_value.__enter__.return_value = mock_link
        mock_link_session.return_value.__exit__.return_value = None

        art_repo = ArtifactRepository(db_config)
        link_repo = ArtifactLinkRepository(db_config)

        artifact = ArtifactCreate(
            id="ART-001",
            project_id="PRJ-001",
            artifact_type="document",
            version="1.0",
            content_json=None,
            markdown=None,
            status="draft",
        )
        art_result = art_repo.create(artifact)

        for i in range(1, 4):
            link = ArtifactLinkCreate(
                artifact_id=art_result.id,
                target_type="process_version",
                target_id=f"PV-{i:03d}",
                link_type="describes",
            )
            link_result = link_repo.create(link)
            assert link_result.artifact_id == art_result.id

    @patch("processfoundry_ai.repositories.artifact_repository.session_context")
    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_multiple_artifacts_linked_to_same_entity(
        self, mock_link_session, mock_art_session, db_config
    ) -> None:
        """Test multiple artifacts linked to the same target entity."""
        mock_art = MagicMock()
        mock_art_session.return_value.__enter__.return_value = mock_art
        mock_art_session.return_value.__exit__.return_value = None

        mock_link = MagicMock()
        mock_link_session.return_value.__enter__.return_value = mock_link
        mock_link_session.return_value.__exit__.return_value = None

        art_repo = ArtifactRepository(db_config)
        link_repo = ArtifactLinkRepository(db_config)

        for i in range(1, 4):
            artifact = ArtifactCreate(
                id=f"ART-{i:03d}",
                project_id="PRJ-001",
                artifact_type="document",
                version="1.0",
                content_json=None,
                markdown=None,
                status="draft",
            )
            art_result = art_repo.create(artifact)

            link = ArtifactLinkCreate(
                artifact_id=art_result.id,
                target_type="process_version",
                target_id="PV-001",
                link_type="describes",
            )
            link_result = link_repo.create(link)
            assert link_result.target_id == "PV-001"
            assert link_result.target_type == "process_version"
