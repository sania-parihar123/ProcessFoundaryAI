"""Tests for document, document section, and evidence item repositories."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from psycopg import Error as PsycopgError

from processfoundry_ai.database.config import DatabaseConfig
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


# ============================================================================
# DocumentRepository Tests
# ============================================================================


class TestDocumentRepositoryCreate:
    """Test DocumentRepository.create() method."""

    @patch("processfoundry_ai.repositories.document_repository.get_connection")
    def test_create_document_success(
        self, mock_get_connection, db_config, sample_document_create
    ) -> None:
        """Test successful document creation."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": "DOC-001",
            "project_id": "PRJ-001",
            "filename": "test_document.pdf",
            "mime_type": "application/pdf",
            "checksum": "sha256abc123",
            "version": "1.0",
            "storage_path": "/storage/documents/test_document.pdf",
        }

        repo = DocumentRepository(db_config)
        result = repo.create(sample_document_create)

        assert result.id == "DOC-001"
        assert result.project_id == "PRJ-001"
        assert result.filename == "test_document.pdf"
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("processfoundry_ai.repositories.document_repository.get_connection")
    def test_create_document_uses_parameterized_query(
        self, mock_get_connection, db_config, sample_document_create
    ) -> None:
        """Test that create uses parameterized SQL queries."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": sample_document_create.id,
            "project_id": sample_document_create.project_id,
            "filename": sample_document_create.filename,
            "mime_type": sample_document_create.mime_type,
            "checksum": sample_document_create.checksum,
            "version": sample_document_create.version,
            "storage_path": sample_document_create.storage_path,
        }

        repo = DocumentRepository(db_config)
        repo.create(sample_document_create)

        args = mock_cursor.execute.call_args
        assert isinstance(args[0][0], str)
        assert "%s" in args[0][0]
        assert isinstance(args[0][1], tuple)

    @patch("processfoundry_ai.repositories.document_repository.get_connection")
    def test_create_document_foreign_key_error(
        self, mock_get_connection, db_config, sample_document_create
    ) -> None:
        """Test document creation with invalid project_id (foreign key)."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = PsycopgError("Foreign key constraint")

        repo = DocumentRepository(db_config)
        with pytest.raises(PsycopgError, match="Failed to create document"):
            repo.create(sample_document_create)
        mock_conn.rollback.assert_called_once()


class TestDocumentRepositoryGetById:
    """Test DocumentRepository.get_by_id() method."""

    @patch("processfoundry_ai.repositories.document_repository.get_connection")
    def test_get_by_id_success(
        self, mock_get_connection, db_config, sample_document_read
    ) -> None:
        """Test successful document retrieval by ID."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": sample_document_read.id,
            "project_id": sample_document_read.project_id,
            "filename": sample_document_read.filename,
            "mime_type": sample_document_read.mime_type,
            "checksum": sample_document_read.checksum,
            "version": sample_document_read.version,
            "storage_path": sample_document_read.storage_path,
        }

        repo = DocumentRepository(db_config)
        result = repo.get_by_id("DOC-001")

        assert result is not None
        assert result.id == "DOC-001"
        mock_conn.close.assert_called_once()

    @patch("processfoundry_ai.repositories.document_repository.get_connection")
    def test_get_by_id_not_found(self, mock_get_connection, db_config) -> None:
        """Test document retrieval when not found."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        repo = DocumentRepository(db_config)
        result = repo.get_by_id("NONEXISTENT")

        assert result is None


class TestDocumentRepositoryListByProject:
    """Test DocumentRepository.list_by_project() method."""

    @patch("processfoundry_ai.repositories.document_repository.get_connection")
    def test_list_by_project_success(self, mock_get_connection, db_config) -> None:
        """Test successful listing of documents for a project."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {
                "id": "DOC-001",
                "project_id": "PRJ-001",
                "filename": "doc1.pdf",
                "mime_type": "application/pdf",
                "checksum": "abc123",
                "version": "1.0",
                "storage_path": "/storage/doc1.pdf",
            },
            {
                "id": "DOC-002",
                "project_id": "PRJ-001",
                "filename": "doc2.pdf",
                "mime_type": "application/pdf",
                "checksum": "def456",
                "version": "1.0",
                "storage_path": "/storage/doc2.pdf",
            },
        ]

        repo = DocumentRepository(db_config)
        results = repo.list_by_project("PRJ-001")

        assert len(results) == 2
        assert all(isinstance(r, DocumentRead) for r in results)
        assert all(r.project_id == "PRJ-001" for r in results)

    @patch("processfoundry_ai.repositories.document_repository.get_connection")
    def test_list_by_project_empty(self, mock_get_connection, db_config) -> None:
        """Test listing documents when none exist for project."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        repo = DocumentRepository(db_config)
        results = repo.list_by_project("EMPTY-PROJECT")

        assert results == []


# ============================================================================
# DocumentSectionRepository Tests
# ============================================================================


