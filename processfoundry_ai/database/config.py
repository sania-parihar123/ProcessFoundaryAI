"""Database configuration and environment loading for ProcessFoundry AI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _load_project_env() -> None:
    """Load the local .env file from the repository root if available."""
    project_root = Path(__file__).resolve().parents[2]
    candidates = [project_root / ".env", Path.cwd() / ".env"]
    for candidate in candidates:
        if candidate.exists():
            load_dotenv(candidate, override=False)
            return


_load_project_env()


@dataclass(frozen=True)
class DatabaseConfig:
    """PostgreSQL database configuration from environment variables."""

    dsn: str

    @property
    def sqlalchemy_dsn(self) -> str:
        """Return a SQLAlchemy URL that uses the psycopg v3 driver when needed.

        Raw ``postgresql://`` URLs are valid for ``psycopg.connect`` but SQLAlchemy 2
        would otherwise look for psycopg2. SQLite and already-qualified URLs are
        left unchanged.
        """
        dsn = self.dsn
        if dsn.startswith(("postgresql+psycopg://", "postgresql+psycopg2://")):
            return dsn
        if dsn.startswith("postgresql://"):
            return "postgresql+psycopg://" + dsn[len("postgresql://") :]
        if dsn.startswith("postgres://"):
            return "postgresql+psycopg://" + dsn[len("postgres://") :]
        return dsn

    @staticmethod
    def from_env(env_var: str = "DATABASE_URL") -> "DatabaseConfig":
        """Load database config from environment variable.

        Args:
            env_var: Environment variable name (default: DATABASE_URL).

        Returns:
            DatabaseConfig with DSN from environment.

        Raises:
            ValueError: If env_var is not set or empty.
        """
        _load_project_env()
        dsn = os.getenv(env_var, "").strip()
        if not dsn:
            raise ValueError(
                f"Environment variable '{env_var}' is required "
                "and must contain a valid PostgreSQL connection string"
            )
        return DatabaseConfig(dsn=dsn)
