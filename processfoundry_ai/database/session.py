"""SQLAlchemy engine and session management for ProcessFoundry AI.

This module provides:
- Engine configuration for PostgreSQL (and SQLite for testing)
- Session factory for creating database sessions
- Context managers for safe session lifecycle and transaction management

The module is safe to import even without DATABASE_URL configured
(engine and session factory are only created when explicitly called).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from processfoundry_ai.database.config import DatabaseConfig

# Global engine and session factory (created lazily)
_engine: Optional[Engine] = None
_engine_dsn: Optional[str] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine(config: DatabaseConfig) -> Engine:
    """Get or create SQLAlchemy engine.

    Creates an engine using the connection string from config.
    The engine is created once and cached for reuse unless the DSN changes.

    Args:
        config: Database configuration with DSN.

    Returns:
        SQLAlchemy Engine instance.

    Note:
        The engine does not connect to the database until the first query is executed.
    """
    global _engine, _engine_dsn, _SessionLocal
    engine_url = config.sqlalchemy_dsn
    if _engine is not None and _engine_dsn != engine_url:
        dispose_engine()

    if _engine is None:
        _engine_dsn = engine_url
        if engine_url.startswith("sqlite"):
            engine = create_engine(
                engine_url,
                echo=False,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
            )

            @event.listens_for(engine, "connect")
            def _configure_sqlite_connection(dbapi_connection, connection_record):
                # Enable foreign key constraint enforcement in SQLite
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
                # Register btrim function so PostgreSQL check constraints work in SQLite
                dbapi_connection.create_function(
                    "btrim", 1, lambda s: s.strip() if s is not None else None
                )

            _engine = engine
        else:
            _engine = create_engine(
                engine_url,
                echo=False,
                pool_pre_ping=True,
            )
    return _engine


def get_session_factory(config: DatabaseConfig) -> sessionmaker:
    """Get or create SQLAlchemy session factory.

    Creates a sessionmaker bound to the configured engine.
    The factory is created once and cached for reuse.

    Args:
        config: Database configuration with DSN.

    Returns:
        SQLAlchemy sessionmaker instance.
    """
    global _SessionLocal
    engine = get_engine(config)
    if _SessionLocal is None or _SessionLocal.kw.get("bind") != engine:
        _SessionLocal = sessionmaker(
            bind=engine,
            class_=Session,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_session(config: DatabaseConfig) -> Session:
    """Create a new database session.

    Args:
        config: Database configuration with DSN.

    Returns:
        A new SQLAlchemy Session instance.

    Note:
        Prefer using session_context() for automatic cleanup.
    """
    factory = get_session_factory(config)
    return factory()


@contextmanager
def session_context(config: DatabaseConfig) -> Generator[Session, None, None]:
    """Context manager for safe session lifecycle management.

    Automatically rolls back uncommitted changes on exception and
    closes the session on exit.

    Args:
        config: Database configuration with DSN.

    Yields:
        A SQLAlchemy Session instance.

    Example:
        >>> with session_context(config) as session:
        ...     project = session.query(Project).filter_by(id="PRJ-001").first()
    """
    session = get_session(config)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def dispose_engine() -> None:
    """Dispose of the global engine and reset session factory.

    This is useful for testing or when switching database configurations.
    The next call to get_engine() will create a new engine.
    """
    global _engine, _engine_dsn, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
    _engine_dsn = None
    _SessionLocal = None
