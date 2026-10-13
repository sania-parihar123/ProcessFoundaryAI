"""SQLAlchemy ORM models for the canonical ProcessFoundry AI schema.

This module implements the 16 entities described in
ProcessFoundry_AI_Detailed_Implementation_Design.md and the project
specification documents. The schema is intentionally process-agnostic and
preserves the traceability relationships between source evidence,
requirements, rules, workflow steps, artifacts, and test cases.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from processfoundry_ai.database.base import Base


class Project(Base):
    """Project-level metadata and ownership for all project entities."""

    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="projects_name_check"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    process_type: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    documents: Mapped[list[Document]] = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="Document.project_id",
    )
    evidence_items: Mapped[list[EvidenceItem]] = relationship(
        "EvidenceItem",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="EvidenceItem.project_id",
    )
    process_versions: Mapped[list[ProcessVersion]] = relationship(
        "ProcessVersion",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="ProcessVersion.project_id",
    )
    business_rules: Mapped[list[BusinessRule]] = relationship(
        "BusinessRule",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="BusinessRule.project_id",
    )
    clarification_items: Mapped[list[ClarificationItem]] = relationship(
        "ClarificationItem",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="ClarificationItem.project_id",
    )
    requirements: Mapped[list[Requirement]] = relationship(
        "Requirement",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="Requirement.project_id",
    )
    artifacts: Mapped[list[Artifact]] = relationship(
        "Artifact",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="Artifact.project_id",
    )
    test_cases: Mapped[list[TestCase]] = relationship(
        "TestCase",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="TestCase.project_id",
    )
    approvals: Mapped[list[Approval]] = relationship(
        "Approval",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="Approval.project_id",
    )
    agent_runs: Mapped[list[AgentRun]] = relationship(
        "AgentRun",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="AgentRun.project_id",
    )


class Document(Base):
    """Uploaded source documents for a project."""

    __tablename__ = "documents"
    __table_args__ = (Index("idx_documents_project_id", "project_id"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("projects.id", name="fk_documents_project"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="documents")
    sections: Mapped[list[DocumentSection]] = relationship(
        "DocumentSection",
        back_populates="document",
        cascade="all, delete-orphan",
        foreign_keys="DocumentSection.document_id",
    )


class DocumentSection(Base):
    """Extracted content chunks from a document."""

    __tablename__ = "document_sections"
    __table_args__ = (Index("idx_document_sections_document_id", "document_id"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    document_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("documents.id", name="fk_document_sections_document"),
        nullable=False,
    )
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    document: Mapped[Document] = relationship("Document", back_populates="sections")
    evidence_items: Mapped[list[EvidenceItem]] = relationship(
        "EvidenceItem",
        back_populates="document_section",
        cascade="all, delete-orphan",
        foreign_keys="EvidenceItem.document_section_id",
    )


class EvidenceItem(Base):
    """Grounded evidence extracted from document sections."""

    __tablename__ = "evidence_items"
    __table_args__ = (
        Index(
            "idx_evidence_items_project_id",
            "project_id",
            "document_section_id",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("projects.id", name="fk_evidence_items_project"),
        nullable=False,
    )
    document_section_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("document_sections.id", name="fk_evidence_items_document_section"),
        nullable=False,
    )
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric, nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="evidence_items")
    document_section: Mapped[DocumentSection] = relationship(
        "DocumentSection",
        back_populates="evidence_items",
    )
    rule_evidence_links: Mapped[list[RuleEvidence]] = relationship(
        "RuleEvidence",
        back_populates="evidence_item",
        cascade="all, delete-orphan",
        foreign_keys="RuleEvidence.evidence_id",
    )


class ProcessVersion(Base):
    """Versioned As-Is/To-Be process definition snapshots."""

    __tablename__ = "process_versions"
    __table_args__ = (Index("idx_process_versions_project_id", "project_id"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("projects.id", name="fk_process_versions_project"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(Text, nullable=False)
    as_is_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    to_be_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="process_versions")
    steps: Mapped[list[ProcessStep]] = relationship(
        "ProcessStep",
        back_populates="process_version",
        cascade="all, delete-orphan",
        foreign_keys="ProcessStep.process_version_id",
    )


class ProcessStep(Base):
    """Ordered workflow steps within a process version."""

    __tablename__ = "process_steps"
    __table_args__ = (
        Index(
            "idx_process_steps_process_version_id",
            "process_version_id",
            "sequence",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    process_version_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("process_versions.id", name="fk_process_steps_process_version"),
        nullable=False,
    )
    step_key: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    step_type: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    process_version: Mapped[ProcessVersion] = relationship(
        "ProcessVersion",
        back_populates="steps",
    )


class BusinessRule(Base):
    """Candidate business rules tied to a project and evidence."""

    __tablename__ = "business_rules"
    __table_args__ = (Index("idx_business_rules_project_id", "project_id"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("projects.id", name="fk_business_rules_project"),
        nullable=False,
    )
    rule_key: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    condition_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="business_rules")
    rule_evidence_links: Mapped[list[RuleEvidence]] = relationship(
        "RuleEvidence",
        back_populates="business_rule",
        cascade="all, delete-orphan",
        foreign_keys="RuleEvidence.rule_id",
    )


class RuleEvidence(Base):
    """Link table connecting rules to evidence items."""

    __tablename__ = "rule_evidence"
    __table_args__ = (
        PrimaryKeyConstraint("rule_id", "evidence_id", name="pk_rule_evidence"),
        Index("idx_rule_evidence_rule_id", "rule_id"),
        Index("idx_rule_evidence_evidence_id", "evidence_id"),
    )

    rule_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("business_rules.id", name="fk_rule_evidence_business_rule"),
        nullable=False,
    )
    evidence_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("evidence_items.id", name="fk_rule_evidence_evidence_item"),
        nullable=False,
    )

    business_rule: Mapped[BusinessRule] = relationship(
        "BusinessRule",
        back_populates="rule_evidence_links",
    )
    evidence_item: Mapped[EvidenceItem] = relationship(
        "EvidenceItem",
        back_populates="rule_evidence_links",
    )


class ClarificationItem(Base):
    """Open issues and answers required for a project."""

    __tablename__ = "clarification_items"
    __table_args__ = (
        Index("idx_clarification_items_project_id", "project_id", "status"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("projects.id", name="fk_clarification_items_project"),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    answered_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="clarification_items")


class Requirement(Base):
    """Requirements derived from the approved model."""

    __tablename__ = "requirements"
    __table_args__ = (Index("idx_requirements_project_id", "project_id"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("projects.id", name="fk_requirements_project"),
        nullable=False,
    )
    requirement_key: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="requirements")
    requirement_links: Mapped[list[RequirementLink]] = relationship(
        "RequirementLink",
        back_populates="source_requirement",
        cascade="all, delete-orphan",
        foreign_keys="RequirementLink.source_requirement_id",
    )
    test_cases: Mapped[list[TestCase]] = relationship(
        "TestCase",
        back_populates="requirement",
        cascade="all, delete-orphan",
        foreign_keys="TestCase.requirement_id",
    )


class RequirementLink(Base):
    """Requirement traceability links to target IDs without a separate target table."""

    __tablename__ = "requirement_links"
    __table_args__ = (
        PrimaryKeyConstraint(
            "source_requirement_id",
            "target_id",
            "link_type",
            name="pk_requirement_links",
        ),
        Index(
            "idx_requirement_links_source_requirement_id",
            "source_requirement_id",
        ),
    )

    source_requirement_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("requirements.id", name="fk_requirement_links_source_requirement"),
        nullable=False,
    )
    target_id: Mapped[str] = mapped_column(Text, nullable=False)
    link_type: Mapped[str] = mapped_column(Text, nullable=False)

    source_requirement: Mapped[Requirement] = relationship(
        "Requirement",
        back_populates="requirement_links",
    )


class Artifact(Base):
    """Generated output artifacts and documents."""

    __tablename__ = "artifacts"
    __table_args__ = (
        Index("idx_artifacts_project_id", "project_id", "artifact_type"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("projects.id", name="fk_artifacts_project"),
        nullable=False,
    )
    artifact_type: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    content_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="artifacts")
    artifact_links: Mapped[list[ArtifactLink]] = relationship(
        "ArtifactLink",
        back_populates="artifact",
        cascade="all, delete-orphan",
        foreign_keys="ArtifactLink.artifact_id",
    )


class ArtifactLink(Base):
    """Artifact traceability links to target entities."""

    __tablename__ = "artifact_links"
    __table_args__ = (
        PrimaryKeyConstraint(
            "artifact_id",
            "target_type",
            "target_id",
            "link_type",
            name="pk_artifact_links",
        ),
        Index("idx_artifact_links_artifact_id", "artifact_id"),
    )

    artifact_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("artifacts.id", name="fk_artifact_links_source_artifact"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[str] = mapped_column(Text, nullable=False)
    link_type: Mapped[str] = mapped_column(Text, nullable=False)

    artifact: Mapped[Artifact] = relationship(
        "Artifact",
        back_populates="artifact_links",
    )


class TestCase(Base):
    """Requirement-linked tests and UAT scenarios."""

    __tablename__ = "test_cases"
    __table_args__ = (
        Index("idx_test_cases_project_id", "project_id", "requirement_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("projects.id", name="fk_test_cases_project"),
        nullable=False,
    )
    test_key: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("requirements.id", name="fk_test_cases_requirement"),
        nullable=False,
    )
    scenario: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="test_cases")
    requirement: Mapped[Requirement] = relationship("Requirement", back_populates="test_cases")


class Approval(Base):
    """Human approvals and issue-resolution decisions."""

    __tablename__ = "approvals"
    __table_args__ = (
        Index(
            "idx_approvals_project_id",
            "project_id",
            "target_type",
            "target_id",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("projects.id", name="fk_approvals_project"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[str] = mapped_column(Text, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="approvals")


class AgentRun(Base):
    """Run status and debugging record for orchestration steps."""

    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("idx_agent_runs_project_id", "project_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("projects.id", name="fk_agent_runs_project"),
        nullable=False,
    )
    node_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    input_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="agent_runs")
