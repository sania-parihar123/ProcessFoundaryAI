"""Functional tests for all four repositories using in-memory SQLite database."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.base import Base
from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.session import dispose_engine, get_engine
from processfoundry_ai.models.document import DocumentCreate
from processfoundry_ai.models.document_section import DocumentSectionCreate
from processfoundry_ai.models.evidence_item import EvidenceItemCreate
from processfoundry_ai.models.project import ProjectCreate
from processfoundry_ai.repositories.document_repository import DocumentRepository
from processfoundry_ai.repositories.document_section_repository import (
    DocumentSectionRepository,
)
from processfoundry_ai.repositories.evidence_item_repository import (
    EvidenceItemRepository,
)
from processfoundry_ai.repositories.project_repository import ProjectRepository


@pytest.fixture
def sqlite_config():
    """Create in-memory SQLite database configuration with tables initialized."""
    dispose_engine()
    config = DatabaseConfig(dsn="sqlite:///:memory:")
    engine = get_engine(config)
    Base.metadata.create_all(engine)
    yield config
    Base.metadata.drop_all(engine)
    dispose_engine()


class TestRepositoriesSQLiteIntegration:
    """Test repository CRUD operations and constraints against real SQLite database."""

    def test_project_crud_and_check_constraint(self, sqlite_config) -> None:
        """Test ProjectRepository create, get, list, and check constraint on real DB."""
        repo = ProjectRepository(sqlite_config)
        now = datetime.now(timezone.utc)

        # 1. Create project
        proj_in = ProjectCreate(
            id="PRJ-100",
            name="Admissions Optimization",
            process_type="admissions",
            description="Process discovery for freshman admissions",
            status="active",
            created_at=now,
            updated_at=now,
        )
        created = repo.create(proj_in)
        assert created.id == "PRJ-100"
        assert created.name == "Admissions Optimization"

        # 2. Get by ID
        found = repo.get_by_id("PRJ-100")
        assert found is not None
        assert found.id == "PRJ-100"
        assert found.name == "Admissions Optimization"

        # 3. Get non-existent
        not_found = repo.get_by_id("PRJ-NONEXISTENT")
        assert not_found is None

        # 4. List projects
        projects = repo.list_projects()
        assert len(projects) == 1
        assert projects[0].id == "PRJ-100"

        # 5. Check constraint validation: whitespace-only name
        # Pydantic validates at model level; test direct DB constraint via invalid construction
        with pytest.raises(SQLAlchemyError):
            # Bypass Pydantic validator by creating ORM directly with whitespace name
            from processfoundry_ai.database.models import Project as ProjectORM
            from processfoundry_ai.database.session import session_context

            with session_context(sqlite_config) as session:
                invalid_p = ProjectORM(
                    id="PRJ-INVALID",
                    name="   ",
                    process_type="test",
                    description="test",
                    status="draft",
                    created_at=now,
                    updated_at=now,
                )
                session.add(invalid_p)
                session.commit()

    def test_document_crud_and_foreign_key(self, sqlite_config) -> None:
        """Test DocumentRepository create, get, list, and foreign key constraint."""
        proj_repo = ProjectRepository(sqlite_config)
        doc_repo = DocumentRepository(sqlite_config)
        now = datetime.now(timezone.utc)

        # Create parent project
        proj_repo.create(
            ProjectCreate(
                id="PRJ-200",
                name="Financial Aid Review",
                process_type="financial_aid",
                description="Auditing financial aid process",
                status="draft",
                created_at=now,
                updated_at=now,
            )
        )

        # 1. Create document
        doc_in = DocumentCreate(
            id="DOC-200",
            project_id="PRJ-200",
            filename="financial_aid_policy.pdf",
            mime_type="application/pdf",
            checksum="abcde12345",
            version="1.0",
            storage_path="/files/financial_aid_policy.pdf",
        )
        created_doc = doc_repo.create(doc_in)
        assert created_doc.id == "DOC-200"
        assert created_doc.project_id == "PRJ-200"

        # 2. Get by ID
        found_doc = doc_repo.get_by_id("DOC-200")
        assert found_doc is not None
        assert found_doc.filename == "financial_aid_policy.pdf"

        # 3. List by project
        docs = doc_repo.list_by_project("PRJ-200")
        assert len(docs) == 1
        assert docs[0].id == "DOC-200"

        # 4. Foreign key constraint rejection
        with pytest.raises(SQLAlchemyError):
            doc_repo.create(
                DocumentCreate(
                    id="DOC-INVALID",
                    project_id="NONEXISTENT-PROJECT",
                    filename="orphan.pdf",
                    mime_type="application/pdf",
                    checksum="xyz",
                    version="1.0",
                    storage_path="/files/orphan.pdf",
                )
            )

    def test_document_section_crud_and_foreign_key(self, sqlite_config) -> None:
        """Test DocumentSectionRepository create, get, list, and foreign key."""
        proj_repo = ProjectRepository(sqlite_config)
        doc_repo = DocumentRepository(sqlite_config)
        sec_repo = DocumentSectionRepository(sqlite_config)
        now = datetime.now(timezone.utc)

        proj_repo.create(
            ProjectCreate(
                id="PRJ-300",
                name="Curriculum Design",
                process_type="academics",
                description="Curriculum redesign",
                status="draft",
                created_at=now,
                updated_at=now,
            )
        )
        doc_repo.create(
            DocumentCreate(
                id="DOC-300",
                project_id="PRJ-300",
                filename="syllabus.docx",
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                checksum="checksum300",
                version="1.0",
                storage_path="/files/syllabus.docx",
            )
        )

        # 1. Create section
        sec_in = DocumentSectionCreate(
            id="SEC-300",
            document_id="DOC-300",
            page_number=2,
            section_title="Course Objectives",
            text="Students will learn advanced software engineering principles.",
        )
        created_sec = sec_repo.create(sec_in)
        assert created_sec.id == "SEC-300"
        assert created_sec.document_id == "DOC-300"

        # 2. Get by ID
        found_sec = sec_repo.get_by_id("SEC-300")
        assert found_sec is not None
        assert found_sec.section_title == "Course Objectives"

        # 3. List by document
        sections = sec_repo.list_by_document("DOC-300")
        assert len(sections) == 1
        assert sections[0].id == "SEC-300"

        # 4. Foreign key constraint rejection
        with pytest.raises(SQLAlchemyError):
            sec_repo.create(
                DocumentSectionCreate(
                    id="SEC-INVALID",
                    document_id="NONEXISTENT-DOC",
                    page_number=1,
                    section_title="None",
                    text="Invalid text",
                )
            )

    def test_evidence_item_crud_and_traceability(self, sqlite_config) -> None:
        """Test EvidenceItemRepository create, get, list, and foreign keys."""
        proj_repo = ProjectRepository(sqlite_config)
        doc_repo = DocumentRepository(sqlite_config)
        sec_repo = DocumentSectionRepository(sqlite_config)
        evd_repo = EvidenceItemRepository(sqlite_config)
        now = datetime.now(timezone.utc)

        proj_repo.create(
            ProjectCreate(
                id="PRJ-400",
                name="Graduation Verification",
                process_type="records",
                description="Verification process",
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
        doc_repo.create(
            DocumentCreate(
                id="DOC-400",
                project_id="PRJ-400",
                filename="audit.pdf",
                mime_type="application/pdf",
                checksum="audit123",
                version="1.0",
                storage_path="/files/audit.pdf",
            )
        )
        sec_repo.create(
            DocumentSectionCreate(
                id="SEC-400",
                document_id="DOC-400",
                page_number=5,
                section_title="Credit Requirements",
                text="A minimum of 120 credit hours is required for graduation.",
            )
        )

        # 1. Create evidence item
        evd_in = EvidenceItemCreate(
            id="EVD-400",
            project_id="PRJ-400",
            document_section_id="SEC-400",
            quote="minimum of 120 credit hours is required",
            claim_type="requirement",
            confidence=Decimal("0.98"),
        )
        created_evd = evd_repo.create(evd_in)
        assert created_evd.id == "EVD-400"
        assert created_evd.confidence == Decimal("0.98")

        # 2. Get by ID
        found_evd = evd_repo.get_by_id("EVD-400")
        assert found_evd is not None
        assert found_evd.id == "EVD-400"
        assert found_evd.quote == "minimum of 120 credit hours is required"

        # 3. List by project
        evd_list_proj = evd_repo.list_by_project("PRJ-400")
        assert len(evd_list_proj) == 1
        assert evd_list_proj[0].id == "EVD-400"

        # 4. List by document section (traceability)
        evd_list_sec = evd_repo.list_by_document_section("SEC-400")
        assert len(evd_list_sec) == 1
        assert evd_list_sec[0].id == "EVD-400"

        # 5. Foreign key constraint rejection on invalid project
        with pytest.raises(SQLAlchemyError):
            evd_repo.create(
                EvidenceItemCreate(
                    id="EVD-BAD-PROJ",
                    project_id="PRJ-NONEXISTENT",
                    document_section_id="SEC-400",
                    quote="quote",
                    claim_type="type",
                    confidence=Decimal("0.5"),
                )
            )

        # 6. Foreign key constraint rejection on invalid section
        with pytest.raises(SQLAlchemyError):
            evd_repo.create(
                EvidenceItemCreate(
                    id="EVD-BAD-SEC",
                    project_id="PRJ-400",
                    document_section_id="SEC-NONEXISTENT",
                    quote="quote",
                    claim_type="type",
                    confidence=Decimal("0.5"),
                )
            )
