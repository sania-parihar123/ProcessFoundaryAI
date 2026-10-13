"""Tests for SQLAlchemy ORM models, metadata, constraints, and relationships."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlalchemy.orm import class_mapper

from processfoundry_ai.database.base import Base
from processfoundry_ai.database.models import (
    AgentRun,
    Approval,
    Artifact,
    ArtifactLink,
    BusinessRule,
    ClarificationItem,
    Document,
    DocumentSection,
    EvidenceItem,
    ProcessStep,
    ProcessVersion,
    Project,
    Requirement,
    RequirementLink,
    RuleEvidence,
    TestCase,
)

CANONICAL_TABLES = {
    "projects",
    "documents",
    "document_sections",
    "evidence_items",
    "process_versions",
    "process_steps",
    "business_rules",
    "rule_evidence",
    "clarification_items",
    "requirements",
    "requirement_links",
    "artifacts",
    "artifact_links",
    "test_cases",
    "approvals",
    "agent_runs",
}


class TestORMMetadata:
    """Test ORM metadata configuration and table definitions."""

    def test_tables_registered_in_metadata(self) -> None:
        """Verify that all 16 canonical tables are registered in Base.metadata."""
        assert CANONICAL_TABLES == set(Base.metadata.tables.keys())

    def test_recommended_indexes_are_declared(self) -> None:
        """Verify SPEC-002 recommended indexes are present on ORM metadata."""
        expected = {
            "documents": ("idx_documents_project_id", ("project_id",)),
            "document_sections": ("idx_document_sections_document_id", ("document_id",)),
            "evidence_items": (
                "idx_evidence_items_project_id",
                ("project_id", "document_section_id"),
            ),
            "process_versions": ("idx_process_versions_project_id", ("project_id",)),
            "process_steps": (
                "idx_process_steps_process_version_id",
                ("process_version_id", "sequence"),
            ),
            "business_rules": ("idx_business_rules_project_id", ("project_id",)),
            "clarification_items": (
                "idx_clarification_items_project_id",
                ("project_id", "status"),
            ),
            "requirements": ("idx_requirements_project_id", ("project_id",)),
            "artifacts": (
                "idx_artifacts_project_id",
                ("project_id", "artifact_type"),
            ),
            "test_cases": (
                "idx_test_cases_project_id",
                ("project_id", "requirement_id"),
            ),
            "approvals": (
                "idx_approvals_project_id",
                ("project_id", "target_type", "target_id"),
            ),
            "agent_runs": (
                "idx_agent_runs_project_id",
                ("project_id", "created_at"),
            ),
        }
        for table_name, (index_name, columns) in expected.items():
            table = Base.metadata.tables[table_name]
            index = table.indexes
            match = next((idx for idx in index if idx.name == index_name), None)
            assert match is not None, f"Missing index {index_name} on {table_name}"
            assert tuple(col.name for col in match.columns) == columns

    def test_projects_table_columns_and_constraints(self) -> None:
        """Verify projects table columns, nullability, PK, and check constraint."""
        table = Base.metadata.tables["projects"]

        # Check primary key
        assert [c.name for c in table.primary_key.columns] == ["id"]

        # Check column types and nullability
        expected_columns = {
            "id": False,
            "name": False,
            "process_type": False,
            "description": False,
            "status": False,
            "created_at": False,
            "updated_at": False,
        }
        for col_name, nullable in expected_columns.items():
            col = table.columns[col_name]
            assert col.nullable is nullable, f"Column {col_name} nullable mismatch"

        # Check check constraint
        check_constraints = [
            c for c in table.constraints if isinstance(c, CheckConstraint)
        ]
        assert len(check_constraints) >= 1
        check_sql = str(check_constraints[0].sqltext)
        assert "btrim(name)" in check_sql

    def test_documents_table_columns_and_foreign_keys(self) -> None:
        """Verify documents table columns, PK, and foreign keys."""
        table = Base.metadata.tables["documents"]

        # Check primary key
        assert [c.name for c in table.primary_key.columns] == ["id"]

        # Check columns
        expected_columns = {
            "id": False,
            "project_id": False,
            "filename": False,
            "mime_type": False,
            "checksum": False,
            "version": False,
            "storage_path": False,
        }
        for col_name, nullable in expected_columns.items():
            col = table.columns[col_name]
            assert col.nullable is nullable, f"Column {col_name} nullable mismatch"

        # Check foreign keys
        fk_constraints = [
            c for c in table.constraints if isinstance(c, ForeignKeyConstraint)
        ]
        assert any(
            c.name == "fk_documents_project" and c.elements[0].target_fullname == "projects.id"
            for c in fk_constraints
        )

    def test_document_sections_table_columns_and_foreign_keys(self) -> None:
        """Verify document_sections table columns, PK, and foreign keys."""
        table = Base.metadata.tables["document_sections"]

        # Check primary key
        assert [c.name for c in table.primary_key.columns] == ["id"]

        # Check columns
        expected_columns = {
            "id": False,
            "document_id": False,
            "page_number": True,  # nullable
            "section_title": True,  # nullable
            "text": False,
        }
        for col_name, nullable in expected_columns.items():
            col = table.columns[col_name]
            assert col.nullable is nullable, f"Column {col_name} nullable mismatch"

        # Check foreign keys
        fk_constraints = [
            c for c in table.constraints if isinstance(c, ForeignKeyConstraint)
        ]
        assert any(
            c.name == "fk_document_sections_document"
            and c.elements[0].target_fullname == "documents.id"
            for c in fk_constraints
        )

    def test_evidence_items_table_columns_and_foreign_keys(self) -> None:
        """Verify evidence_items table columns, PK, and foreign keys."""
        table = Base.metadata.tables["evidence_items"]

        # Check primary key
        assert [c.name for c in table.primary_key.columns] == ["id"]

        # Check columns
        expected_columns = {
            "id": False,
            "project_id": False,
            "document_section_id": False,
            "quote": False,
            "claim_type": False,
            "confidence": False,
        }
        for col_name, nullable in expected_columns.items():
            col = table.columns[col_name]
            assert col.nullable is nullable, f"Column {col_name} nullable mismatch"

        # Check foreign keys
        fk_constraints = [
            c for c in table.constraints if isinstance(c, ForeignKeyConstraint)
        ]
        assert any(
            c.name == "fk_evidence_items_project"
            and c.elements[0].target_fullname == "projects.id"
            for c in fk_constraints
        )
        assert any(
            c.name == "fk_evidence_items_document_section"
            and c.elements[0].target_fullname == "document_sections.id"
            for c in fk_constraints
        )

    def test_composite_primary_keys_for_link_tables(self) -> None:
        """Verify link tables use the SPEC-001 composite primary keys."""
        expected = {
            "rule_evidence": ("rule_id", "evidence_id"),
            "requirement_links": ("source_requirement_id", "target_id", "link_type"),
            "artifact_links": ("artifact_id", "target_type", "target_id", "link_type"),
        }
        for table_name, columns in expected.items():
            table = Base.metadata.tables[table_name]
            pk = next(
                c for c in table.constraints if isinstance(c, PrimaryKeyConstraint)
            )
            assert tuple(col.name for col in pk.columns) == columns


class TestORMRelationships:
    """Test relationships configured on ORM models."""

    def test_project_relationships(self) -> None:
        """Verify Project has relationships to child entities in SPEC-001."""
        mapper = class_mapper(Project)
        for rel_name in (
            "documents",
            "evidence_items",
            "process_versions",
            "business_rules",
            "clarification_items",
            "requirements",
            "artifacts",
            "test_cases",
            "approvals",
            "agent_runs",
        ):
            assert rel_name in mapper.relationships

        doc_rel = mapper.relationships["documents"]
        assert doc_rel.entity.class_ == Document
        assert doc_rel.back_populates == "project"

        evd_rel = mapper.relationships["evidence_items"]
        assert evd_rel.entity.class_ == EvidenceItem
        assert evd_rel.back_populates == "project"

    def test_document_relationships(self) -> None:
        """Verify Document has relationships to Project and DocumentSection."""
        mapper = class_mapper(Document)
        assert "project" in mapper.relationships
        assert "sections" in mapper.relationships

        proj_rel = mapper.relationships["project"]
        assert proj_rel.entity.class_ == Project
        assert proj_rel.back_populates == "documents"

        sec_rel = mapper.relationships["sections"]
        assert sec_rel.entity.class_ == DocumentSection
        assert sec_rel.back_populates == "document"

    def test_document_section_relationships(self) -> None:
        """Verify DocumentSection has relationships to Document and EvidenceItem."""
        mapper = class_mapper(DocumentSection)
        assert "document" in mapper.relationships
        assert "evidence_items" in mapper.relationships

        doc_rel = mapper.relationships["document"]
        assert doc_rel.entity.class_ == Document
        assert doc_rel.back_populates == "sections"

        evd_rel = mapper.relationships["evidence_items"]
        assert evd_rel.entity.class_ == EvidenceItem
        assert evd_rel.back_populates == "document_section"

    def test_evidence_item_relationships(self) -> None:
        """Verify EvidenceItem has relationships to Project and DocumentSection."""
        mapper = class_mapper(EvidenceItem)
        assert "project" in mapper.relationships
        assert "document_section" in mapper.relationships

        proj_rel = mapper.relationships["project"]
        assert proj_rel.entity.class_ == Project
        assert proj_rel.back_populates == "evidence_items"

        sec_rel = mapper.relationships["document_section"]
        assert sec_rel.entity.class_ == DocumentSection
        assert sec_rel.back_populates == "evidence_items"

    def test_core_models_can_be_constructed(self) -> None:
        """Verify canonical ORM models accept SPEC-001 fields."""
        now = datetime.now(timezone.utc)
        p = Project(
            id="P1",
            name="N1",
            process_type="T1",
            description="D1",
            status="draft",
            created_at=now,
            updated_at=now,
        )
        assert p.id == "P1"

        d = Document(
            id="D1",
            project_id="P1",
            filename="f.pdf",
            mime_type="app/pdf",
            checksum="c",
            version="1",
            storage_path="p",
        )
        assert d.project_id == "P1"

        s = DocumentSection(
            id="S1",
            document_id="D1",
            page_number=1,
            section_title="title",
            text="t",
        )
        assert s.text == "t"

        e = EvidenceItem(
            id="E1",
            project_id="P1",
            document_section_id="S1",
            quote="q",
            claim_type="claim",
            confidence=Decimal("0.9"),
        )
        assert e.confidence == Decimal("0.9")

        assert ProcessVersion.__tablename__ == "process_versions"
        assert ProcessStep.__tablename__ == "process_steps"
        assert BusinessRule.__tablename__ == "business_rules"
        assert RuleEvidence.__tablename__ == "rule_evidence"
        assert ClarificationItem.__tablename__ == "clarification_items"
        assert Requirement.__tablename__ == "requirements"
        assert RequirementLink.__tablename__ == "requirement_links"
        assert Artifact.__tablename__ == "artifacts"
        assert ArtifactLink.__tablename__ == "artifact_links"
        assert TestCase.__tablename__ == "test_cases"
        assert Approval.__tablename__ == "approvals"
        assert AgentRun.__tablename__ == "agent_runs"
