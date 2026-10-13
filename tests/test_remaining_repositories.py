"""Tests for ClarificationItem, TestCase, Approval, and AgentRun repositories."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import (
    Approval as ApprovalORM,
    AgentRun as AgentRunORM,
    ClarificationItem as ClarificationItemORM,
    TestCase as TestCaseORM,
)
from processfoundry_ai.models.approval import ApprovalCreate
from processfoundry_ai.models.agent_run import AgentRunCreate
from processfoundry_ai.models.clarification_item import ClarificationItemCreate
from processfoundry_ai.models.test_case import TestCaseCreate
from processfoundry_ai.repositories.approval_repository import ApprovalRepository
from processfoundry_ai.repositories.agent_run_repository import AgentRunRepository
from processfoundry_ai.repositories.clarification_item_repository import (
    ClarificationItemRepository,
)
from processfoundry_ai.repositories.test_case_repository import TestCaseRepository


@pytest.fixture
def db_config() -> DatabaseConfig:
    """Provide a test database configuration."""
    return DatabaseConfig(dsn="postgresql://test:test@localhost:5432/test_db")


@pytest.fixture
def sample_clarification_create() -> ClarificationItemCreate:
    """Provide a sample ClarificationItemCreate model."""
    return ClarificationItemCreate(
        id="CL-001",
        project_id="PRJ-001",
        question="What are the exact approval workflow steps required?",
        reason="The source documents omit the approval sequence.",
        status="open",
        answer=None,
        answered_by=None,
    )


@pytest.fixture
def sample_clarification_orm() -> ClarificationItemORM:
    """Provide a sample ClarificationItemORM instance."""
    return ClarificationItemORM(
        id="CL-001",
        project_id="PRJ-001",
        question="What are the exact approval workflow steps required?",
        reason="The source documents omit the approval sequence.",
        status="open",
        answer=None,
        answered_by=None,
    )


@pytest.fixture
def sample_test_case_create() -> TestCaseCreate:
    """Provide a sample TestCaseCreate model."""
    return TestCaseCreate(
        id="TEST-001",
        project_id="PRJ-001",
        test_key="TEST-001",
        requirement_id="REQ-001",
        scenario="Valid document submission",
        expected_result="Document accepted and stored in system",
    )


@pytest.fixture
def sample_test_case_orm() -> TestCaseORM:
    """Provide a sample TestCaseORM instance."""
    return TestCaseORM(
        id="TEST-001",
        project_id="PRJ-001",
        test_key="TEST-001",
        requirement_id="REQ-001",
        scenario="Valid document submission",
        expected_result="Document accepted and stored in system",
    )


@pytest.fixture
def sample_approval_create() -> ApprovalCreate:
    """Provide a sample ApprovalCreate model."""
    now = datetime.now(timezone.utc)
    return ApprovalCreate(
        id="APP-001",
        project_id="PRJ-001",
        target_type="process_version",
        target_id="PV-001",
        decision="approved",
        reviewer="John Doe",
        timestamp=now,
        comment="Awaiting stakeholder review",
    )


@pytest.fixture
def sample_approval_orm() -> ApprovalORM:
    """Provide a sample ApprovalORM instance."""
    now = datetime.now(timezone.utc)
    return ApprovalORM(
        id="APP-001",
        project_id="PRJ-001",
        target_type="process_version",
        target_id="PV-001",
        decision="approved",
        reviewer="John Doe",
        timestamp=now,
        comment="Awaiting stakeholder review",
    )


@pytest.fixture
def sample_agent_run_create() -> AgentRunCreate:
    """Provide a sample AgentRunCreate model."""
    now = datetime.now(timezone.utc)
    return AgentRunCreate(
        id="AR-001",
        project_id="PRJ-001",
        node_name="DocumentAnalyzer",
        status="completed",
        input_summary="Document submitted for analysis",
        output_ref="ART-001",
        error=None,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_agent_run_orm() -> AgentRunORM:
    """Provide a sample AgentRunORM instance."""
    now = datetime.now(timezone.utc)
    return AgentRunORM(
        id="AR-001",
        project_id="PRJ-001",
        node_name="DocumentAnalyzer",
        status="completed",
        input_summary="Document submitted for analysis",
        output_ref="ART-001",
        error=None,
        created_at=now,
        updated_at=now,
    )


class TestClarificationItemRepository:
    """Test ClarificationItemRepository CRUD operations."""

    @patch(
        "processfoundry_ai.repositories.clarification_item_repository.session_context"
    )
    def test_create_clarification_success(
        self, mock_session_context, db_config, sample_clarification_create
    ) -> None:
        """Test successful clarification item creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ClarificationItemRepository(db_config)
        result = repo.create(sample_clarification_create)

        assert result.id == "CL-001"
        assert result.project_id == "PRJ-001"
        assert result.status == "open"
        assert result.reason == "The source documents omit the approval sequence."
        mock_session.add.assert_called_once()

    @patch(
        "processfoundry_ai.repositories.clarification_item_repository.session_context"
    )
    def test_get_clarification_by_id(
        self, mock_session_context, db_config, sample_clarification_orm
    ) -> None:
        """Test successful clarification item retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_clarification_orm

        repo = ClarificationItemRepository(db_config)
        result = repo.get_by_id("CL-001")

        assert result is not None
        assert result.question == "What are the exact approval workflow steps required?"

    @patch(
        "processfoundry_ai.repositories.clarification_item_repository.session_context"
    )
    def test_list_clarifications_by_project(
        self, mock_session_context, db_config, sample_clarification_orm
    ) -> None:
        """Test listing clarification items for a project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_clarification_orm]

        repo = ClarificationItemRepository(db_config)
        result = repo.list_by_project("PRJ-001")

        assert len(result) == 1
        assert result[0].status == "open"

    @patch(
        "processfoundry_ai.repositories.clarification_item_repository.session_context"
    )
    def test_clarification_status_transitions(
        self, mock_session_context, db_config
    ) -> None:
        """Test clarification items with different statuses."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ClarificationItemRepository(db_config)

        statuses = ["open", "answered", "resolved"]
        for status in statuses:
            clarification = ClarificationItemCreate(
                id=f"CL-{status}",
                project_id="PRJ-001",
                question="Test question",
                reason="Needs clarification",
                status=status,
                answer="Resolved answer" if status != "open" else None,
                answered_by="reviewer" if status != "open" else None,
            )
            result = repo.create(clarification)
            assert result.status == status


class TestTestCaseRepository:
    """Test TestCaseRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.test_case_repository.session_context")
    def test_create_test_case_success(
        self, mock_session_context, db_config, sample_test_case_create
    ) -> None:
        """Test successful test case creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = TestCaseRepository(db_config)
        result = repo.create(sample_test_case_create)

        assert result.id == "TEST-001"
        assert result.project_id == "PRJ-001"
        assert result.test_key == "TEST-001"
        assert result.requirement_id == "REQ-001"
        mock_session.add.assert_called_once()

    @patch("processfoundry_ai.repositories.test_case_repository.session_context")
    def test_get_test_case_by_id(
        self, mock_session_context, db_config, sample_test_case_orm
    ) -> None:
        """Test successful test case retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_test_case_orm

        repo = TestCaseRepository(db_config)
        result = repo.get_by_id("TEST-001")

        assert result is not None
        assert result.scenario == "Valid document submission"

    @patch("processfoundry_ai.repositories.test_case_repository.session_context")
    def test_list_test_cases_by_project(
        self, mock_session_context, db_config, sample_test_case_orm
    ) -> None:
        """Test listing test cases for a project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_test_case_orm]

        repo = TestCaseRepository(db_config)
        result = repo.list_by_project("PRJ-001")

        assert len(result) == 1
        assert result[0].expected_result == "Document accepted and stored in system"

    @patch("processfoundry_ai.repositories.test_case_repository.session_context")
    def test_test_cases_linked_to_requirements(
        self, mock_session_context, db_config
    ) -> None:
        """Test test cases can be tied to specific requirements."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = TestCaseRepository(db_config)

        for i, requirement_id in enumerate(["REQ-001", "REQ-002", "REQ-003"], start=1):
            test_case = TestCaseCreate(
                id=f"TEST-{i:03d}",
                project_id="PRJ-001",
                test_key=f"TEST-{i:03d}",
                requirement_id=requirement_id,
                scenario=f"Scenario for {requirement_id}",
                expected_result="Expected outcome",
            )
            result = repo.create(test_case)
            assert result.requirement_id == requirement_id

    @patch("processfoundry_ai.repositories.test_case_repository.session_context")
    def test_create_test_case_invalid_requirement_fk(
        self, mock_session_context, db_config, sample_test_case_create
    ) -> None:
        """Test test case creation with invalid requirement_id FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError(
            "Foreign key constraint violation"
        )

        repo = TestCaseRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_test_case_create)


class TestApprovalRepository:
    """Test ApprovalRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.approval_repository.session_context")
    def test_create_approval_success(
        self, mock_session_context, db_config, sample_approval_create
    ) -> None:
        """Test successful approval creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ApprovalRepository(db_config)
        result = repo.create(sample_approval_create)

        assert result.id == "APP-001"
        assert result.project_id == "PRJ-001"
        assert result.target_type == "process_version"
        assert result.target_id == "PV-001"
        assert result.decision == "approved"
        mock_session.add.assert_called_once()

    @patch("processfoundry_ai.repositories.approval_repository.session_context")
    def test_get_approval_by_id(
        self, mock_session_context, db_config, sample_approval_orm
    ) -> None:
        """Test successful approval retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_approval_orm

        repo = ApprovalRepository(db_config)
        result = repo.get_by_id("APP-001")

        assert result is not None
        assert result.reviewer == "John Doe"

    @patch("processfoundry_ai.repositories.approval_repository.session_context")
    def test_list_approvals_by_project(
        self, mock_session_context, db_config, sample_approval_orm
    ) -> None:
        """Test listing approvals for a project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_approval_orm]

        repo = ApprovalRepository(db_config)
        result = repo.list_by_project("PRJ-001")

        assert len(result) == 1
        assert result[0].target_type == "process_version"

    @patch("processfoundry_ai.repositories.approval_repository.session_context")
    def test_approval_decision_values(self, mock_session_context, db_config) -> None:
        """Test approval records with different decision values."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ApprovalRepository(db_config)
        now = datetime.now(timezone.utc)

        decisions = ["approved", "rejected", "request_changes"]
        for decision in decisions:
            approval = ApprovalCreate(
                id=f"APP-{decision}",
                project_id="PRJ-001",
                target_type="requirement",
                target_id="REQ-001",
                decision=decision,
                reviewer="Reviewer",
                timestamp=now,
                comment=f"Approval decision: {decision}",
            )
            result = repo.create(approval)
            assert result.decision == decision


