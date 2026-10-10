"""Test database models and configuration loading."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models import (
    DocumentCreate,
    DocumentRead,
    DocumentSectionCreate,
    DocumentSectionRead,
    EvidenceItemCreate,
    EvidenceItemRead,
    ProjectCreate,
    ProjectRead,
)


def test_project_model_creation() -> None:
    """Test creating a ProjectCreate model instance."""
    now = datetime.now(timezone.utc)
    project = ProjectCreate(
        id="PRJ-001",
        name="Test Project",
        process_type="admissions",
        description="Test project description",
        status="draft",
        created_at=now,
        updated_at=now,
    )
    assert project.id == "PRJ-001"
    assert project.name == "Test Project"


def test_document_model_creation() -> None:
    """Test creating a DocumentCreate model instance."""
    doc = DocumentCreate(
        id="DOC-001",
        project_id="PRJ-001",
        filename="test.pdf",
        mime_type="application/pdf",
        checksum="abc123",
        version="1.0",
        storage_path="/storage/test.pdf",
    )
    assert doc.id == "DOC-001"
    assert doc.project_id == "PRJ-001"


def test_document_section_model_creation() -> None:
    """Test creating a DocumentSectionCreate model instance."""
    section = DocumentSectionCreate(
        id="SEC-001",
        document_id="DOC-001",
        page_number=1,
        section_title="Introduction",
        text="This is the introduction.",
    )
    assert section.id == "SEC-001"
    assert section.page_number == 1


def test_evidence_item_model_creation() -> None:
    """Test creating an EvidenceItemCreate model instance."""
    evidence = EvidenceItemCreate(
        id="EVD-001",
        project_id="PRJ-001",
        document_section_id="SEC-001",
        quote="This is evidence.",
        claim_type="process_step",
        confidence=Decimal("0.95"),
    )
    assert evidence.id == "EVD-001"
    assert evidence.confidence == Decimal("0.95")


def test_database_config_from_env(monkeypatch):
    """Test loading DatabaseConfig from environment variable."""
    test_dsn = "postgresql://user:pass@localhost:5432/processfoundry"
    monkeypatch.setenv("DATABASE_URL", test_dsn)

    config = DatabaseConfig.from_env()
    assert config.dsn == test_dsn


def test_database_config_missing_env(monkeypatch) -> None:
    """Test that DatabaseConfig.from_env raises error when env var is missing."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    try:
        DatabaseConfig.from_env()
        assert False, "Expected ValueError for missing DATABASE_URL"
    except ValueError as e:
        assert "DATABASE_URL" in str(e)


if __name__ == "__main__":
    print("Running model and config tests...")
    test_project_model_creation()
    print("✓ Project model creation")
    test_document_model_creation()
    print("✓ Document model creation")
    test_document_section_model_creation()
    print("✓ Document section model creation")
    test_evidence_item_model_creation()
    print("✓ Evidence item model creation")
    print("\nAll model tests passed!")
