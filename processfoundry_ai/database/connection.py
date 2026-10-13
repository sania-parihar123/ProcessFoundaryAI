"""Database connection utilities using psycopg."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg import Error as PsycopgError
from sqlalchemy import text
from sqlalchemy.engine import Engine

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.session import get_engine


def get_connection(config: DatabaseConfig) -> psycopg.Connection[dict[str, Any]]:
    """Open a new database connection.

    Args:
        config: Database configuration with DSN.

    Returns:
        An open psycopg Connection.

    Raises:
        PsycopgError: If connection fails.
    """
    try:
        conn = psycopg.connect(config.dsn, row_factory=psycopg.rows.dict_row)
        return conn
    except PsycopgError as e:
        raise PsycopgError(f"Failed to connect to database: {e}") from e


def health_check(config: DatabaseConfig) -> bool:
    """Verify database connectivity without modifying data.

    Args:
        config: Database configuration with DSN.

    Returns:
        True if database is reachable, False otherwise.
    """
    try:
        conn = get_connection(config)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


def inspect_database_state(config: DatabaseConfig) -> dict[str, Any]:
    """Return a read-only summary of database reachability and schema state.

    This helper intentionally does not mutate schema or migration history. It can be
    used before a migration is considered safe for an existing PostgreSQL database.
    """
    result: dict[str, Any] = {
        "reachable": False,
        "database": None,
        "tables": [],
        "alembic_revision": None,
        "schema_state": "unknown",
        "errors": [],
    }

    try:
        engine: Engine = get_engine(config)
        with engine.connect() as conn:
            result["reachable"] = True
            result["database"] = conn.dialect.name
            table_rows = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = current_schema() "
                    "ORDER BY table_name"
                )
            ).fetchall()
            result["tables"] = [row[0] for row in table_rows]
            revision_rows = conn.execute(
                text(
                    "SELECT version_num FROM alembic_version LIMIT 1"
                )
            ).fetchall()
            result["alembic_revision"] = revision_rows[0][0] if revision_rows else None
    except Exception as exc:  # pragma: no cover - defensive helper
        result["errors"].append(str(exc))
        return result

    present = set(result["tables"])
    expected = {
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

    if expected.issubset(present):
        result["schema_state"] = "fully-migrated"
    elif {"projects", "documents", "document_sections", "evidence_items"}.issubset(present):
        result["schema_state"] = "legacy-four-table"
    elif present:
        result["schema_state"] = "custom-or-partial-schema"
    else:
        result["schema_state"] = "empty-database"

    return result
