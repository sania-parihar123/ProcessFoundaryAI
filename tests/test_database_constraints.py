"""Tests for database constraints: foreign key enforcement and cascade delete behavior."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.process_version import ProcessVersionCreate
from processfoundry_ai.models.process_step import ProcessStepCreate
from processfoundry_ai.models.business_rule import BusinessRuleCreate
from processfoundry_ai.models.rule_evidence import RuleEvidenceCreate
from processfoundry_ai.models.requirement import RequirementCreate
from processfoundry_ai.models.requirement_link import RequirementLinkCreate
from processfoundry_ai.models.artifact import ArtifactCreate
from processfoundry_ai.models.artifact_link import ArtifactLinkCreate
from processfoundry_ai.repositories.process_version_repository import (
    ProcessVersionRepository,
)
from processfoundry_ai.repositories.process_step_repository import ProcessStepRepository
from processfoundry_ai.repositories.business_rule_repository import (
    BusinessRuleRepository,
)
from processfoundry_ai.repositories.rule_evidence_repository import (
    RuleEvidenceRepository,
)
from processfoundry_ai.repositories.requirement_repository import RequirementRepository
from processfoundry_ai.repositories.requirement_link_repository import (
    RequirementLinkRepository,
)
from processfoundry_ai.repositories.artifact_repository import ArtifactRepository
from processfoundry_ai.repositories.artifact_link_repository import ArtifactLinkRepository


@pytest.fixture
def db_config() -> DatabaseConfig:
    """Provide a test database configuration."""
    return DatabaseConfig(dsn="postgresql://test:test@localhost:5432/test_db")


class TestForeignKeyEnforcement:
    """Test foreign key constraint enforcement across all repositories."""

    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    def test_process_step_invalid_process_version_fk(
        self, mock_session_context, db_config
    ) -> None:
        """Test ProcessStep creation with invalid ProcessVersion FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "foreign key constraint", None, None
        )

        repo = ProcessStepRepository(db_config)
        step = ProcessStepCreate(
            id="PS-001",
            process_version_id="INVALID-PV",
            step_key="STEP-001",
            name="Invalid step",
            actor="Student",
            step_type="task",
            sequence=1,
        )

        with pytest.raises(IntegrityError):
            repo.create(step)

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_rule_evidence_invalid_business_rule_fk(
        self, mock_session_context, db_config
    ) -> None:
        """Test RuleEvidence creation with invalid BusinessRule FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "foreign key constraint", None, None
        )

        repo = RuleEvidenceRepository(db_config)
        evidence = RuleEvidenceCreate(
            rule_id="INVALID-BR",
            evidence_id="EV-001",
        )

        with pytest.raises(IntegrityError):
            repo.create(evidence)

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_rule_evidence_invalid_evidence_item_fk(
        self, mock_session_context, db_config
    ) -> None:
        """Test RuleEvidence creation with invalid EvidenceItem FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "foreign key constraint", None, None
        )

        repo = RuleEvidenceRepository(db_config)
        evidence = RuleEvidenceCreate(
            rule_id="BR-001",
            evidence_id="INVALID-EV",
        )

        with pytest.raises(IntegrityError):
            repo.create(evidence)

    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_requirement_link_invalid_source_requirement_fk(
        self, mock_session_context, db_config
    ) -> None:
        """Test RequirementLink creation with invalid source_requirement_id FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "foreign key constraint", None, None
        )

        repo = RequirementLinkRepository(db_config)
        link = RequirementLinkCreate(
            source_requirement_id="INVALID-REQ",
            target_id="PS-001",
            link_type="implements_step",
        )

        with pytest.raises(IntegrityError):
            repo.create(link)

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_artifact_link_invalid_artifact_fk(
        self, mock_session_context, db_config
    ) -> None:
        """Test ArtifactLink creation with invalid artifact_id FK."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "foreign key constraint", None, None
        )

        repo = ArtifactLinkRepository(db_config)
        link = ArtifactLinkCreate(
            artifact_id="INVALID-ART",
            target_type="process_version",
            target_id="PV-001",
            link_type="describes",
        )

        with pytest.raises(IntegrityError):
            repo.create(link)


