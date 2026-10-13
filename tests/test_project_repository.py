"""Tests for the project repository with SQLAlchemy ORM."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.project import ProjectCreate, ProjectRead
from processfoundry_ai.repositories.project_repository import ProjectRepository
from processfoundry_ai.database.models import Project as ProjectORM


@pytest.fixture
def db_config() -> DatabaseConfig:
    """Provide a test database configuration."""
    return DatabaseConfig(dsn="postgresql://test:test@localhost:5432/test_db")


@pytest.fixture
def sample_project_create() -> ProjectCreate:
    """Provide a sample ProjectCreate model."""
    now = datetime.now(timezone.utc)
    return ProjectCreate(
        id="PRJ-001",
        name="Test Project",
        process_type="admissions",
        description="A test project for admissions process",
        status="draft",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_project_orm() -> ProjectORM:
    """Provide a sample ProjectORM instance."""
    now = datetime.now(timezone.utc)
    project = ProjectORM(
        id="PRJ-001",
        name="Test Project",
        process_type="admissions",
        description="A test project for admissions process",
        status="draft",
        created_at=now,
        updated_at=now,
    )
    return project


class TestProjectRepositoryCreate:
    """Test ProjectRepository.create() method."""

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_create_project_success(
        self, mock_session_context, db_config, sample_project_create
    ) -> None:
        """Test successful project creation."""
        # Setup mock session context
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        # Execute
        repo = ProjectRepository(db_config)
        result = repo.create(sample_project_create)

        # Assert
        assert result.id == "PRJ-001"
        assert result.name == "Test Project"
        assert result.process_type == "admissions"
        assert result.status == "draft"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_create_project_database_error(
        self, mock_session_context, db_config, sample_project_create
    ) -> None:
        """Test project creation with database error."""
        # Setup mock to raise error
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Database error")

        # Execute and assert
        repo = ProjectRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_project_create)

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_create_closes_session_on_error(
        self, mock_session_context, db_config, sample_project_create
    ) -> None:
        """Test that session is closed even on error via context manager."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Error")

        # Execute
        repo = ProjectRepository(db_config)
        try:
            repo.create(sample_project_create)
        except SQLAlchemyError:
            pass

        # Assert context manager cleanup is called
        mock_session_context.return_value.__exit__.assert_called()



class TestProjectRepositoryGetById:
    """Test ProjectRepository.get_by_id() method."""

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_get_by_id_success(
        self, mock_session_context, db_config, sample_project_orm
    ) -> None:
        """Test successful project retrieval by ID."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        # Mock scalars().first() chain
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.first.return_value = sample_project_orm

        # Execute
        repo = ProjectRepository(db_config)
        result = repo.get_by_id("PRJ-001")

        # Assert
        assert result is not None
        assert result.id == "PRJ-001"
        assert result.name == "Test Project"
        mock_session.scalars.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_get_by_id_not_found(self, mock_session_context, db_config) -> None:
        """Test project retrieval when project does not exist."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.first.return_value = None

        # Execute
        repo = ProjectRepository(db_config)
        result = repo.get_by_id("NONEXISTENT")

        # Assert
        assert result is None

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_get_by_id_database_error(self, mock_session_context, db_config) -> None:
        """Test project retrieval with database error."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.scalars.side_effect = SQLAlchemyError("Connection failed")

        # Execute and assert
        repo = ProjectRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.get_by_id("PRJ-001")



class TestProjectRepositoryListProjects:
    """Test ProjectRepository.list_projects() method."""

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_list_projects_success(self, mock_session_context, db_config) -> None:
        """Test successful listing of projects."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        now = datetime.now(timezone.utc)
        project1 = ProjectORM(
            id="PRJ-001",
            name="Project 1",
            process_type="admissions",
            description="First project",
            status="active",
            created_at=now,
            updated_at=now,
        )
        project2 = ProjectORM(
            id="PRJ-002",
            name="Project 2",
            process_type="enrollment",
            description="Second project",
            status="draft",
            created_at=now,
            updated_at=now,
        )

        # Mock scalars().all() chain
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = [project1, project2]

        # Execute
        repo = ProjectRepository(db_config)
        results = repo.list_projects()

        # Assert
        assert len(results) == 2
        assert results[0].id == "PRJ-001"
        assert results[1].id == "PRJ-002"
        assert all(isinstance(r, ProjectRead) for r in results)
        mock_session.scalars.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_list_projects_empty(self, mock_session_context, db_config) -> None:
        """Test listing projects when none exist."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = []

        # Execute
        repo = ProjectRepository(db_config)
        results = repo.list_projects()

        # Assert
        assert results == []

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_list_projects_database_error(self, mock_session_context, db_config) -> None:
        """Test listing projects with database error."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.scalars.side_effect = SQLAlchemyError("Connection failed")

        # Execute and assert
        repo = ProjectRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.list_projects()



class TestProjectRepositoryConnectionHandling:
    """Test connection and resource handling."""

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_connection_closed_on_success(
        self, mock_session_context, db_config, sample_project_create
    ) -> None:
        """Test that sessions are closed on successful operations."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ProjectRepository(db_config)
        repo.create(sample_project_create)

        mock_session_context.return_value.__enter__.assert_called_once()
        mock_session_context.return_value.__exit__.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.session_context")
    def test_connection_closed_on_error(
        self, mock_session_context, db_config, sample_project_create
    ) -> None:
        """Test that sessions are closed even when errors occur."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Query failed")

        repo = ProjectRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_project_create)

        mock_session_context.return_value.__exit__.assert_called_once()

    @patch("processfoundry_ai.database.session.get_session")
    def test_rollback_on_error(
        self, mock_get_session, db_config, sample_project_create
    ) -> None:
        """Test that rollback is called on database errors."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Constraint violation")

        repo = ProjectRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_project_create)

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
