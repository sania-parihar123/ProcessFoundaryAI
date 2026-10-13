"""Create the complete ProcessFoundry schema.

Revision ID: 001_initial_core_tables
Revises: None
Create Date: 2026-10-12

This revision is the initial full 16-table schema for a fresh database.
Do not edit it after it has been applied. If an existing database already
contains the earlier four-table schema, stamp or upgrade only after
inspecting `alembic current` and adding a later additive revision.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001_initial_core_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the complete canonical database schema for ProcessFoundry AI."""
    op.create_table(
        "projects",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("process_type", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("btrim(name) <> ''", name="projects_name_check"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("checksum", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_documents_project"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "document_sections",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("document_id", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.Text(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], name="fk_document_sections_document"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evidence_items",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("document_section_id", sa.Text(), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_evidence_items_project"
        ),
        sa.ForeignKeyConstraint(
            ["document_section_id"],
            ["document_sections.id"],
            name="fk_evidence_items_document_section",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "process_versions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("as_is_json", sa.JSON(), nullable=True),
        sa.Column("to_be_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_process_versions_project"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "process_steps",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("process_version_id", sa.Text(), nullable=False),
        sa.Column("step_key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("step_type", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["process_version_id"],
            ["process_versions.id"],
            name="fk_process_steps_process_version",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "business_rules",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("rule_key", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("condition_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_business_rules_project"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rule_evidence",
        sa.Column("rule_id", sa.Text(), nullable=False),
        sa.Column("evidence_id", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["rule_id"], ["business_rules.id"], name="fk_rule_evidence_business_rule"
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"], ["evidence_items.id"], name="fk_rule_evidence_evidence_item"
        ),
        sa.PrimaryKeyConstraint("rule_id", "evidence_id", name="pk_rule_evidence"),
    )

    op.create_table(
        "clarification_items",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("answered_by", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_clarification_items_project"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "requirements",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("requirement_key", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_requirements_project"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "requirement_links",
        sa.Column("source_requirement_id", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=False),
        sa.Column("link_type", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_requirement_id"],
            ["requirements.id"],
            name="fk_requirement_links_source_requirement",
        ),
        sa.PrimaryKeyConstraint(
            "source_requirement_id",
            "target_id",
            "link_type",
            name="pk_requirement_links",
        ),
    )

    op.create_table(
        "artifacts",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("artifact_type", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=True),
        sa.Column("markdown", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_artifacts_project"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "artifact_links",
        sa.Column("artifact_id", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=False),
        sa.Column("link_type", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"], ["artifacts.id"], name="fk_artifact_links_source_artifact"
        ),
        sa.PrimaryKeyConstraint(
            "artifact_id",
            "target_type",
            "target_id",
            "link_type",
            name="pk_artifact_links",
        ),
    )

    op.create_table(
        "test_cases",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("test_key", sa.Text(), nullable=False),
        sa.Column("requirement_id", sa.Text(), nullable=False),
        sa.Column("scenario", sa.Text(), nullable=False),
        sa.Column("expected_result", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_test_cases_project"
        ),
        sa.ForeignKeyConstraint(
            ["requirement_id"], ["requirements.id"], name="fk_test_cases_requirement"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "approvals",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("reviewer", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_approvals_project"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("node_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_ref", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_agent_runs_project"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_documents_project_id", "documents", ["project_id"])
    op.create_index("idx_document_sections_document_id", "document_sections", ["document_id"])
    op.create_index(
        "idx_evidence_items_project_id",
        "evidence_items",
        ["project_id", "document_section_id"],
    )
    op.create_index("idx_process_versions_project_id", "process_versions", ["project_id"])
    op.create_index("idx_process_steps_process_version_id", "process_steps", ["process_version_id", "sequence"])
    op.create_index("idx_business_rules_project_id", "business_rules", ["project_id"])
    op.create_index("idx_rule_evidence_rule_id", "rule_evidence", ["rule_id"])
    op.create_index("idx_rule_evidence_evidence_id", "rule_evidence", ["evidence_id"])
    op.create_index("idx_clarification_items_project_id", "clarification_items", ["project_id", "status"])
    op.create_index("idx_requirements_project_id", "requirements", ["project_id"])
    op.create_index("idx_requirement_links_source_requirement_id", "requirement_links", ["source_requirement_id"])
    op.create_index("idx_artifacts_project_id", "artifacts", ["project_id", "artifact_type"])
    op.create_index("idx_artifact_links_artifact_id", "artifact_links", ["artifact_id"])
    op.create_index("idx_test_cases_project_id", "test_cases", ["project_id", "requirement_id"])
    op.create_index("idx_approvals_project_id", "approvals", ["project_id", "target_type", "target_id"])
    op.create_index("idx_agent_runs_project_id", "agent_runs", ["project_id", "created_at"])


def downgrade() -> None:
    """Drop the complete ProcessFoundry schema in dependency order."""
    op.drop_table("agent_runs")
    op.drop_table("approvals")
    op.drop_table("test_cases")
    op.drop_table("artifact_links")
    op.drop_table("artifacts")
    op.drop_table("requirement_links")
    op.drop_table("requirements")
    op.drop_table("clarification_items")
    op.drop_table("rule_evidence")
    op.drop_table("business_rules")
    op.drop_table("process_steps")
    op.drop_table("process_versions")
    op.drop_table("evidence_items")
    op.drop_table("document_sections")
    op.drop_table("documents")
    op.drop_table("projects")