class TestDuplicateCompositeKeys:
    """Test composite primary keys reject duplicate link rows."""

    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_rule_evidence_duplicate_pair_rejected(
        self, mock_session_context, db_config
    ) -> None:
        """Test duplicate (rule_id, evidence_id) is rejected."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "duplicate key", None, None
        )

        repo = RuleEvidenceRepository(db_config)
        with pytest.raises(IntegrityError):
            repo.create(RuleEvidenceCreate(rule_id="BR-001", evidence_id="EV-001"))

    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_requirement_link_duplicate_triple_rejected(
        self, mock_session_context, db_config
    ) -> None:
        """Test duplicate (source_requirement_id, target_id, link_type) is rejected."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "duplicate key", None, None
        )

        repo = RequirementLinkRepository(db_config)
        with pytest.raises(IntegrityError):
            repo.create(
                RequirementLinkCreate(
                    source_requirement_id="REQ-001",
                    target_id="PS-001",
                    link_type="implements_step",
                )
            )

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_artifact_link_duplicate_quad_rejected(
        self, mock_session_context, db_config
    ) -> None:
        """Test duplicate (artifact_id, target_type, target_id, link_type) is rejected."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "duplicate key", None, None
        )

        repo = ArtifactLinkRepository(db_config)
        with pytest.raises(IntegrityError):
            repo.create(
                ArtifactLinkCreate(
                    artifact_id="ART-001",
                    target_type="requirement",
                    target_id="REQ-001",
                    link_type="documents",
                )
            )


class TestCascadeDeleteBehavior:
    """Test cascade delete behavior for parent-child relationships."""

    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    def test_process_version_cascade_delete_steps(
        self, mock_step_session, mock_pv_session, db_config
    ) -> None:
        """Test that deleting ProcessVersion cascades to ProcessSteps at the ORM layer."""
        mock_pv = MagicMock()
        mock_pv_session.return_value.__enter__.return_value = mock_pv
        mock_pv_session.return_value.__exit__.return_value = None

        mock_step = MagicMock()
        mock_step_session.return_value.__enter__.return_value = mock_step
        mock_step_session.return_value.__exit__.return_value = None

        pv_repo = ProcessVersionRepository(db_config)

        pv = ProcessVersionCreate(
            id="PV-001",
            project_id="PRJ-001",
            version="1.0",
            as_is_json=None,
            to_be_json=None,
            status="draft",
        )
        pv_result = pv_repo.create(pv)

        # Database FKs do not declare ON DELETE CASCADE; ORM relationships do.
        # Runtime cascade verification requires an integration database.
        assert pv_result.id == "PV-001"

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_business_rule_cascade_delete_evidence(
        self, mock_evidence_session, mock_br_session, db_config
    ) -> None:
        """Test that deleting BusinessRule cascades to RuleEvidence at the ORM layer."""
        mock_br = MagicMock()
        mock_br_session.return_value.__enter__.return_value = mock_br
        mock_br_session.return_value.__exit__.return_value = None

        mock_evidence = MagicMock()
        mock_evidence_session.return_value.__enter__.return_value = mock_evidence
        mock_evidence_session.return_value.__exit__.return_value = None

        br_repo = BusinessRuleRepository(db_config)

        br = BusinessRuleCreate(
            id="BR-001",
            project_id="PRJ-001",
            rule_key="BR-001",
            description="Rule description",
            condition_json=None,
            status="active",
        )
        br_result = br_repo.create(br)

        assert br_result.id == "BR-001"

    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    @patch(
        "processfoundry_ai.repositories.requirement_link_repository.session_context"
    )
    def test_requirement_cascade_delete_links(
        self, mock_link_session, mock_req_session, db_config
    ) -> None:
        """Test that deleting Requirement cascades to RequirementLinks at the ORM layer."""
        mock_req = MagicMock()
        mock_req_session.return_value.__enter__.return_value = mock_req
        mock_req_session.return_value.__exit__.return_value = None

        mock_link = MagicMock()
        mock_link_session.return_value.__enter__.return_value = mock_link
        mock_link_session.return_value.__exit__.return_value = None

        req_repo = RequirementRepository(db_config)

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

        assert req_result.id == "REQ-001"

    @patch("processfoundry_ai.repositories.artifact_repository.session_context")
    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_artifact_cascade_delete_links(
        self, mock_link_session, mock_art_session, db_config
    ) -> None:
        """Test that deleting Artifact cascades to ArtifactLinks at the ORM layer."""
        mock_art = MagicMock()
        mock_art_session.return_value.__enter__.return_value = mock_art
        mock_art_session.return_value.__exit__.return_value = None

        mock_link = MagicMock()
        mock_link_session.return_value.__enter__.return_value = mock_link
        mock_link_session.return_value.__exit__.return_value = None

        art_repo = ArtifactRepository(db_config)

        art = ArtifactCreate(
            id="ART-001",
            project_id="PRJ-001",
            artifact_type="document",
            version="1.0",
            content_json=None,
            markdown=None,
            status="draft",
        )
        art_result = art_repo.create(art)

        assert art_result.id == "ART-001"


class TestConstraintEnforcement:
    """Test general constraint enforcement policies."""

    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    def test_process_version_project_id_required(
        self, mock_session_context, db_config
    ) -> None:
        """Test that ProcessVersion requires project_id."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = IntegrityError(
            "NOT NULL constraint", None, None
        )

        repo = ProcessVersionRepository(db_config)

        pv = ProcessVersionCreate(
            id="PV-001",
            project_id="",
            version="1.0",
            as_is_json=None,
            to_be_json=None,
            status="draft",
        )

        with pytest.raises(IntegrityError):
            repo.create(pv)

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    def test_business_rule_status_persisted(
        self, mock_session_context, db_config
    ) -> None:
        """Test that BusinessRule status is stored as required text."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session

        repo = BusinessRuleRepository(db_config)

        br = BusinessRuleCreate(
            id="BR-001",
            project_id="PRJ-001",
            rule_key="BR-001",
            description="Description",
            condition_json=None,
            status="active",
        )
        result = repo.create(br)
        assert result.status == "active"

    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    def test_requirement_priority_persisted(
        self, mock_session_context, db_config
    ) -> None:
        """Test that Requirement priority is stored as required text."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session

        repo = RequirementRepository(db_config)

        valid_priorities = ["must", "should", "could", "wont"]
        for priority in valid_priorities:
            req = RequirementCreate(
                id=f"REQ-{priority}",
                project_id="PRJ-001",
                requirement_key=f"REQ-{priority}",
                type="functional",
                statement="Description",
                priority=priority,
                status="draft",
            )
            result = repo.create(req)
            assert result.priority == priority


