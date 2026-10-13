
"""Safely add missing ProcessFoundry schema tables.

Revision ID: 002_additive_schema
Revises: 001_initial_core_tables

This migration creates missing tables from the SQLAlchemy models.
Existing tables and their data are not dropped or recreated.
"""

from typing import Sequence, Union

from alembic import op

from processfoundry_ai.database.base import Base
from processfoundry_ai.database import models  # noqa: F401


revision: str = "002_additive_schema"
down_revision: Union[str, None] = "001_initial_core_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# These are the 12 tables added after the original four-table schema.
ADDITIONAL_TABLES = [
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
]


def upgrade() -> None:
    """Create only additional tables that do not already exist."""
    connection = op.get_bind()

    tables_to_create = [
        Base.metadata.tables[table_name]
        for table_name in ADDITIONAL_TABLES
        if table_name not in set(
            __import__("sqlalchemy").inspect(connection).get_table_names()
        )
    ]

    if tables_to_create:
        Base.metadata.create_all(
            bind=connection,
            tables=tables_to_create,
            checkfirst=True,
        )


def downgrade() -> None:
    """Prevent accidental deletion of existing project data."""
    raise RuntimeError(
        "Automatic downgrade is disabled for this additive migration. "
        "Review the database and back up data before any manual rollback."
    )
