"""Tests for database engine and session management."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.session import (
    dispose_engine,
    get_engine,
    get_session,
    get_session_factory,
    session_context,
)


@pytest.fixture(autouse=True)
def clean_engine():
    """Ensure engine and session factory are disposed before and after each test."""
    dispose_engine()
    yield
    dispose_engine()


class TestDatabaseSessionManagement:
    """Test engine and session lifecycle functions."""

    def test_get_engine_creates_and_caches_engine(self) -> None:
        """Verify get_engine creates an engine and returns the cached instance on subsequent calls."""
        config = DatabaseConfig(dsn="sqlite:///:memory:")
        engine1 = get_engine(config)
        assert isinstance(engine1, Engine)

        engine2 = get_engine(config)
        assert engine1 is engine2

    def test_get_engine_recreates_on_dsn_change(self) -> None:
        """Verify get_engine disposes the old engine and creates a new one when DSN changes."""
        config1 = DatabaseConfig(dsn="sqlite:///:memory:")
        engine1 = get_engine(config1)

        config2 = DatabaseConfig(dsn="sqlite:///test2.db")
        engine2 = get_engine(config2)
        assert engine1 is not engine2

    def test_get_session_factory(self) -> None:
        """Verify get_session_factory creates a sessionmaker bound to the engine."""
        config = DatabaseConfig(dsn="sqlite:///:memory:")
        factory1 = get_session_factory(config)
        assert isinstance(factory1, sessionmaker)

        factory2 = get_session_factory(config)
        assert factory1 is factory2

    def test_get_session(self) -> None:
        """Verify get_session returns a new Session instance."""
        config = DatabaseConfig(dsn="sqlite:///:memory:")
        session = get_session(config)
        assert isinstance(session, Session)
        session.close()

    @patch("processfoundry_ai.database.session.get_session")
    def test_session_context_success(self, mock_get_session) -> None:
        """Verify session_context provides a session and closes it on exit."""
        config = DatabaseConfig(dsn="sqlite:///:memory:")
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        with session_context(config) as session:
            assert session is mock_session

        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

    @patch("processfoundry_ai.database.session.get_session")
    def test_session_context_rollback_on_error(self, mock_get_session) -> None:
        """Verify session_context rolls back and closes on exception."""
        config = DatabaseConfig(dsn="sqlite:///:memory:")
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        with pytest.raises(RuntimeError, match="Simulated error"):
            with session_context(config):
                raise RuntimeError("Simulated error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_dispose_engine(self) -> None:
        """Verify dispose_engine cleans up engine and sessionmaker."""
        config = DatabaseConfig(dsn="sqlite:///:memory:")
        get_engine(config)
        get_session_factory(config)

        dispose_engine()

        # Next call creates a fresh engine
        new_engine = get_engine(config)
        assert new_engine is not None