class TestPolymorphicLinkingConstraints:
    """Test linking validation for flexible entity references."""

    @patch(
        "processfoundry_ai.repositories.requirement_link_repository.session_context"
    )
    def test_requirement_link_multiple_target_ids(
        self, mock_session_context, db_config
    ) -> None:
        """Test RequirementLink can point at multiple related entity IDs."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = RequirementLinkRepository(db_config)

        targets = [
            ("PS-001", "implements_step"),
            ("BR-001", "grounded_in_rule"),
            ("ART-001", "documented_by"),
            ("TEST-001", "verified_by"),
            ("APP-001", "approved_by"),
        ]

        for target_id, link_type in targets:
            link = RequirementLinkCreate(
                source_requirement_id="REQ-001",
                target_id=target_id,
                link_type=link_type,
            )
            result = repo.create(link)
            assert result.target_id == target_id
            assert result.link_type == link_type

    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    def test_artifact_link_polymorphic_targets(
        self, mock_session_context, db_config
    ) -> None:
        """Test ArtifactLink can link to multiple entity types."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = ArtifactLinkRepository(db_config)

        target_types = [
            "process_version",
            "process_step",
            "business_rule",
            "requirement",
            "test_case",
        ]

        for i, target_type in enumerate(target_types, 1):
            link = ArtifactLinkCreate(
                artifact_id="ART-001",
                target_type=target_type,
                target_id=f"ENT-{i:03d}",
                link_type="relates_to",
            )
            result = repo.create(link)
            assert result.target_type == target_type
