"""Tests for Requirement and RequirementLink repositories."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import (
    Requirement as RequirementORM,
    RequirementLink as RequirementLinkORM,
)
from processfoundry_ai.models.requirement import RequirementCreate
from processfoundry_ai.models.requirement_link import RequirementLinkCreate
from processfoundry_ai.repositories.requirement_link_repository import (
    RequirementLinkRepository,
)
from processfoundry_ai.repositories.requirement_repository import RequirementRepository


@pytest.fixture
def db_config() -> DatabaseConfig:
    """Provide a test database configuration."""
    return DatabaseConfig(dsn="postgresql://test:test@localhost:5432/test_db")


@pytest.fixture
def sample_requirement_create() -> RequirementCreate:
    """Provide a sample RequirementCreate model."""
    return RequirementCreate(
        id="REQ-001",
        project_id="PRJ-001",
        requirement_key="REQ-001",
        type="functional",
        statement="System must validate all required fields before submission",
        priority="must",
        status="draft",
    )


@pytest.fixture
def sample_requirement_orm() -> RequirementORM:
    """Provide a sample RequirementORM instance."""
    return RequirementORM(
        id="REQ-001",
        project_id="PRJ-001",
        requirement_key="REQ-001",
        type="functional",
        statement="System must validate all required fields before submission",
        priority="must",
        status="draft",
    )


@pytest.fixture
def sample_requirement_link_create() -> RequirementLinkCreate:
    """Provide a sample RequirementLinkCreate model."""
    return RequirementLinkCreate(
        source_requirement_id="REQ-001",
        target_id="PS-001",
        link_type="implements_step",
    )


@pytest.fixture
def sample_requirement_link_orm() -> RequirementLinkORM:
    """Provide a sample RequirementLinkORM instance."""
    return RequirementLinkORM(
        source_requirement_id="REQ-001",
        target_id="PS-001",
        link_type="implements_step",
    )


class TestRequirementRepository:
    """Test RequirementRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    def test_create_requirement_success(
        self, mock_session_context, db_config, sample_requirement_create
    ) -> None:
        """Test successful requirement creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = RequirementRepository(db_config)
        result = repo.create(sample_requirement_create)

        assert result.id == "REQ-001"
        assert result.project_id == "PRJ-001"
        assert result.requirement_key == "REQ-001"
        assert result.type == "functional"
        assert result.priority == "must"
        mock_session.add.assert_called_once()

    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    def test_get_requirement_by_id_success(
        self, mock_session_context, db_config, sample_requirement_orm
    ) -> None:
        """Test successful requirement retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_requirement_orm

        repo = RequirementRepository(db_config)
        result = repo.get_by_id("REQ-001")

        assert result is not None
        assert result.id == "REQ-001"
        assert result.statement == "System must validate all required fields before submission"

    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    def test_list_requirements_by_project(
        self, mock_session_context, db_config, sample_requirement_orm
    ) -> None:
        """Test listing requirements for a project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_requirement_orm]

        repo = RequirementRepository(db_config)
        result = repo.list_by_project("PRJ-001")

        assert len(result) == 1
        assert result[0].id == "REQ-001"

    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    def test_create_requirement_different_types(
        self, mock_session_context, db_config
    ) -> None:
        """Test creating requirements with different types."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = RequirementRepository(db_config)

        for req_type in ["functional", "non-functional", "business"]:
            req = RequirementCreate(
                id=f"REQ-{req_type}",
                project_id="PRJ-001",
                requirement_key=f"REQ-{req_type}",
                type=req_type,
                statement="Test statement",
                priority="must",
                status="draft",
            )
            result = repo.create(req)
            assert result.type == req_type

    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    def test_create_requirement_different_priorities(
        self, mock_session_context, db_config
    ) -> None:
        """Test creating requirements with different priorities."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = RequirementRepository(db_config)

        for priority in ["must", "should", "could", "wont"]:
            req = RequirementCreate(
                id=f"REQ-{priority}",
                project_id="PRJ-001",
                requirement_key=f"REQ-{priority}",
                type="functional",
                statement="Test statement",
                priority=priority,
                status="draft",
            )
            result = repo.create(req)
            assert result.priority == priority


class TestRequirementLinkRepository:
    """Test RequirementLinkRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_create_requirement_link_success(
        self, mock_session_context, db_config, sample_requirement_link_create
    ) -> None:
        """Test successful requirement link creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = RequirementLinkRepository(db_config)
        result = repo.create(sample_requirement_link_create)

        assert result.source_requirement_id == "REQ-001"
        assert result.target_id == "PS-001"
        assert result.link_type == "implements_step"

    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_get_requirement_link_by_composite_key_success(
        self, mock_session_context, db_config, sample_requirement_link_orm
    ) -> None:
        """Test successful requirement link retrieval by composite primary key."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_requirement_link_orm

        repo = RequirementLinkRepository(db_config)
        result = repo.get_by_source_target_and_link_type(
            "REQ-001", "PS-001", "implements_step"
        )

        assert result is not None
        assert result.source_requirement_id == "REQ-001"
        assert result.target_id == "PS-001"
        assert result.link_type == "implements_step"

    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_get_requirement_link_by_composite_key_not_found(
        self, mock_session_context, db_config
    ) -> None:
        """Test requirement link retrieval when the composite key is missing."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = None

        repo = RequirementLinkRepository(db_config)
        result = repo.get_by_source_target_and_link_type(
            "REQ-999", "PS-999", "missing"
        )

        assert result is None

    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_list_requirement_links_by_source(
        self, mock_session_context, db_config, sample_requirement_link_orm
    ) -> None:
        """Test listing requirement links from a source requirement."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_requirement_link_orm]

        repo = RequirementLinkRepository(db_config)
        result = repo.list_by_source_requirement("REQ-001")

        assert len(result) == 1
        assert result[0].source_requirement_id == "REQ-001"

    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_list_requirement_links_by_target(
        self, mock_session_context, db_config, sample_requirement_link_orm
    ) -> None:
        """Test listing requirement links to a target entity ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_requirement_link_orm]

        repo = RequirementLinkRepository(db_config)
        result = repo.list_by_target_id("PS-001")

        assert len(result) == 1
        assert result[0].target_id == "PS-001"
        assert result[0].link_type == "implements_step"

    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_requirement_links_to_different_entities(
        self, mock_session_context, db_config
    ) -> None:
        """Test requirement links pointing to different related entities."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = RequirementLinkRepository(db_config)

        entity_targets = [
            ("PS-001", "implements_step"),
            ("BR-001", "grounded_in_rule"),
            ("ART-001", "documented_by"),
            ("TEST-001", "verified_by"),
        ]

        links = []
        for target_id, link_type in entity_targets:
            link = RequirementLinkCreate(
                source_requirement_id="REQ-001",
                target_id=target_id,
                link_type=link_type,
            )
            links.append(link)

        assert all(link.source_requirement_id == "REQ-001" for link in links)
        assert len({link.target_id for link in links}) == 4
        assert len({link.link_type for link in links}) == 4

    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_create_requirement_link_invalid_source_fk(
        self, mock_session_context, db_config, sample_requirement_link_create
    ) -> None:
        """Test requirement link creation with invalid source_requirement_id FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Foreign key constraint violation")

        repo = RequirementLinkRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_requirement_link_create)

    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_create_requirement_link_duplicate_composite_key(
        self, mock_session_context, db_config, sample_requirement_link_create
    ) -> None:
        """Test duplicate (source_requirement_id, target_id, link_type) is rejected."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "duplicate composite primary key", None, None
        )

        repo = RequirementLinkRepository(db_config)
        with pytest.raises(IntegrityError):
            repo.create(sample_requirement_link_create)


class TestRequirementAndLinkRelationship:
    """Test Requirement and RequirementLink relationships."""

    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_link_requirement_to_multiple_entities(
        self, mock_link_session, mock_req_session, db_config
    ) -> None:
        """Test linking a requirement to multiple target entities."""
        mock_req = MagicMock()
        mock_req_session.return_value.__enter__.return_value = mock_req
        mock_req_session.return_value.__exit__.return_value = None

        mock_link = MagicMock()
        mock_link_session.return_value.__enter__.return_value = mock_link
        mock_link_session.return_value.__exit__.return_value = None

        req_repo = RequirementRepository(db_config)
        link_repo = RequirementLinkRepository(db_config)

        req = RequirementCreate(
            id="REQ-001",
            project_id="PRJ-001",
            requirement_key="REQ-001",
            type="functional",
            statement="Test requirement",
            priority="must",
            status="draft",
        )
        req_result = req_repo.create(req)

        for i in range(1, 4):
            link = RequirementLinkCreate(
                source_requirement_id=req_result.id,
                target_id=f"PS-{i:03d}",
                link_type="implements_step",
            )
            link_result = link_repo.create(link)
            assert link_result.source_requirement_id == req_result.id
            assert link_result.link_type == "implements_step"
