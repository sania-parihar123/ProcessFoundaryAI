"""Test Pydantic schemas for new database entities."""

from __future__ import annotations

from datetime import datetime, timezone

from processfoundry_ai.models import (
    AgentRunCreate,
    ApprovalCreate,
    ArtifactCreate,
    ArtifactLinkCreate,
    BusinessRuleCreate,
    BusinessRuleRead,
    ClarificationItemCreate,
    ProcessStepCreate,
    ProcessVersionCreate,
    ProcessVersionRead,
    RequirementCreate,
    RequirementLinkCreate,
    RuleEvidenceCreate,
    TestCaseCreate,
)


class TestProcessVersionSchemas:
    """Test ProcessVersion Pydantic schemas."""

    def test_process_version_create_valid(self) -> None:
        """Test creating a valid ProcessVersionCreate model."""
        pv = ProcessVersionCreate(
            id="PV-001",
            project_id="PRJ-001",
            version="1.0",
            as_is_json={"steps": []},
            to_be_json=None,
            status="draft",
        )
        assert pv.id == "PV-001"
        assert pv.project_id == "PRJ-001"
        assert pv.version == "1.0"
        assert pv.status == "draft"

    def test_process_version_read_from_attributes(self) -> None:
        """Test ProcessVersionRead with from_attributes config."""
        data = {
            "id": "PV-001",
            "project_id": "PRJ-001",
            "version": "1.0",
            "as_is_json": None,
            "to_be_json": None,
            "status": "draft",
        }
        pv = ProcessVersionRead(**data)
        assert pv.id == "PV-001"


class TestProcessStepSchemas:
    """Test ProcessStep Pydantic schemas."""

    def test_process_step_create_valid(self) -> None:
        """Test creating a valid ProcessStepCreate model."""
        ps = ProcessStepCreate(
            id="PS-001",
            process_version_id="PV-001",
            step_key="STEP-001",
            name="Submit Request",
            actor="Student",
            step_type="task",
            sequence=1,
        )
        assert ps.id == "PS-001"
        assert ps.process_version_id == "PV-001"
        assert ps.step_key == "STEP-001"
        assert ps.sequence == 1
        assert ps.name == "Submit Request"

    def test_process_step_sequence_ordering(self) -> None:
        """Test that sequence can be ordered."""
        steps = [
            ProcessStepCreate(
                id="PS-001",
                process_version_id="PV-001",
                step_key="STEP-002",
                name="Review",
                actor="Advisor",
                step_type="review",
                sequence=2,
            ),
            ProcessStepCreate(
                id="PS-002",
                process_version_id="PV-001",
                step_key="STEP-001",
                name="Submit",
                actor="Student",
                step_type="task",
                sequence=1,
            ),
        ]
        sorted_steps = sorted(steps, key=lambda s: s.sequence)
        assert sorted_steps[0].sequence == 1
        assert sorted_steps[1].sequence == 2


class TestBusinessRuleSchemas:
    """Test BusinessRule Pydantic schemas."""

    def test_business_rule_create_valid(self) -> None:
        """Test creating a valid BusinessRuleCreate model."""
        br = BusinessRuleCreate(
            id="BR-001",
            project_id="PRJ-001",
            rule_key="BR-001",
            description="Applicants must have GPA >= 3.0",
            condition_json={"gpa": {"min": 3.0}},
            status="candidate",
        )
        assert br.id == "BR-001"
        assert br.project_id == "PRJ-001"
        assert br.rule_key == "BR-001"

    def test_business_rule_read_model(self) -> None:
        """Test BusinessRuleRead model."""
        br = BusinessRuleRead(
            id="BR-001",
            project_id="PRJ-001",
            rule_key="BR-001",
            description="Applicants must have GPA >= 3.0",
            condition_json={"gpa": {"min": 3.0}},
            status="candidate",
        )
        assert br.status == "candidate"


class TestRuleEvidenceSchemas:
    """Test RuleEvidence Pydantic schemas."""

    def test_rule_evidence_create_valid(self) -> None:
        """Test creating a valid RuleEvidenceCreate model."""
        re = RuleEvidenceCreate(
            rule_id="BR-001",
            evidence_id="EVD-001",
        )
        assert re.rule_id == "BR-001"
        assert re.evidence_id == "EVD-001"

    def test_rule_evidence_linking(self) -> None:
        """Test rule evidence linking multiple evidence items to a rule."""
        rule_id = "BR-001"
        evidence_links = [
            RuleEvidenceCreate(
                rule_id=rule_id,
                evidence_id=f"EVD-{i:03d}",
            )
            for i in range(1, 4)
        ]
        assert len(evidence_links) == 3
        assert all(link.rule_id == rule_id for link in evidence_links)


