"""Tests for document, document section, and evidence item repositories with SQLAlchemy ORM."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import (
    Document as DocumentORM,
    DocumentSection as DocumentSectionORM,
    EvidenceItem as EvidenceItemORM,
)
from processfoundry_ai.models.document import DocumentCreate, DocumentRead
from processfoundry_ai.models.document_section import (
    DocumentSectionCreate,
    DocumentSectionRead,
)
from processfoundry_ai.models.evidence_item import EvidenceItemCreate, EvidenceItemRead
from processfoundry_ai.repositories.document_repository import DocumentRepository
from processfoundry_ai.repositories.document_section_repository import (
    DocumentSectionRepository,
)
from processfoundry_ai.repositories.evidence_item_repository import (
    EvidenceItemRepository,
)


@pytest.fixture
def db_config() -> DatabaseConfig:
    """Provide a test database configuration."""
    return DatabaseConfig(dsn="postgresql://test:test@localhost:5432/test_db")


@pytest.fixture
def sample_document_create() -> DocumentCreate:
    """Provide a sample DocumentCreate model."""
    return DocumentCreate(
        id="DOC-001",
        project_id="PRJ-001",
        filename="test_document.pdf",
        mime_type="application/pdf",
        checksum="sha256abc123",
        version="1.0",
        storage_path="/storage/documents/test_document.pdf",
    )


@pytest.fixture
def sample_document_read() -> DocumentRead:
    """Provide a sample DocumentRead model."""
    return DocumentRead(
        id="DOC-001",
        project_id="PRJ-001",
        filename="test_document.pdf",
        mime_type="application/pdf",
        checksum="sha256abc123",
        version="1.0",
        storage_path="/storage/documents/test_document.pdf",
    )


@pytest.fixture
def sample_document_orm() -> DocumentORM:
    """Provide a sample DocumentORM instance."""
    return DocumentORM(
        id="DOC-001",
        project_id="PRJ-001",
        filename="test_document.pdf",
        mime_type="application/pdf",
        checksum="sha256abc123",
        version="1.0",
        storage_path="/storage/documents/test_document.pdf",
    )


@pytest.fixture
def sample_section_create() -> DocumentSectionCreate:
    """Provide a sample DocumentSectionCreate model."""
    return DocumentSectionCreate(
        id="SEC-001",
        document_id="DOC-001",
        page_number=1,
        section_title="Introduction",
        text="This is the introduction section of the document.",
    )


@pytest.fixture
def sample_section_read() -> DocumentSectionRead:
    """Provide a sample DocumentSectionRead model."""
    return DocumentSectionRead(
        id="SEC-001",
        document_id="DOC-001",
        page_number=1,
        section_title="Introduction",
        text="This is the introduction section of the document.",
    )


@pytest.fixture
def sample_section_orm() -> DocumentSectionORM:
    """Provide a sample DocumentSectionORM instance."""
    return DocumentSectionORM(
        id="SEC-001",
        document_id="DOC-001",
        page_number=1,
        section_title="Introduction",
        text="This is the introduction section of the document.",
    )


@pytest.fixture
def sample_evidence_create() -> EvidenceItemCreate:
    """Provide a sample EvidenceItemCreate model."""
    return EvidenceItemCreate(
        id="EVD-001",
        project_id="PRJ-001",
        document_section_id="SEC-001",
        quote="A key quote from the section",
        claim_type="process_step",
        confidence=Decimal("0.95"),
    )


@pytest.fixture
def sample_evidence_read() -> EvidenceItemRead:
    """Provide a sample EvidenceItemRead model."""
    return EvidenceItemRead(
        id="EVD-001",
        project_id="PRJ-001",
        document_section_id="SEC-001",
        quote="A key quote from the section",
        claim_type="process_step",
        confidence=Decimal("0.95"),
    )


@pytest.fixture
def sample_evidence_orm() -> EvidenceItemORM:
    """Provide a sample EvidenceItemORM instance."""
    return EvidenceItemORM(
        id="EVD-001",
        project_id="PRJ-001",
        document_section_id="SEC-001",
        quote="A key quote from the section",
        claim_type="process_step",
        confidence=Decimal("0.95"),
    )


# ============================================================================
# DocumentRepository Tests
# ============================================================================


class TestDocumentRepositoryCreate:
    """Test DocumentRepository.create() method."""

    @patch("processfoundry_ai.repositories.document_repository.session_context")
    def test_create_document_success(
        self, mock_session_context, db_config, sample_document_create
    ) -> None:
        """Test successful document creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = DocumentRepository(db_config)
        result = repo.create(sample_document_create)

        assert result.id == "DOC-001"
        assert result.project_id == "PRJ-001"
        assert result.filename == "test_document.pdf"
        assert result.mime_type == "application/pdf"
        assert result.checksum == "sha256abc123"
        assert result.version == "1.0"
        assert result.storage_path == "/storage/documents/test_document.pdf"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch("processfoundry_ai.repositories.document_repository.session_context")
    def test_create_document_foreign_key_error(
        self, mock_session_context, db_config, sample_document_create
    ) -> None:
        """Test document creation with database error (e.g., foreign key)."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.commit.side_effect = SQLAlchemyError("Foreign key constraint")

        repo = DocumentRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_document_create)


class TestDocumentRepositoryGetById:
    """Test DocumentRepository.get_by_id() method."""

    @patch("processfoundry_ai.repositories.document_repository.session_context")
    def test_get_by_id_success(
        self, mock_session_context, db_config, sample_document_orm
    ) -> None:
        """Test successful document retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.first.return_value = sample_document_orm

        repo = DocumentRepository(db_config)
        result = repo.get_by_id("DOC-001")

        assert result is not None
        assert result.id == "DOC-001"
        assert result.project_id == "PRJ-001"
        assert result.filename == "test_document.pdf"
        mock_session.scalars.assert_called_once()

    @patch("processfoundry_ai.repositories.document_repository.session_context")
    def test_get_by_id_not_found(self, mock_session_context, db_config) -> None:
        """Test document retrieval when not found."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.first.return_value = None

        repo = DocumentRepository(db_config)
        result = repo.get_by_id("NONEXISTENT")

        assert result is None

    @patch("processfoundry_ai.repositories.document_repository.session_context")
    def test_get_by_id_database_error(self, mock_session_context, db_config) -> None:
        """Test document retrieval with database error."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.scalars.side_effect = SQLAlchemyError("Connection failed")

        repo = DocumentRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.get_by_id("DOC-001")


