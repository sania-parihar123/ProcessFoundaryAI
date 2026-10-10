"""Tests for the project repository."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from psycopg import Error as PsycopgError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.project import ProjectCreate, ProjectRead
from processfoundry_ai.repositories.project_repository import ProjectRepository


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
def sample_project_read() -> ProjectRead:
    """Provide a sample ProjectRead model."""
    now = datetime.now(timezone.utc)
    return ProjectRead(
        id="PRJ-001",
        name="Test Project",
        process_type="admissions",
        description="A test project for admissions process",
        status="draft",
        created_at=now,
        updated_at=now,
    )


class TestProjectRepositoryCreate:
    """Test ProjectRepository.create() method."""

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_create_project_success(
        self, mock_get_connection, db_config, sample_project_create
    ) -> None:
        """Test successful project creation."""
        # Setup mock connection and cursor
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock the RETURNING clause result
        now = datetime.now(timezone.utc)
        mock_cursor.fetchone.return_value = {
            "id": "PRJ-001",
            "name": "Test Project",
            "process_type": "admissions",
            "description": "A test project for admissions process",
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        }

        # Execute
        repo = ProjectRepository(db_config)
        result = repo.create(sample_project_create)

        # Assert
        assert result.id == "PRJ-001"
        assert result.name == "Test Project"
        assert result.process_type == "admissions"
        assert result.status == "draft"
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_create_project_database_error(
        self, mock_get_connection, db_config, sample_project_create
    ) -> None:
        """Test project creation with database error."""
        # Setup mock to raise error
        mock_get_connection.side_effect = PsycopgError("Connection failed")

        # Execute and assert
        repo = ProjectRepository(db_config)
        with pytest.raises(PsycopgError, match="Failed to create project"):
            repo.create(sample_project_create)

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_create_project_no_result(
        self, mock_get_connection, db_config, sample_project_create
    ) -> None:
        """Test project creation when database returns no result."""
        # Setup mock
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # No result

        # Execute and assert
        repo = ProjectRepository(db_config)
        with pytest.raises(PsycopgError, match="no result returned"):
            repo.create(sample_project_create)

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_create_project_uses_parameterized_query(
        self, mock_get_connection, db_config, sample_project_create
    ) -> None:
        """Test that create uses parameterized SQL queries."""
        # Setup mock
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        now = datetime.now(timezone.utc)
        mock_cursor.fetchone.return_value = {
            "id": sample_project_create.id,
            "name": sample_project_create.name,
            "process_type": sample_project_create.process_type,
            "description": sample_project_create.description,
            "status": sample_project_create.status,
            "created_at": now,
            "updated_at": now,
        }

        # Execute
        repo = ProjectRepository(db_config)
        repo.create(sample_project_create)

        # Assert - verify execute was called with parameterized query
        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args
        # First arg should be SQL string, second should be tuple of params
        assert isinstance(args[0][0], str)
        assert "%s" in args[0][0]  # Parameterized query
        assert isinstance(args[0][1], tuple)
        assert args[0][1][0] == sample_project_create.id


class TestProjectRepositoryGetById:
    """Test ProjectRepository.get_by_id() method."""

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_get_by_id_success(
        self, mock_get_connection, db_config, sample_project_read
    ) -> None:
        """Test successful project retrieval by ID."""
        # Setup mock
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": sample_project_read.id,
            "name": sample_project_read.name,
            "process_type": sample_project_read.process_type,
            "description": sample_project_read.description,
            "status": sample_project_read.status,
            "created_at": sample_project_read.created_at,
            "updated_at": sample_project_read.updated_at,
        }

        # Execute
        repo = ProjectRepository(db_config)
        result = repo.get_by_id("PRJ-001")

        # Assert
        assert result is not None
        assert result.id == "PRJ-001"
        assert result.name == "Test Project"
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_get_by_id_not_found(self, mock_get_connection, db_config) -> None:
        """Test project retrieval when project does not exist."""
        # Setup mock
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        # Execute
        repo = ProjectRepository(db_config)
        result = repo.get_by_id("NONEXISTENT")

        # Assert
        assert result is None
        mock_conn.close.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_get_by_id_database_error(self, mock_get_connection, db_config) -> None:
        """Test project retrieval with database error."""
        # Setup mock
        mock_get_connection.side_effect = PsycopgError("Connection failed")

        # Execute and assert
        repo = ProjectRepository(db_config)
        with pytest.raises(PsycopgError, match="Failed to retrieve project"):
            repo.get_by_id("PRJ-001")

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_get_by_id_uses_parameterized_query(
        self, mock_get_connection, db_config, sample_project_read
    ) -> None:
        """Test that get_by_id uses parameterized SQL queries."""
        # Setup mock
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": "PRJ-001",
            "name": "Test",
            "process_type": "test",
            "description": "test",
            "status": "draft",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        # Execute
        repo = ProjectRepository(db_config)
        repo.get_by_id("PRJ-001")

        # Assert - verify parameterized query
        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args
        assert "%s" in args[0][0]  # Parameterized
        assert args[0][1][0] == "PRJ-001"


class TestProjectRepositoryListProjects:
    """Test ProjectRepository.list_projects() method."""

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_list_projects_success(self, mock_get_connection, db_config) -> None:
        """Test successful listing of projects."""
        # Setup mock
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        now = datetime.now(timezone.utc)
        mock_cursor.fetchall.return_value = [
            {
                "id": "PRJ-001",
                "name": "Project 1",
                "process_type": "admissions",
                "description": "First project",
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "PRJ-002",
                "name": "Project 2",
                "process_type": "enrollment",
                "description": "Second project",
                "status": "draft",
                "created_at": now,
                "updated_at": now,
            },
        ]

        # Execute
        repo = ProjectRepository(db_config)
        results = repo.list_projects()

        # Assert
        assert len(results) == 2
        assert results[0].id == "PRJ-001"
        assert results[1].id == "PRJ-002"
        assert all(isinstance(r, ProjectRead) for r in results)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_list_projects_empty(self, mock_get_connection, db_config) -> None:
        """Test listing projects when none exist."""
        # Setup mock
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        # Execute
        repo = ProjectRepository(db_config)
        results = repo.list_projects()

        # Assert
        assert results == []
        mock_conn.close.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_list_projects_database_error(self, mock_get_connection, db_config) -> None:
        """Test listing projects with database error."""
        # Setup mock
        mock_get_connection.side_effect = PsycopgError("Connection failed")

        # Execute and assert
        repo = ProjectRepository(db_config)
        with pytest.raises(PsycopgError, match="Failed to list projects"):
            repo.list_projects()

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_list_projects_ordered_by_created_at_desc(
        self, mock_get_connection, db_config
    ) -> None:
        """Test that list_projects orders by created_at DESC."""
        # Setup mock
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        # Execute
        repo = ProjectRepository(db_config)
        repo.list_projects()

        # Assert - verify query includes ORDER BY created_at DESC
        mock_cursor.execute.assert_called_once()
        sql = mock_cursor.execute.call_args[0][0]
        assert "ORDER BY created_at DESC" in sql


class TestProjectRepositoryConnectionHandling:
    """Test connection and resource handling."""

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_connection_closed_on_success(
        self, mock_get_connection, db_config, sample_project_create
    ) -> None:
        """Test that connections are closed on successful operations."""
        # Setup mock
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        now = datetime.now(timezone.utc)
        mock_cursor.fetchone.return_value = {
            "id": "PRJ-001",
            "name": "Test",
            "process_type": "test",
            "description": "test",
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        }

        # Execute
        repo = ProjectRepository(db_config)
        repo.create(sample_project_create)

        # Assert
        mock_conn.close.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_connection_closed_on_error(
        self, mock_get_connection, db_config, sample_project_create
    ) -> None:
        """Test that connections are closed even when errors occur."""
        # Setup mock to raise error during execute
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = PsycopgError("Query failed")

        # Execute and catch error
        repo = ProjectRepository(db_config)
        try:
            repo.create(sample_project_create)
        except PsycopgError:
            pass

        # Assert connection was closed and rollback was called
        mock_conn.close.assert_called_once()
        mock_conn.rollback.assert_called_once()

    @patch("processfoundry_ai.repositories.project_repository.get_connection")
    def test_rollback_on_error(
        self, mock_get_connection, db_config, sample_project_create
    ) -> None:
        """Test that rollback is called on database errors."""
        # Setup mock
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = PsycopgError("Constraint violation")

        # Execute
        repo = ProjectRepository(db_config)
        with pytest.raises(PsycopgError):
            repo.create(sample_project_create)

        # Assert
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()