class TestRequirementSchemas:
    """Test Requirement Pydantic schemas."""

    def test_requirement_create_valid(self) -> None:
        """Test creating a valid RequirementCreate model."""
        req = RequirementCreate(
            id="REQ-001",
            project_id="PRJ-001",
            requirement_key="REQ-001",
            type="functional",
            statement="System must validate all required fields",
            priority="must",
            status="draft",
        )
        assert req.id == "REQ-001"
        assert req.type == "functional"
        assert req.priority == "must"

    def test_requirement_priority_levels(self) -> None:
        """Test various requirement priority levels."""
        priorities = ["must", "should", "could", "wont"]
        for priority in priorities:
            req = RequirementCreate(
                id=f"REQ-{priority}",
                project_id="PRJ-001",
                requirement_key=f"REQ-{priority}",
                type="functional",
                statement=f"Priority {priority}",
                priority=priority,
                status="draft",
            )
            assert req.priority == priority


class TestRequirementLinkSchemas:
    """Test RequirementLink Pydantic schemas."""

    def test_requirement_link_create_valid(self) -> None:
        """Test creating a valid RequirementLinkCreate model."""
        rl = RequirementLinkCreate(
            source_requirement_id="REQ-001",
            target_id="PS-001",
            link_type="implements_step",
        )
        assert rl.source_requirement_id == "REQ-001"
        assert rl.target_id == "PS-001"
        assert rl.link_type == "implements_step"

    def test_requirement_link_flexible_targets(self) -> None:
        """Test requirement links to different related entities."""
        source_req = "REQ-001"
        targets = [
            ("PS-001", "implements_step"),
            ("BR-001", "grounded_in_rule"),
            ("ART-001", "documented_by"),
        ]
        links = [
            RequirementLinkCreate(
                source_requirement_id=source_req,
                target_id=target_id,
                link_type=link_type,
            )
            for target_id, link_type in targets
        ]
        assert len(links) == 3
        assert links[0].target_id == "PS-001"
        assert links[1].target_id == "BR-001"
        assert links[2].target_id == "ART-001"


class TestClarificationItemSchemas:
    """Test ClarificationItem Pydantic schemas."""

    def test_clarification_item_create_valid(self) -> None:
        """Test creating a valid ClarificationItemCreate model."""
        ci = ClarificationItemCreate(
            id="CLR-001",
            project_id="PRJ-001",
            question="What is the deadline for final approval?",
            reason="No deadline is stated in the source documents.",
            status="open",
            answer=None,
            answered_by=None,
        )
        assert ci.id == "CLR-001"
        assert ci.project_id == "PRJ-001"
        assert ci.status == "open"

    def test_clarification_item_status_transitions(self) -> None:
        """Test clarification item status lifecycle."""
        statuses = ["open", "in_progress", "resolved"]
        for i, status in enumerate(statuses):
            ci = ClarificationItemCreate(
                id=f"CLR-{i:03d}",
                project_id="PRJ-001",
                question="Test question",
                reason="Needs clarification",
                status=status,
            )
            assert ci.status == status


class TestArtifactSchemas:
    """Test Artifact Pydantic schemas."""

    def test_artifact_create_valid(self) -> None:
        """Test creating a valid ArtifactCreate model."""
        art = ArtifactCreate(
            id="ART-001",
            project_id="PRJ-001",
            artifact_type="process_diagram",
            version="1.0",
            content_json={"title": "As-Is Process Flow"},
            markdown="# As-Is Process Flow",
            status="draft",
        )
        assert art.id == "ART-001"
        assert art.artifact_type == "process_diagram"

    def test_artifact_types(self) -> None:
        """Test various artifact types."""
        types = ["process_diagram", "requirements", "workflow", "test_plan"]
        for i, artifact_type in enumerate(types):
            art = ArtifactCreate(
                id=f"ART-{i:03d}",
                project_id="PRJ-001",
                artifact_type=artifact_type,
                version="1.0",
                content_json={"kind": artifact_type},
                markdown=None,
                status="draft",
            )
            assert art.artifact_type == artifact_type