class TestDocumentRepositoryListByProject:
    """Test DocumentRepository.list_by_project() method."""

    @patch("processfoundry_ai.repositories.document_repository.session_context")
    def test_list_by_project_success(self, mock_session_context, db_config) -> None:
        """Test successful listing of documents for a project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session

        doc1 = DocumentORM(
            id="DOC-001",
            project_id="PRJ-001",
            filename="doc1.pdf",
            mime_type="application/pdf",
            checksum="abc123",
            version="1.0",
            storage_path="/storage/doc1.pdf",
        )
        doc2 = DocumentORM(
            id="DOC-002",
            project_id="PRJ-001",
            filename="doc2.pdf",
            mime_type="application/pdf",
            checksum="def456",
            version="1.0",
            storage_path="/storage/doc2.pdf",
        )
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = [doc1, doc2]

        repo = DocumentRepository(db_config)
        results = repo.list_by_project("PRJ-001")

        assert len(results) == 2
        assert all(isinstance(r, DocumentRead) for r in results)
        assert all(r.project_id == "PRJ-001" for r in results)
        assert results[0].id == "DOC-001"
        assert results[1].id == "DOC-002"

    @patch("processfoundry_ai.repositories.document_repository.session_context")
    def test_list_by_project_empty(self, mock_session_context, db_config) -> None:
        """Test listing documents when none exist for project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = []

        repo = DocumentRepository(db_config)
        results = repo.list_by_project("EMPTY-PROJECT")

        assert results == []

    @patch("processfoundry_ai.repositories.document_repository.session_context")
    def test_list_by_project_database_error(self, mock_session_context, db_config) -> None:
        """Test listing documents with database error."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.scalars.side_effect = SQLAlchemyError("Query failed")

        repo = DocumentRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.list_by_project("PRJ-001")


# ============================================================================
# DocumentSectionRepository Tests
# ============================================================================


class TestDocumentSectionRepositoryCreate:
    """Test DocumentSectionRepository.create() method."""

    @patch(
        "processfoundry_ai.repositories.document_section_repository.session_context"
    )
    def test_create_section_success(
        self, mock_session_context, db_config, sample_section_create
    ) -> None:
        """Test successful document section creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = DocumentSectionRepository(db_config)
        result = repo.create(sample_section_create)

        assert result.id == "SEC-001"
        assert result.document_id == "DOC-001"
        assert result.page_number == 1
        assert result.section_title == "Introduction"
        assert result.text == "This is the introduction section of the document."
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch(
        "processfoundry_ai.repositories.document_section_repository.session_context"
    )
    def test_create_section_foreign_key_error(
        self, mock_session_context, db_config, sample_section_create
    ) -> None:
        """Test section creation with database error."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.commit.side_effect = SQLAlchemyError("Foreign key constraint")

        repo = DocumentSectionRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_section_create)


class TestDocumentSectionRepositoryGetById:
    """Test DocumentSectionRepository.get_by_id() method."""

    @patch(
        "processfoundry_ai.repositories.document_section_repository.session_context"
    )
    def test_get_by_id_success(
        self, mock_session_context, db_config, sample_section_orm
    ) -> None:
        """Test successful document section retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.first.return_value = sample_section_orm

        repo = DocumentSectionRepository(db_config)
        result = repo.get_by_id("SEC-001")

        assert result is not None
        assert result.id == "SEC-001"
        assert result.document_id == "DOC-001"
        assert result.page_number == 1
        assert result.section_title == "Introduction"

    @patch(
        "processfoundry_ai.repositories.document_section_repository.session_context"
    )
    def test_get_by_id_not_found(self, mock_session_context, db_config) -> None:
        """Test document section retrieval when not found."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.first.return_value = None

        repo = DocumentSectionRepository(db_config)
        result = repo.get_by_id("NONEXISTENT")

        assert result is None

    @patch(
        "processfoundry_ai.repositories.document_section_repository.session_context"
    )
    def test_get_by_id_database_error(self, mock_session_context, db_config) -> None:
        """Test document section retrieval with database error."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.scalars.side_effect = SQLAlchemyError("Connection failed")

        repo = DocumentSectionRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.get_by_id("SEC-001")


