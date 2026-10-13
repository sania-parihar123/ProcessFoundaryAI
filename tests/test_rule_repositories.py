"""Tests for BusinessRule and RuleEvidence repositories."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import (
    BusinessRule as BusinessRuleORM,
    RuleEvidence as RuleEvidenceORM,
)
from processfoundry_ai.models.business_rule import BusinessRuleCreate
from processfoundry_ai.models.rule_evidence import RuleEvidenceCreate
from processfoundry_ai.repositories.business_rule_repository import (
    BusinessRuleRepository,
)
from processfoundry_ai.repositories.rule_evidence_repository import (
    RuleEvidenceRepository,
)


@pytest.fixture
def db_config() -> DatabaseConfig:
    """Provide a test database configuration."""
    return DatabaseConfig(dsn="postgresql://test:test@localhost:5432/test_db")


@pytest.fixture
def sample_business_rule_create() -> BusinessRuleCreate:
    """Provide a sample BusinessRuleCreate model."""
    return BusinessRuleCreate(
        id="BR-001",
        project_id="PRJ-001",
        rule_key="BR-001",
        description="Applicants must have GPA >= 3.0",
        condition_json={"gpa": {"min": 3.0}},
        status="candidate",
    )


@pytest.fixture
def sample_business_rule_orm() -> BusinessRuleORM:
    """Provide a sample BusinessRuleORM instance."""
    return BusinessRuleORM(
        id="BR-001",
        project_id="PRJ-001",
        rule_key="BR-001",
        description="Applicants must have GPA >= 3.0",
        condition_json={"gpa": {"min": 3.0}},
        status="candidate",
    )


@pytest.fixture
def sample_rule_evidence_create() -> RuleEvidenceCreate:
    """Provide a sample RuleEvidenceCreate model."""
    return RuleEvidenceCreate(
        rule_id="BR-001",
        evidence_id="EVD-001",
    )


@pytest.fixture
def sample_rule_evidence_orm() -> RuleEvidenceORM:
    """Provide a sample RuleEvidenceORM instance."""
    return RuleEvidenceORM(
        rule_id="BR-001",
        evidence_id="EVD-001",
    )


class TestBusinessRuleRepository:
    """Test BusinessRuleRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    def test_create_business_rule_success(
        self, mock_session_context, db_config, sample_business_rule_create
    ) -> None:
        """Test successful business rule creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = BusinessRuleRepository(db_config)
        result = repo.create(sample_business_rule_create)

        assert result.id == "BR-001"
        assert result.project_id == "PRJ-001"
        assert result.rule_key == "BR-001"
        assert result.description == "Applicants must have GPA >= 3.0"
        assert result.status == "candidate"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    def test_get_business_rule_by_id_success(
        self, mock_session_context, db_config, sample_business_rule_orm
    ) -> None:
        """Test successful business rule retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_business_rule_orm

        repo = BusinessRuleRepository(db_config)
        result = repo.get_by_id("BR-001")

        assert result is not None
        assert result.id == "BR-001"
        assert result.rule_key == "BR-001"
        assert result.description == "Applicants must have GPA >= 3.0"

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    def test_list_business_rules_by_project(
        self, mock_session_context, db_config, sample_business_rule_orm
    ) -> None:
        """Test listing business rules for a project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_business_rule_orm]

        repo = BusinessRuleRepository(db_config)
        result = repo.list_by_project("PRJ-001")

        assert len(result) == 1
        assert result[0].id == "BR-001"

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    def test_create_business_rule_invalid_project_fk(
        self, mock_session_context, db_config, sample_business_rule_create
    ) -> None:
        """Test business rule creation with invalid project_id FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Foreign key constraint violation")

        repo = BusinessRuleRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_business_rule_create)

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    def test_list_business_rules_empty(self, mock_session_context, db_config) -> None:
        """Test listing business rules when none exist."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = []

        repo = BusinessRuleRepository(db_config)
        result = repo.list_by_project("PRJ-999")

        assert result == []


class TestRuleEvidenceRepository:
    """Test RuleEvidenceRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_create_rule_evidence_success(
        self, mock_session_context, db_config, sample_rule_evidence_create
    ) -> None:
        """Test successful rule evidence link creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = RuleEvidenceRepository(db_config)
        result = repo.create(sample_rule_evidence_create)

        assert result.rule_id == "BR-001"
        assert result.evidence_id == "EVD-001"
        mock_session.add.assert_called_once()

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_get_rule_evidence_by_composite_key_success(
        self, mock_session_context, db_config, sample_rule_evidence_orm
    ) -> None:
        """Test successful rule evidence retrieval by composite key."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_rule_evidence_orm

        repo = RuleEvidenceRepository(db_config)
        result = repo.get_by_rule_and_evidence("BR-001", "EVD-001")

        assert result is not None
        assert result.rule_id == "BR-001"
        assert result.evidence_id == "EVD-001"

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_get_rule_evidence_by_composite_key_not_found(
        self, mock_session_context, db_config
    ) -> None:
        """Test rule evidence retrieval when the composite key is missing."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = None

        repo = RuleEvidenceRepository(db_config)
        result = repo.get_by_rule_and_evidence("BR-999", "EVD-999")

        assert result is None

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_list_rule_evidence_by_rule_id(
        self, mock_session_context, db_config, sample_rule_evidence_orm
    ) -> None:
        """Test listing evidence links for a business rule."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_rule_evidence_orm]

        repo = RuleEvidenceRepository(db_config)
        result = repo.list_by_rule_id("BR-001")

        assert len(result) == 1
        assert result[0].rule_id == "BR-001"

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_list_rule_evidence_by_evidence_id(
        self, mock_session_context, db_config, sample_rule_evidence_orm
    ) -> None:
        """Test listing rule links for an evidence item."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_rule_evidence_orm]

        repo = RuleEvidenceRepository(db_config)
        result = repo.list_by_evidence_id("EVD-001")

        assert len(result) == 1
        assert result[0].evidence_id == "EVD-001"

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_create_rule_evidence_invalid_rule_fk(
        self, mock_session_context, db_config, sample_rule_evidence_create
    ) -> None:
        """Test rule evidence creation with invalid rule_id FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Foreign key constraint violation")

        repo = RuleEvidenceRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_rule_evidence_create)

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_create_rule_evidence_invalid_evidence_fk(
        self, mock_session_context, db_config
    ) -> None:
        """Test rule evidence creation with invalid evidence_id FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Foreign key constraint violation")

        repo = RuleEvidenceRepository(db_config)
        re = RuleEvidenceCreate(
            rule_id="BR-001",
            evidence_id="EVD-999",
        )
        with pytest.raises(SQLAlchemyError):
            repo.create(re)

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_create_rule_evidence_duplicate_composite_key(
        self, mock_session_context, db_config, sample_rule_evidence_create
    ) -> None:
        """Test duplicate (rule_id, evidence_id) is rejected."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "duplicate composite primary key", None, None
        )

        repo = RuleEvidenceRepository(db_config)
        with pytest.raises(IntegrityError):
            repo.create(sample_rule_evidence_create)

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_multiple_evidence_items_for_one_rule(
        self, mock_session_context, db_config
    ) -> None:
        """Test linking multiple evidence items to one business rule."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        evidence_items = [
            RuleEvidenceORM(rule_id="BR-001", evidence_id="EVD-001"),
            RuleEvidenceORM(rule_id="BR-001", evidence_id="EVD-002"),
            RuleEvidenceORM(rule_id="BR-001", evidence_id="EVD-003"),
        ]
        mock_session.scalars.return_value.all.return_value = evidence_items

        repo = RuleEvidenceRepository(db_config)
        result = repo.list_by_rule_id("BR-001")

        assert len(result) == 3
        assert all(item.rule_id == "BR-001" for item in result)


class TestBusinessRuleAndEvidenceRelationship:
    """Test BusinessRule and RuleEvidence relationships."""

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_create_rule_then_evidence_links(
        self, mock_evidence_session, mock_rule_session, db_config
    ) -> None:
        """Test creating a business rule and linking evidence to it."""
        mock_rule = MagicMock()
        mock_rule_session.return_value.__enter__.return_value = mock_rule
        mock_rule_session.return_value.__exit__.return_value = None

        mock_evidence = MagicMock()
        mock_evidence_session.return_value.__enter__.return_value = mock_evidence
        mock_evidence_session.return_value.__exit__.return_value = None

        rule_repo = BusinessRuleRepository(db_config)
        evidence_repo = RuleEvidenceRepository(db_config)

        rule = BusinessRuleCreate(
            id="BR-001",
            project_id="PRJ-001",
            rule_key="BR-001",
            description="Test rule description",
            condition_json=None,
            status="candidate",
        )
        rule_result = rule_repo.create(rule)

        for i in range(1, 4):
            evidence_link = RuleEvidenceCreate(
                rule_id=rule_result.id,
                evidence_id=f"EVD-{i:03d}",
            )
            evidence_result = evidence_repo.create(evidence_link)
            assert evidence_result.rule_id == rule_result.id