class TestDocumentSectionRepositoryCreate:
    """Test DocumentSectionRepository.create() method."""

    @patch(
        "processfoundry_ai.repositories.document_section_repository.get_connection"
    )
    def test_create_section_success(
        self, mock_get_connection, db_config, sample_section_create
    ) -> None:
        """Test successful document section creation."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": "SEC-001",
            "document_id": "DOC-001",
            "page_number": 1,
            "section_title": "Introduction",
            "text": "This is the introduction section of the document.",
        }

        repo = DocumentSectionRepository(db_config)
        result = repo.create(sample_section_create)

        assert result.id == "SEC-001"
        assert result.document_id == "DOC-001"
        assert result.page_number == 1
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch(
        "processfoundry_ai.repositories.document_section_repository.get_connection"
    )
    def test_create_section_foreign_key_error(
        self, mock_get_connection, db_config, sample_section_create
    ) -> None:
        """Test section creation with invalid document_id (foreign key)."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = PsycopgError("Foreign key constraint")

        repo = DocumentSectionRepository(db_config)
        with pytest.raises(PsycopgError, match="Failed to create document section"):
            repo.create(sample_section_create)
        mock_conn.rollback.assert_called_once()


class TestDocumentSectionRepositoryGetById:
    """Test DocumentSectionRepository.get_by_id() method."""

    @patch(
        "processfoundry_ai.repositories.document_section_repository.get_connection"
    )
    def test_get_by_id_success(
        self, mock_get_connection, db_config, sample_section_read
    ) -> None:
        """Test successful document section retrieval by ID."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": sample_section_read.id,
            "document_id": sample_section_read.document_id,
            "page_number": sample_section_read.page_number,
            "section_title": sample_section_read.section_title,
            "text": sample_section_read.text,
        }

        repo = DocumentSectionRepository(db_config)
        result = repo.get_by_id("SEC-001")

        assert result is not None
        assert result.id == "SEC-001"


class TestDocumentSectionRepositoryListByDocument:
    """Test DocumentSectionRepository.list_by_document() method."""

    @patch(
        "processfoundry_ai.repositories.document_section_repository.get_connection"
    )
    def test_list_by_document_success(self, mock_get_connection, db_config) -> None:
        """Test successful listing of sections for a document."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {
                "id": "SEC-001",
                "document_id": "DOC-001",
                "page_number": 1,
                "section_title": "Introduction",
                "text": "Intro text",
            },
            {
                "id": "SEC-002",
                "document_id": "DOC-001",
                "page_number": 2,
                "section_title": "Body",
                "text": "Body text",
            },
        ]

        repo = DocumentSectionRepository(db_config)
        results = repo.list_by_document("DOC-001")

        assert len(results) == 2
        assert all(isinstance(r, DocumentSectionRead) for r in results)
        assert all(r.document_id == "DOC-001" for r in results)


# ============================================================================
# EvidenceItemRepository Tests
# ============================================================================


class TestEvidenceItemRepositoryCreate:
    """Test EvidenceItemRepository.create() method."""

    @patch("processfoundry_ai.repositories.evidence_item_repository.get_connection")
    def test_create_evidence_success(
        self, mock_get_connection, db_config, sample_evidence_create
    ) -> None:
        """Test successful evidence item creation."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": "EVD-001",
            "project_id": "PRJ-001",
            "document_section_id": "SEC-001",
            "quote": "A key quote from the section",
            "claim_type": "process_step",
            "confidence": Decimal("0.95"),
        }

        repo = EvidenceItemRepository(db_config)
        result = repo.create(sample_evidence_create)

        assert result.id == "EVD-001"
        assert result.project_id == "PRJ-001"
        assert result.document_section_id == "SEC-001"
        assert result.confidence == Decimal("0.95")
        mock_conn.commit.assert_called_once()

    @patch("processfoundry_ai.repositories.evidence_item_repository.get_connection")
    def test_create_evidence_uses_parameterized_query(
        self, mock_get_connection, db_config, sample_evidence_create
    ) -> None:
        """Test that create uses parameterized SQL queries."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": sample_evidence_create.id,
            "project_id": sample_evidence_create.project_id,
            "document_section_id": sample_evidence_create.document_section_id,
            "quote": sample_evidence_create.quote,
            "claim_type": sample_evidence_create.claim_type,
            "confidence": sample_evidence_create.confidence,
        }

        repo = EvidenceItemRepository(db_config)
        repo.create(sample_evidence_create)

        args = mock_cursor.execute.call_args
        assert "%s" in args[0][0]
        assert isinstance(args[0][1], tuple)

    @patch("processfoundry_ai.repositories.evidence_item_repository.get_connection")
    def test_create_evidence_foreign_key_project_error(
        self, mock_get_connection, db_config, sample_evidence_create
    ) -> None:
        """Test evidence creation with invalid project_id (foreign key)."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = PsycopgError("Foreign key constraint")

        repo = EvidenceItemRepository(db_config)
        with pytest.raises(PsycopgError, match="Failed to create evidence item"):
            repo.create(sample_evidence_create)
        mock_conn.rollback.assert_called_once()

    @patch("processfoundry_ai.repositories.evidence_item_repository.get_connection")
    def test_create_evidence_foreign_key_section_error(
        self, mock_get_connection, db_config, sample_evidence_create
    ) -> None:
        """Test evidence creation with invalid document_section_id (foreign key)."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = PsycopgError("Foreign key constraint")

        repo = EvidenceItemRepository(db_config)
        with pytest.raises(PsycopgError, match="Failed to create evidence item"):
            repo.create(sample_evidence_create)