class TestDocumentSectionRepositoryListByDocument:
    """Test DocumentSectionRepository.list_by_document() method."""

    @patch(
        "processfoundry_ai.repositories.document_section_repository.session_context"
    )
    def test_list_by_document_success(self, mock_session_context, db_config) -> None:
        """Test successful listing of sections for a document."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session

        sec1 = DocumentSectionORM(
            id="SEC-001",
            document_id="DOC-001",
            page_number=1,
            section_title="Introduction",
            text="Intro text",
        )
        sec2 = DocumentSectionORM(
            id="SEC-002",
            document_id="DOC-001",
            page_number=2,
            section_title="Body",
            text="Body text",
        )
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = [sec1, sec2]

        repo = DocumentSectionRepository(db_config)
        results = repo.list_by_document("DOC-001")

        assert len(results) == 2
        assert all(isinstance(r, DocumentSectionRead) for r in results)
        assert all(r.document_id == "DOC-001" for r in results)
        assert results[0].id == "SEC-001"
        assert results[1].id == "SEC-002"

    @patch(
        "processfoundry_ai.repositories.document_section_repository.session_context"
    )
    def test_list_by_document_empty(self, mock_session_context, db_config) -> None:
        """Test listing sections when none exist for document."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = []

        repo = DocumentSectionRepository(db_config)
        results = repo.list_by_document("EMPTY-DOC")

        assert results == []

    @patch(
        "processfoundry_ai.repositories.document_section_repository.session_context"
    )
    def test_list_by_document_database_error(
        self, mock_session_context, db_config
    ) -> None:
        """Test listing sections with database error."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.scalars.side_effect = SQLAlchemyError("Query failed")

        repo = DocumentSectionRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.list_by_document("DOC-001")


# ============================================================================
# EvidenceItemRepository Tests
# ============================================================================


class TestEvidenceItemRepositoryCreate:
    """Test EvidenceItemRepository.create() method."""

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_create_evidence_success(
        self, mock_session_context, db_config, sample_evidence_create
    ) -> None:
        """Test successful evidence item creation."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session_context.return_value.__exit__.return_value = None

        repo = EvidenceItemRepository(db_config)
        result = repo.create(sample_evidence_create)

        assert result.id == "EVD-001"
        assert result.project_id == "PRJ-001"
        assert result.document_section_id == "SEC-001"
        assert result.quote == "A key quote from the section"
        assert result.claim_type == "process_step"
        assert result.confidence == Decimal("0.95")
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_create_evidence_foreign_key_project_error(
        self, mock_session_context, db_config, sample_evidence_create
    ) -> None:
        """Test evidence creation with invalid project_id."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.commit.side_effect = SQLAlchemyError("Foreign key violation: project")

        repo = EvidenceItemRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_evidence_create)

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_create_evidence_foreign_key_section_error(
        self, mock_session_context, db_config, sample_evidence_create
    ) -> None:
        """Test evidence creation with invalid document_section_id."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.commit.side_effect = SQLAlchemyError(
            "Foreign key violation: document_section"
        )

        repo = EvidenceItemRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_evidence_create)


