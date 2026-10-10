"""Database connection utilities using psycopg."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg import Error as PsycopgError

from processfoundry_ai.database.config import DatabaseConfig


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
