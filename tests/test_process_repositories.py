"""Tests for ProcessVersion and ProcessStep repositories."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import (
    ProcessStep as ProcessStepORM,
    ProcessVersion as ProcessVersionORM,
)
from processfoundry_ai.models.process_step import ProcessStepCreate, ProcessStepRead
from processfoundry_ai.models.process_version import (
    ProcessVersionCreate,
    ProcessVersionRead,
)
from processfoundry_ai.repositories.process_step_repository import (
    ProcessStepRepository,
)
from processfoundry_ai.repositories.process_version_repository import (
    ProcessVersionRepository,
)


@pytest.fixture
def db_config() -> DatabaseConfig:
    """Provide a test database configuration."""
    return DatabaseConfig(dsn="postgresql://test:test@localhost:5432/test_db")


@pytest.fixture
def sample_process_version_create() -> ProcessVersionCreate:
    """Provide a sample ProcessVersionCreate model."""
    return ProcessVersionCreate(
        id="PV-001",
        project_id="PRJ-001",
        version="1.0",
        as_is_json=None,
        to_be_json=None,
        status="draft",
    )


@pytest.fixture
def sample_process_version_orm() -> ProcessVersionORM:
    """Provide a sample ProcessVersionORM instance."""
    return ProcessVersionORM(
        id="PV-001",
        project_id="PRJ-001",
        version="1.0",
        as_is_json=None,
        to_be_json=None,
        status="draft",
    )


@pytest.fixture
def sample_process_step_create() -> ProcessStepCreate:
    """Provide a sample ProcessStepCreate model."""
    return ProcessStepCreate(
        id="PS-001",
        process_version_id="PV-001",
        step_key="STEP-001",
        name="Submit Request",
        actor="Student",
        step_type="task",
        sequence=1,
    )


@pytest.fixture
def sample_process_step_orm() -> ProcessStepORM:
    """Provide a sample ProcessStepORM instance."""
    return ProcessStepORM(
        id="PS-001",
        process_version_id="PV-001",
        step_key="STEP-001",
        name="Submit Request",
        actor="Student",
        step_type="task",
        sequence=1,
    )


class TestProcessVersionRepository:
    """Test ProcessVersionRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    def test_create_process_version_success(
        self, mock_session_context, db_config, sample_process_version_create
    ) -> None:
        """Test successful process version creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ProcessVersionRepository(db_config)
        result = repo.create(sample_process_version_create)

        assert result.id == "PV-001"
        assert result.project_id == "PRJ-001"
        assert result.version == "1.0"
        assert result.status == "draft"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    def test_create_process_version_database_error(
        self, mock_session_context, db_config, sample_process_version_create
    ) -> None:
        """Test process version creation with database error."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Database error")

        repo = ProcessVersionRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_process_version_create)

    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    def test_get_process_version_by_id_success(
        self, mock_session_context, db_config, sample_process_version_orm
    ) -> None:
        """Test successful process version retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_process_version_orm

        repo = ProcessVersionRepository(db_config)
        result = repo.get_by_id("PV-001")

        assert result is not None
        assert result.id == "PV-001"

    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    def test_get_process_version_by_id_not_found(
        self, mock_session_context, db_config
    ) -> None:
        """Test process version retrieval when not found."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = None

        repo = ProcessVersionRepository(db_config)
        result = repo.get_by_id("PV-999")

        assert result is None

    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    def test_list_process_versions_by_project(
        self, mock_session_context, db_config, sample_process_version_orm
    ) -> None:
        """Test listing process versions for a project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_process_version_orm]

        repo = ProcessVersionRepository(db_config)
        result = repo.list_by_project("PRJ-001")

        assert len(result) == 1
        assert result[0].id == "PV-001"

    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    def test_list_process_versions_empty(
        self, mock_session_context, db_config
    ) -> None:
        """Test listing process versions when none exist."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = []

        repo = ProcessVersionRepository(db_config)
        result = repo.list_by_project("PRJ-999")

        assert result == []


class TestProcessStepRepository:
    """Test ProcessStepRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    def test_create_process_step_success(
        self, mock_session_context, db_config, sample_process_step_create
    ) -> None:
        """Test successful process step creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ProcessStepRepository(db_config)
        result = repo.create(sample_process_step_create)

        assert result.id == "PS-001"
        assert result.process_version_id == "PV-001"
        assert result.sequence == 1
        mock_session.add.assert_called_once()

    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    def test_get_process_step_by_id_success(
        self, mock_session_context, db_config, sample_process_step_orm
    ) -> None:
        """Test successful process step retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_process_step_orm

        repo = ProcessStepRepository(db_config)
        result = repo.get_by_id("PS-001")

        assert result is not None
        assert result.id == "PS-001"

    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    def test_list_process_steps_by_version(
        self, mock_session_context, db_config, sample_process_step_orm
    ) -> None:
        """Test listing process steps for a process version."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_process_step_orm]

        repo = ProcessStepRepository(db_config)
        result = repo.list_by_process_version("PV-001")

        assert len(result) == 1
        assert result[0].sequence == 1

    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    def test_list_process_steps_ordered_by_sequence(
        self, mock_session_context, db_config
    ) -> None:
        """Test that process steps are ordered by sequence."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        # Create steps with different sequences
        step1 = ProcessStepORM(
            id="PS-001",
            process_version_id="PV-001",
            step_key="STEP-001",
            name="First",
            actor="Student",
            step_type="task",
            sequence=1,
        )
        step2 = ProcessStepORM(
            id="PS-002",
            process_version_id="PV-001",
            step_key="STEP-002",
            name="Second",
            actor="Advisor",
            step_type="review",
            sequence=2,
        )
        mock_session.scalars.return_value.all.return_value = [step1, step2]

        repo = ProcessStepRepository(db_config)
        result = repo.list_by_process_version("PV-001")

        assert result[0].sequence == 1
        assert result[1].sequence == 2

    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    def test_create_process_step_foreign_key_error(
        self, mock_session_context, db_config, sample_process_step_create
    ) -> None:
        """Test process step creation with invalid process_version_id FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Foreign key constraint violation")

        repo = ProcessStepRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_process_step_create)


class TestProcessVersionAndStepRelationship:
    """Test ProcessVersion and ProcessStep relationships."""

    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    def test_create_version_then_steps(
        self, mock_step_session, mock_version_session, db_config
    ) -> None:
        """Test creating a process version and its steps."""
        # Setup version creation
        mock_version = MagicMock()
        mock_version_session.return_value.__enter__.return_value = mock_version
        mock_version_session.return_value.__exit__.return_value = None

        # Setup step creation
        mock_step = MagicMock()
        mock_step_session.return_value.__enter__.return_value = mock_step
        mock_step_session.return_value.__exit__.return_value = None

        version_repo = ProcessVersionRepository(db_config)
        step_repo = ProcessStepRepository(db_config)

        version = ProcessVersionCreate(
            id="PV-001",
            project_id="PRJ-001",
            version="1.0",
            as_is_json=None,
            to_be_json=None,
            status="draft",
        )
        version_result = version_repo.create(version)

        step = ProcessStepCreate(
            id="PS-001",
            process_version_id=version_result.id,
            step_key="STEP-001",
            name="Step 1",
            actor="Student",
            step_type="task",
            sequence=1,
        )
        step_result = step_repo.create(step)

        assert version_result.id == step_result.process_version_id