class TestEvidenceItemRepositoryGetById:
    """Test EvidenceItemRepository.get_by_id() method."""

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_get_by_id_success(
        self, mock_session_context, db_config, sample_evidence_orm
    ) -> None:
        """Test successful evidence item retrieval by ID."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.first.return_value = sample_evidence_orm

        repo = EvidenceItemRepository(db_config)
        result = repo.get_by_id("EVD-001")

        assert result is not None
        assert result.id == "EVD-001"
        assert result.project_id == "PRJ-001"
        assert result.document_section_id == "SEC-001"
        assert result.confidence == Decimal("0.95")

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_get_by_id_not_found(self, mock_session_context, db_config) -> None:
        """Test evidence item retrieval when not found."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.first.return_value = None

        repo = EvidenceItemRepository(db_config)
        result = repo.get_by_id("NONEXISTENT")

        assert result is None

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_get_by_id_database_error(self, mock_session_context, db_config) -> None:
        """Test evidence item retrieval with database error."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.scalars.side_effect = SQLAlchemyError("Connection failed")

        repo = EvidenceItemRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.get_by_id("EVD-001")


class TestEvidenceItemRepositoryListByProject:
    """Test EvidenceItemRepository.list_by_project() method."""

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_list_by_project_success(self, mock_session_context, db_config) -> None:
        """Test successful listing of evidence items for a project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session

        item1 = EvidenceItemORM(
            id="EVD-001",
            project_id="PRJ-001",
            document_section_id="SEC-001",
            quote="Quote 1",
            claim_type="process_step",
            confidence=Decimal("0.95"),
        )
        item2 = EvidenceItemORM(
            id="EVD-002",
            project_id="PRJ-001",
            document_section_id="SEC-002",
            quote="Quote 2",
            claim_type="decision",
            confidence=Decimal("0.85"),
        )
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = [item1, item2]

        repo = EvidenceItemRepository(db_config)
        results = repo.list_by_project("PRJ-001")

        assert len(results) == 2
        assert all(isinstance(r, EvidenceItemRead) for r in results)
        assert all(r.project_id == "PRJ-001" for r in results)

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_list_by_project_empty(self, mock_session_context, db_config) -> None:
        """Test listing evidence items when none exist for project."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = []

        repo = EvidenceItemRepository(db_config)
        results = repo.list_by_project("EMPTY-PROJECT")

        assert results == []

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_list_by_project_database_error(
        self, mock_session_context, db_config
    ) -> None:
        """Test listing evidence items with database error."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.scalars.side_effect = SQLAlchemyError("Query failed")

        repo = EvidenceItemRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.list_by_project("PRJ-001")


