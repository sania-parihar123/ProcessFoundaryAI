"""Database configuration and connection management."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    """PostgreSQL database configuration from environment variables."""

    dsn: str

    @staticmethod
    def from_env(env_var: str = "DATABASE_URL") -> DatabaseConfig:
        """Load database config from environment variable.

        Args:
            env_var: Environment variable name (default: DATABASE_URL).

        Returns:
            DatabaseConfig with DSN from environment.

        Raises:
            ValueError: If env_var is not set or empty.
        """
        dsn = os.getenv(env_var, "").strip()
        if not dsn:
            raise ValueError(
                f"Environment variable '{env_var}' is required "
                "and must contain a valid PostgreSQL connection string"
            )
        return DatabaseConfig(dsn=dsn)