class TestAgentRunRepository:
    """Test AgentRunRepository CRUD operations."""

    @patch("processfoundry_ai.repositories.agent_run_repository.session_context")
    def test_create_agent_run_success(
        self, mock_session_context, db_config, sample_agent_run_create
    ) -> None:
        """Test successful agent run creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = AgentRunRepository(db_config)
        result = repo.create(sample_agent_run_create)

        assert result.id == "AR-001"
        assert result.project_id == "PRJ-001"
        assert result.status == "completed"
        assert result.error is None
        mock_session.add.assert_called_once()

    @patch("processfoundry_ai.repositories.agent_run_repository.session_context")
    def test_get_agent_run_by_id(
        self, mock_session_context, db_config, sample_agent_run_orm
    ) -> None:
        """Test successful agent run retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.first.return_value = sample_agent_run_orm

        repo = AgentRunRepository(db_config)
        result = repo.get_by_id("AR-001")

        assert result is not None
        assert result.node_name == "DocumentAnalyzer"

    @patch("processfoundry_ai.repositories.agent_run_repository.session_context")
    def test_list_agent_runs_by_project(
        self, mock_session_context, db_config, sample_agent_run_orm
    ) -> None:
        """Test listing agent runs for a project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None
        mock_session.scalars.return_value.all.return_value = [sample_agent_run_orm]

        repo = AgentRunRepository(db_config)
        result = repo.list_by_project("PRJ-001")

        assert len(result) == 1
        assert result[0].output_ref == "ART-001"

    @patch("processfoundry_ai.repositories.agent_run_repository.session_context")
    def test_agent_run_status_values(self, mock_session_context, db_config) -> None:
        """Test agent runs with different status values."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = AgentRunRepository(db_config)
        now = datetime.now(timezone.utc)

        statuses = ["running", "completed", "failed"]
        for status in statuses:
            agent_run = AgentRunCreate(
                id=f"AR-{status}",
                project_id="PRJ-001",
                node_name="TestAgent",
                status=status,
                input_summary="Input data",
                output_ref="ART-001" if status == "completed" else None,
                error="Error occurred" if status == "failed" else None,
                created_at=now,
                updated_at=now,
            )
            result = repo.create(agent_run)
            assert result.status == status

    @patch("processfoundry_ai.repositories.agent_run_repository.session_context")
    def test_agent_run_error_handling(self, mock_session_context, db_config) -> None:
        """Test agent runs with error messages."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = AgentRunRepository(db_config)
        now = datetime.now(timezone.utc)

        agent_run = AgentRunCreate(
            id="AR-error",
            project_id="PRJ-001",
            node_name="FailingAgent",
            status="failed",
            input_summary="Input data",
            output_ref=None,
            error="Database connection timeout after 30 seconds",
            created_at=now,
            updated_at=now,
        )
        result = repo.create(agent_run)
        assert result.status == "failed"
        assert result.error is not None