class TestEvidenceItemRepositoryListByDocumentSection:
    """Test EvidenceItemRepository.list_by_document_section() method (traceability)."""

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_list_by_document_section_success(
        self, mock_session_context, db_config
    ) -> None:
        """Test successful listing of evidence items by document section (traceability)."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session

        item1 = EvidenceItemORM(
            id="EVD-001",
            project_id="PRJ-001",
            document_section_id="SEC-001",
            quote="Quote from section",
            claim_type="process_step",
            confidence=Decimal("0.95"),
        )
        item2 = EvidenceItemORM(
            id="EVD-003",
            project_id="PRJ-001",
            document_section_id="SEC-001",
            quote="Another quote",
            claim_type="decision",
            confidence=Decimal("0.87"),
        )
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = [item1, item2]

        repo = EvidenceItemRepository(db_config)
        results = repo.list_by_document_section("SEC-001")

        assert len(results) == 2
        assert all(isinstance(r, EvidenceItemRead) for r in results)
        assert all(r.document_section_id == "SEC-001" for r in results)
        assert results[0].confidence >= results[1].confidence

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_list_by_document_section_empty(
        self, mock_session_context, db_config
    ) -> None:
        """Test listing evidence for a section with no evidence."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_scalars = MagicMock()
        mock_session.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = []

        repo = EvidenceItemRepository(db_config)
        results = repo.list_by_document_section("EMPTY-SECTION")

        assert results == []

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_list_by_document_section_database_error(
        self, mock_session_context, db_config
    ) -> None:
        """Test listing evidence items with database error."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.scalars.side_effect = SQLAlchemyError("Query failed")

        repo = EvidenceItemRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.list_by_document_section("SEC-001")


# ============================================================================
# Session / Connection Handling Tests
# ============================================================================


class TestConnectionHandling:
    """Test session lifecycle and resource handling across repositories."""

    @patch("processfoundry_ai.repositories.document_repository.session_context")
    def test_document_connection_closed_on_error(
        self, mock_session_context, db_config, sample_document_create
    ) -> None:
        """Test that sessions are closed when document operations fail."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Insert error")

        repo = DocumentRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_document_create)

        mock_session_context.return_value.__exit__.assert_called_once()

    @patch(
        "processfoundry_ai.repositories.document_section_repository.session_context"
    )
    def test_section_connection_closed_on_error(
        self, mock_session_context, db_config, sample_section_create
    ) -> None:
        """Test that sessions are closed when section operations fail."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Insert error")

        repo = DocumentSectionRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_section_create)

        mock_session_context.return_value.__exit__.assert_called_once()

    @patch("processfoundry_ai.repositories.evidence_item_repository.session_context")
    def test_evidence_connection_closed_on_error(
        self, mock_session_context, db_config, sample_evidence_create
    ) -> None:
        """Test that sessions are closed when evidence operations fail."""
        mock_session = MagicMock()
        mock_session_context.return_value.__enter__.return_value = mock_session
        mock_session.add.side_effect = SQLAlchemyError("Insert error")

        repo = EvidenceItemRepository(db_config)
        with pytest.raises(SQLAlchemyError):
            repo.create(sample_evidence_create)

        mock_session_context.return_value.__exit__.assert_called_once()