class TestArtifactLinkSchemas:
    """Test ArtifactLink Pydantic schemas."""

    def test_artifact_link_create_valid(self) -> None:
        """Test creating a valid ArtifactLinkCreate model."""
        al = ArtifactLinkCreate(
            artifact_id="ART-001",
            target_type="requirement",
            target_id="REQ-001",
            link_type="documents",
        )
        assert al.artifact_id == "ART-001"
        assert al.target_type == "requirement"
        assert al.target_id == "REQ-001"

    def test_artifact_link_multiple_targets(self) -> None:
        """Test artifact links to multiple entities."""
        source_art = "ART-001"
        links = [
            ArtifactLinkCreate(
                artifact_id=source_art,
                target_type="process_step",
                target_id=f"PS-{i:03d}",
                link_type="illustrates",
            )
            for i in range(1, 4)
        ]
        assert all(link.artifact_id == source_art for link in links)


class TestTestCaseSchemas:
    """Test TestCase Pydantic schemas."""

    def test_test_case_create_valid(self) -> None:
        """Test creating a valid TestCaseCreate model."""
        tc = TestCaseCreate(
            id="TEST-001",
            project_id="PRJ-001",
            test_key="TEST-001",
            requirement_id="REQ-001",
            scenario="Student submits valid request with all required fields",
            expected_result="Request is accepted",
        )
        assert tc.id == "TEST-001"
        assert tc.project_id == "PRJ-001"
        assert tc.requirement_id == "REQ-001"

    def test_test_case_requirement_links(self) -> None:
        """Test test cases can reference different requirements."""
        for requirement_id in ["REQ-001", "REQ-002", "REQ-003"]:
            tc = TestCaseCreate(
                id=f"TEST-{requirement_id}",
                project_id="PRJ-001",
                test_key=f"TEST-{requirement_id}",
                requirement_id=requirement_id,
                scenario="Test scenario",
                expected_result="Expected outcome",
            )
            assert tc.requirement_id == requirement_id


class TestApprovalSchemas:
    """Test Approval Pydantic schemas."""

    def test_approval_create_valid(self) -> None:
        """Test creating a valid ApprovalCreate model."""
        now = datetime.now(timezone.utc)
        app = ApprovalCreate(
            id="APP-001",
            project_id="PRJ-001",
            target_type="process_version",
            target_id="PV-001",
            decision="approved",
            reviewer="dept-head@example.com",
            timestamp=now,
            comment=None,
        )
        assert app.id == "APP-001"
        assert app.target_type == "process_version"
        assert app.decision == "approved"

    def test_approval_decision_outcomes(self) -> None:
        """Test various approval decision values."""
        now = datetime.now(timezone.utc)
        decisions = ["approved", "rejected", "request_changes"]
        for decision in decisions:
            app = ApprovalCreate(
                id=f"APP-{decision}",
                project_id="PRJ-001",
                target_type="requirement",
                target_id="REQ-001",
                decision=decision,
                reviewer="approver@example.com",
                timestamp=now,
            )
            assert app.decision == decision


class TestAgentRunSchemas:
    """Test AgentRun Pydantic schemas."""

    def test_agent_run_create_valid(self) -> None:
        """Test creating a valid AgentRunCreate model."""
        now = datetime.now(timezone.utc)
        ar = AgentRunCreate(
            id="ARUN-001",
            project_id="PRJ-001",
            node_name="process_discovery_agent",
            status="completed",
            input_summary="Extract process steps from evidence",
            output_ref="ART-001",
            error=None,
            created_at=now,
            updated_at=now,
        )
        assert ar.id == "ARUN-001"
        assert ar.project_id == "PRJ-001"
        assert ar.node_name == "process_discovery_agent"

    def test_agent_run_statuses(self) -> None:
        """Test agent run status values."""
        now = datetime.now(timezone.utc)
        statuses = ["pending", "running", "completed", "failed", "paused"]
        for status in statuses:
            ar = AgentRunCreate(
                id=f"ARUN-{status}",
                project_id="PRJ-001",
                node_name="test_agent",
                status=status,
                input_summary=None,
                output_ref=None,
                error=None,
                created_at=now,
                updated_at=now,
            )
            assert ar.status == status
