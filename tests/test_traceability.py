"""Tests for traceability linking: complete data lineage from evidence to test cases."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.business_rule import BusinessRuleCreate
from processfoundry_ai.models.rule_evidence import RuleEvidenceCreate
from processfoundry_ai.models.requirement import RequirementCreate
from processfoundry_ai.models.requirement_link import RequirementLinkCreate
from processfoundry_ai.models.process_version import ProcessVersionCreate
from processfoundry_ai.models.process_step import ProcessStepCreate
from processfoundry_ai.models.test_case import TestCaseCreate
from processfoundry_ai.models.artifact import ArtifactCreate
from processfoundry_ai.models.artifact_link import ArtifactLinkCreate
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
from processfoundry_ai.repositories.process_version_repository import (
    ProcessVersionRepository,
)
from processfoundry_ai.repositories.process_step_repository import ProcessStepRepository
from processfoundry_ai.repositories.test_case_repository import TestCaseRepository
from processfoundry_ai.repositories.artifact_repository import ArtifactRepository
from processfoundry_ai.repositories.artifact_link_repository import ArtifactLinkRepository


@pytest.fixture
def db_config() -> DatabaseConfig:
    """Provide a test database configuration."""
    return DatabaseConfig(dsn="postgresql://test:test@localhost:5432/test_db")


class TestEvidenceToRuleTraceability:
    """Test traceability from Evidence Items to Business Rules."""

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_evidence_links_to_business_rule(
        self, mock_evidence_session, mock_br_session, db_config
    ) -> None:
        """Test that evidence items can be linked to business rules."""
        mock_br = MagicMock()
        mock_br_session.return_value.__enter__.return_value = mock_br
        mock_br_session.return_value.__exit__.return_value = None

        mock_evidence = MagicMock()
        mock_evidence_session.return_value.__enter__.return_value = mock_evidence
        mock_evidence_session.return_value.__exit__.return_value = None

        br_repo = BusinessRuleRepository(db_config)
        evidence_repo = RuleEvidenceRepository(db_config)

        br = BusinessRuleCreate(
            id="BR-001",
            project_id="PRJ-001",
            rule_key="BR-001",
            description="All documents must have signatures",
            condition_json=None,
            status="active",
        )
        br_result = br_repo.create(br)

        evidence_link = RuleEvidenceCreate(
            rule_id=br_result.id,
            evidence_id="EV-001",
        )
        evidence_result = evidence_repo.create(evidence_link)

        assert evidence_result.rule_id == br_result.id
        assert evidence_result.evidence_id == "EV-001"

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    def test_multiple_evidence_items_support_rule(
        self, mock_evidence_session, mock_br_session, db_config
    ) -> None:
        """Test that multiple evidence items can support a single business rule."""
        mock_br = MagicMock()
        mock_br_session.return_value.__enter__.return_value = mock_br
        mock_br_session.return_value.__exit__.return_value = None

        mock_evidence = MagicMock()
        mock_evidence_session.return_value.__enter__.return_value = mock_evidence
        mock_evidence_session.return_value.__exit__.return_value = None

        br_repo = BusinessRuleRepository(db_config)
        evidence_repo = RuleEvidenceRepository(db_config)

        br = BusinessRuleCreate(
            id="BR-001",
            project_id="PRJ-001",
            rule_key="BR-001",
            description="Rule supported by multiple evidence items",
            condition_json=None,
            status="active",
        )
        br_result = br_repo.create(br)

        evidence_ids = ["EV-001", "EV-002", "EV-003"]
        links = []
        for ev_id in evidence_ids:
            evidence_link = RuleEvidenceCreate(
                rule_id=br_result.id,
                evidence_id=ev_id,
            )
            link_result = evidence_repo.create(evidence_link)
            links.append(link_result)

        assert all(link.rule_id == br_result.id for link in links)
        assert len(links) == 3


class TestRuleToRequirementTraceability:
    """Test traceability from Business Rules to Requirements."""

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    def test_business_rule_links_to_requirement(
        self, mock_link_session, mock_req_session, mock_br_session, db_config
    ) -> None:
        """Test that business rules can link to requirements."""
        mock_br = MagicMock()
        mock_br_session.return_value.__enter__.return_value = mock_br
        mock_br_session.return_value.__exit__.return_value = None

        mock_req = MagicMock()
        mock_req_session.return_value.__enter__.return_value = mock_req
        mock_req_session.return_value.__exit__.return_value = None

        mock_link = MagicMock()
        mock_link_session.return_value.__enter__.return_value = mock_link
        mock_link_session.return_value.__exit__.return_value = None

        br_repo = BusinessRuleRepository(db_config)
        req_repo = RequirementRepository(db_config)
        link_repo = RequirementLinkRepository(db_config)

        br = BusinessRuleCreate(
            id="BR-001",
            project_id="PRJ-001",
            rule_key="BR-001",
            description="Rule description",
            condition_json=None,
            status="active",
        )
        br_result = br_repo.create(br)

        req = RequirementCreate(
            id="REQ-001",
            project_id="PRJ-001",
            requirement_key="REQ-001",
            type="functional",
            statement="Implement validation",
            priority="must",
            status="draft",
        )
        req_result = req_repo.create(req)

        link = RequirementLinkCreate(
            source_requirement_id=req_result.id,
            target_id=br_result.id,
            link_type="grounded_in_rule",
        )
        link_result = link_repo.create(link)

        assert link_result.source_requirement_id == req_result.id
        assert link_result.link_type == "grounded_in_rule"
        assert link_result.target_id == br_result.id


class TestRequirementToProcessTraceability:
    """Test traceability from Requirements to Process Steps."""

    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    def test_requirement_links_to_process_step(
        self,
        mock_step_session,
        mock_pv_session,
        mock_link_session,
        mock_req_session,
        db_config,
    ) -> None:
        """Test that requirements can link to process steps."""
        mock_req = MagicMock()
        mock_req_session.return_value.__enter__.return_value = mock_req
        mock_req_session.return_value.__exit__.return_value = None

        mock_pv = MagicMock()
        mock_pv_session.return_value.__enter__.return_value = mock_pv
        mock_pv_session.return_value.__exit__.return_value = None

        mock_step = MagicMock()
        mock_step_session.return_value.__enter__.return_value = mock_step
        mock_step_session.return_value.__exit__.return_value = None

        mock_link = MagicMock()
        mock_link_session.return_value.__enter__.return_value = mock_link
        mock_link_session.return_value.__exit__.return_value = None

        req_repo = RequirementRepository(db_config)
        link_repo = RequirementLinkRepository(db_config)
        pv_repo = ProcessVersionRepository(db_config)
        step_repo = ProcessStepRepository(db_config)

        req = RequirementCreate(
            id="REQ-001",
            project_id="PRJ-001",
            requirement_key="REQ-001",
            type="functional",
            statement="Must implement validation",
            priority="must",
            status="draft",
        )
        req_result = req_repo.create(req)

        pv = ProcessVersionCreate(
            id="PV-001",
            project_id="PRJ-001",
            version="1.0",
            as_is_json=None,
            to_be_json=None,
            status="draft",
        )
        pv_result = pv_repo.create(pv)

        step = ProcessStepCreate(
            id="PS-001",
            process_version_id=pv_result.id,
            step_key="STEP-001",
            name="Validate input",
            actor="System",
            step_type="task",
            sequence=1,
        )
        step_result = step_repo.create(step)

        link = RequirementLinkCreate(
            source_requirement_id=req_result.id,
            target_id=step_result.id,
            link_type="implements_step",
        )
        link_result = link_repo.create(link)

        assert link_result.source_requirement_id == req_result.id
        assert link_result.target_id == step_result.id


class TestProcessToTestCaseTraceability:
    """Test traceability from Process Steps to Test Cases."""

    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    @patch("processfoundry_ai.repositories.test_case_repository.session_context")
    def test_process_step_links_to_test_case(
        self,
        mock_test_session,
        mock_step_session,
        mock_pv_session,
        db_config,
    ) -> None:
        """Test that process steps can be validated by requirement-linked test cases."""
        mock_pv = MagicMock()
        mock_pv_session.return_value.__enter__.return_value = mock_pv
        mock_pv_session.return_value.__exit__.return_value = None

        mock_step = MagicMock()
        mock_step_session.return_value.__enter__.return_value = mock_step
        mock_step_session.return_value.__exit__.return_value = None

        mock_test = MagicMock()
        mock_test_session.return_value.__enter__.return_value = mock_test
        mock_test_session.return_value.__exit__.return_value = None

        pv_repo = ProcessVersionRepository(db_config)
        step_repo = ProcessStepRepository(db_config)
        test_repo = TestCaseRepository(db_config)

        pv = ProcessVersionCreate(
            id="PV-001",
            project_id="PRJ-001",
            version="1.0",
            as_is_json=None,
            to_be_json=None,
            status="draft",
        )
        pv_result = pv_repo.create(pv)

        step = ProcessStepCreate(
            id="PS-001",
            process_version_id=pv_result.id,
            step_key="STEP-001",
            name="Validate input",
            actor="System",
            step_type="task",
            sequence=1,
        )
        step_result = step_repo.create(step)

        test = TestCaseCreate(
            id="TEST-001",
            project_id="PRJ-001",
            test_key="TEST-001",
            requirement_id="REQ-001",
            scenario="Valid input submission",
            expected_result="Form accepted",
        )
        test_result = test_repo.create(test)

        assert test_result.id == "TEST-001"
        assert test_result.requirement_id == "REQ-001"
        assert step_result.id == "PS-001"


class TestArtifactTraceability:
    """Test traceability of artifacts across process entities."""

    @patch("processfoundry_ai.repositories.artifact_repository.session_context")
    @patch("processfoundry_ai.repositories.artifact_link_repository.session_context")
    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    def test_artifact_links_multiple_process_entities(
        self,
        mock_req_session,
        mock_pv_session,
        mock_link_session,
        mock_art_session,
        db_config,
    ) -> None:
        """Test that artifacts can link to multiple entity types."""
        mock_art = MagicMock()
        mock_art_session.return_value.__enter__.return_value = mock_art
        mock_art_session.return_value.__exit__.return_value = None

        mock_pv = MagicMock()
        mock_pv_session.return_value.__enter__.return_value = mock_pv
        mock_pv_session.return_value.__exit__.return_value = None

        mock_req = MagicMock()
        mock_req_session.return_value.__enter__.return_value = mock_req
        mock_req_session.return_value.__exit__.return_value = None

        mock_link = MagicMock()
        mock_link_session.return_value.__enter__.return_value = mock_link
        mock_link_session.return_value.__exit__.return_value = None

        art_repo = ArtifactRepository(db_config)
        link_repo = ArtifactLinkRepository(db_config)
        pv_repo = ProcessVersionRepository(db_config)
        req_repo = RequirementRepository(db_config)

        artifact = ArtifactCreate(
            id="ART-001",
            project_id="PRJ-001",
            artifact_type="diagram",
            version="1.0",
            content_json={"title": "Process Flow Diagram"},
            markdown=None,
            status="draft",
        )
        art_result = art_repo.create(artifact)

        pv = ProcessVersionCreate(
            id="PV-001",
            project_id="PRJ-001",
            version="1.0",
            as_is_json=None,
            to_be_json=None,
            status="draft",
        )
        pv_result = pv_repo.create(pv)

        req = RequirementCreate(
            id="REQ-001",
            project_id="PRJ-001",
            requirement_key="REQ-001",
            type="functional",
            statement="Requirement statement",
            priority="must",
            status="draft",
        )
        req_result = req_repo.create(req)

        link1 = ArtifactLinkCreate(
            artifact_id=art_result.id,
            target_type="process_version",
            target_id=pv_result.id,
            link_type="describes",
        )
        link1_result = link_repo.create(link1)

        link2 = ArtifactLinkCreate(
            artifact_id=art_result.id,
            target_type="requirement",
            target_id=req_result.id,
            link_type="documents",
        )
        link2_result = link_repo.create(link2)

        assert link1_result.artifact_id == art_result.id
        assert link2_result.artifact_id == art_result.id
        assert link1_result.target_type == "process_version"
        assert link2_result.target_type == "requirement"


class TestCompleteTraceabilityChain:
    """Test a complete traceability chain from evidence to test case."""

    @patch("processfoundry_ai.repositories.business_rule_repository.session_context")
    @patch("processfoundry_ai.repositories.rule_evidence_repository.session_context")
    @patch("processfoundry_ai.repositories.requirement_repository.session_context")
    @patch("processfoundry_ai.repositories.requirement_link_repository.session_context")
    @patch("processfoundry_ai.repositories.process_version_repository.session_context")
    @patch("processfoundry_ai.repositories.process_step_repository.session_context")
    @patch("processfoundry_ai.repositories.test_case_repository.session_context")
    def test_complete_evidence_to_test_chain(
        self,
        mock_test_session,
        mock_step_session,
        mock_pv_session,
        mock_link_session,
        mock_req_session,
        mock_evidence_session,
        mock_br_session,
        db_config,
    ) -> None:
        """Test complete traceability: Evidence → Rule → Requirement → Step → Test."""
        mock_br = MagicMock()
        mock_br_session.return_value.__enter__.return_value = mock_br
        mock_br_session.return_value.__exit__.return_value = None

        mock_evidence = MagicMock()
        mock_evidence_session.return_value.__enter__.return_value = mock_evidence
        mock_evidence_session.return_value.__exit__.return_value = None

        mock_req = MagicMock()
        mock_req_session.return_value.__enter__.return_value = mock_req
        mock_req_session.return_value.__exit__.return_value = None

        mock_link = MagicMock()
        mock_link_session.return_value.__enter__.return_value = mock_link
        mock_link_session.return_value.__exit__.return_value = None

        mock_pv = MagicMock()
        mock_pv_session.return_value.__enter__.return_value = mock_pv
        mock_pv_session.return_value.__exit__.return_value = None

        mock_step = MagicMock()
        mock_step_session.return_value.__enter__.return_value = mock_step
        mock_step_session.return_value.__exit__.return_value = None

        mock_test = MagicMock()
        mock_test_session.return_value.__enter__.return_value = mock_test
        mock_test_session.return_value.__exit__.return_value = None

        br_repo = BusinessRuleRepository(db_config)
        ev_repo = RuleEvidenceRepository(db_config)
        req_repo = RequirementRepository(db_config)
        link_repo = RequirementLinkRepository(db_config)
        pv_repo = ProcessVersionRepository(db_config)
        step_repo = ProcessStepRepository(db_config)
        test_repo = TestCaseRepository(db_config)

        ev_id = "EV-001"

        br = BusinessRuleCreate(
            id="BR-001",
            project_id="PRJ-001",
            rule_key="BR-001",
            description="All documents need signatures",
            condition_json=None,
            status="active",
        )
        br_result = br_repo.create(br)

        ev_link = RuleEvidenceCreate(
            rule_id=br_result.id,
            evidence_id=ev_id,
        )
        ev_link_result = ev_repo.create(ev_link)

        req = RequirementCreate(
            id="REQ-001",
            project_id="PRJ-001",
            requirement_key="REQ-001",
            type="functional",
            statement="System must support digital signatures",
            priority="must",
            status="draft",
        )
        req_result = req_repo.create(req)

        req_link = RequirementLinkCreate(
            source_requirement_id=req_result.id,
            target_id=br_result.id,
            link_type="grounded_in_rule",
        )
        req_link_result = link_repo.create(req_link)

        pv = ProcessVersionCreate(
            id="PV-001",
            project_id="PRJ-001",
            version="1.0",
            as_is_json=None,
            to_be_json=None,
            status="draft",
        )
        pv_result = pv_repo.create(pv)

        step = ProcessStepCreate(
            id="PS-001",
            process_version_id=pv_result.id,
            step_key="STEP-001",
            name="Collect Digital Signature",
            actor="Student",
            step_type="task",
            sequence=1,
        )
        step_result = step_repo.create(step)

        step_link = RequirementLinkCreate(
            source_requirement_id=req_result.id,
            target_id=step_result.id,
            link_type="implements_step",
        )
        step_link_result = link_repo.create(step_link)

        test = TestCaseCreate(
            id="TEST-001",
            project_id="PRJ-001",
            test_key="TEST-001",
            requirement_id=req_result.id,
            scenario="Valid signature submission",
            expected_result="Document marked as signed",
        )
        test_result = test_repo.create(test)

        assert ev_link_result.rule_id == br_result.id
        assert ev_link_result.evidence_id == ev_id
        assert req_link_result.source_requirement_id == req_result.id
        assert req_link_result.target_id == br_result.id
        assert step_link_result.source_requirement_id == req_result.id
        assert step_link_result.target_id == step_result.id
        assert test_result.requirement_id == req_result.id
        assert test_result.scenario == "Valid signature submission"
