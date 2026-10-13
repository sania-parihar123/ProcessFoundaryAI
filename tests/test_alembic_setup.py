"""Tests for Alembic migration configuration and discovery."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from processfoundry_ai.database.base import Base


class TestAlembicConfiguration:
    """Test Alembic setup and metadata discovery."""

    def test_alembic_ini_exists(self) -> None:
        """Verify alembic.ini is present in repository root."""
        ini_path = Path("alembic.ini")
        assert ini_path.is_file(), "alembic.ini must exist"

    def test_alembic_script_directory_and_head(self) -> None:
        """Verify Alembic script directory is configured and discovers the initial migration."""
        config = Config("alembic.ini")
        script_dir = ScriptDirectory.from_config(config)
        heads = script_dir.get_heads()
        assert len(heads) == 1
        assert heads[0] == "002_additive_schema"

    def test_alembic_command_heads_succeeds(self) -> None:
        """Verify alembic command.heads executes cleanly."""
        import io
        buf = io.StringIO()
        config = Config("alembic.ini", stdout=buf)
        command.heads(config)
        assert "002_additive_schema" in buf.getvalue()

    def test_initial_migration_has_upgrade_and_downgrade(self) -> None:
        """Verify that the initial migration module defines upgrade and downgrade functions."""
        config = Config("alembic.ini")
        script_dir = ScriptDirectory.from_config(config)
        rev = script_dir.get_revision("001_initial_core_tables")
        assert rev is not None
        assert rev.module is not None
        assert callable(rev.module.upgrade)
        assert callable(rev.module.downgrade)
        assert rev.module.revision == "001_initial_core_tables"
        assert rev.module.down_revision is None

    def test_alembic_env_configuration_source(self) -> None:
        """Verify alembic/env.py uses Base.metadata and DatabaseConfig.from_env()."""
        env_py_path = Path("alembic/env.py")
        assert env_py_path.is_file(), "alembic/env.py must exist"

        content = env_py_path.read_text(encoding="utf-8")
        assert "target_metadata = Base.metadata" in content
        assert "DatabaseConfig.from_env()" in content
        assert "postgresql://localhost/processfoundry" not in content

    def test_base_metadata_contains_core_tables(self) -> None:
        """Verify that Base.metadata contains all 16 canonical tables."""
        expected_tables = {
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
        assert expected_tables == set(Base.metadata.tables.keys())

    def test_sql_schema_and_migration_share_name_check_and_indexes(self) -> None:
        """Verify the SQL schema and Alembic revision declare the same constraints."""
        sql = Path(
            "processfoundry_ai/database/001_create_processfoundry_core_tables.sql"
        ).read_text(encoding="utf-8")
        migration = Path(
            "alembic/versions/001_initial_core_tables.py"
        ).read_text(encoding="utf-8")

        assert "projects_name_check" in sql
        assert "btrim(name) <> ''" in sql
        assert "projects_name_check" in migration
        assert "btrim(name) <> ''" in migration
        assert "idx_evidence_items_project_id" in sql
        assert '["project_id", "document_section_id"]' in migration
        assert "idx_evidence_items_document_section_id" not in sql
        assert "idx_evidence_items_document_section_id" not in migration