class TestEvidenceItemRepositoryGetById:
    """Test EvidenceItemRepository.get_by_id() method."""

    @patch("processfoundry_ai.repositories.evidence_item_repository.get_connection")
    def test_get_by_id_success(
        self, mock_get_connection, db_config, sample_evidence_read
    ) -> None:
        """Test successful evidence item retrieval by ID."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": sample_evidence_read.id,
            "project_id": sample_evidence_read.project_id,
            "document_section_id": sample_evidence_read.document_section_id,
            "quote": sample_evidence_read.quote,
            "claim_type": sample_evidence_read.claim_type,
            "confidence": sample_evidence_read.confidence,
        }

        repo = EvidenceItemRepository(db_config)
        result = repo.get_by_id("EVD-001")

        assert result is not None
        assert result.id == "EVD-001"


class TestEvidenceItemRepositoryListByProject:
    """Test EvidenceItemRepository.list_by_project() method."""

    @patch("processfoundry_ai.repositories.evidence_item_repository.get_connection")
    def test_list_by_project_success(self, mock_get_connection, db_config) -> None:
        """Test successful listing of evidence items for a project."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {
                "id": "EVD-001",
                "project_id": "PRJ-001",
                "document_section_id": "SEC-001",
                "quote": "Quote 1",
                "claim_type": "process_step",
                "confidence": Decimal("0.95"),
            },
            {
                "id": "EVD-002",
                "project_id": "PRJ-001",
                "document_section_id": "SEC-002",
                "quote": "Quote 2",
                "claim_type": "decision",
                "confidence": Decimal("0.85"),
            },
        ]

        repo = EvidenceItemRepository(db_config)
        results = repo.list_by_project("PRJ-001")

        assert len(results) == 2
        assert all(isinstance(r, EvidenceItemRead) for r in results)
        assert all(r.project_id == "PRJ-001" for r in results)


class TestEvidenceItemRepositoryListByDocumentSection:
    """Test EvidenceItemRepository.list_by_document_section() method (traceability)."""

    @patch("processfoundry_ai.repositories.evidence_item_repository.get_connection")
    def test_list_by_document_section_success(
        self, mock_get_connection, db_config
    ) -> None:
        """Test successful listing of evidence items by document section (traceability)."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {
                "id": "EVD-001",
                "project_id": "PRJ-001",
                "document_section_id": "SEC-001",
                "quote": "Quote from section",
                "claim_type": "process_step",
                "confidence": Decimal("0.95"),
            },
            {
                "id": "EVD-003",
                "project_id": "PRJ-001",
                "document_section_id": "SEC-001",
                "quote": "Another quote",
                "claim_type": "decision",
                "confidence": Decimal("0.87"),
            },
        ]

        repo = EvidenceItemRepository(db_config)
        results = repo.list_by_document_section("SEC-001")

        assert len(results) == 2
        assert all(isinstance(r, EvidenceItemRead) for r in results)
        assert all(r.document_section_id == "SEC-001" for r in results)
        # Verify ordered by confidence DESC
        assert results[0].confidence >= results[1].confidence

    @patch("processfoundry_ai.repositories.evidence_item_repository.get_connection")
    def test_list_by_document_section_empty(self, mock_get_connection, db_config) -> None:
        """Test listing evidence for a section with no evidence."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        repo = EvidenceItemRepository(db_config)
        results = repo.list_by_document_section("EMPTY-SECTION")

        assert results == []


class TestConnectionHandling:
    """Test connection and resource handling across all repositories."""

    @patch("processfoundry_ai.repositories.document_repository.get_connection")
    def test_document_connection_closed_on_error(
        self, mock_get_connection, db_config, sample_document_create
    ) -> None:
        """Test that connections are closed even when errors occur."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = PsycopgError("Query failed")

        repo = DocumentRepository(db_config)
        try:
            repo.create(sample_document_create)
        except PsycopgError:
            pass

        mock_conn.close.assert_called_once()
        mock_conn.rollback.assert_called_once()

    @patch(
        "processfoundry_ai.repositories.document_section_repository.get_connection"
    )
    def test_section_connection_closed_on_error(
        self, mock_get_connection, db_config, sample_section_create
    ) -> None:
        """Test that connections are closed for sections."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = PsycopgError("Query failed")

        repo = DocumentSectionRepository(db_config)
        try:
            repo.create(sample_section_create)
        except PsycopgError:
            pass

        mock_conn.close.assert_called_once()

    @patch("processfoundry_ai.repositories.evidence_item_repository.get_connection")
    def test_evidence_connection_closed_on_error(
        self, mock_get_connection, db_config, sample_evidence_create
    ) -> None:
        """Test that connections are closed for evidence items."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = PsycopgError("Query failed")

        repo = EvidenceItemRepository(db_config)
        try:
            repo.create(sample_evidence_create)
        except PsycopgError:
            pass

        mock_conn.close.assert_called_once()
