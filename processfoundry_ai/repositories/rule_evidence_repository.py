"""Repository for rule evidence CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import RuleEvidence as RuleEvidenceORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.rule_evidence import RuleEvidenceCreate, RuleEvidenceRead


class RuleEvidenceRepository:
    """Repository for rule_evidence table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, rule_evidence: RuleEvidenceCreate) -> RuleEvidenceRead:
        """Create a new rule evidence link.

        Args:
            rule_evidence: Rule evidence data to create (RuleEvidenceCreate model).

        Returns:
            Created rule evidence link as RuleEvidenceRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_rule_evidence = RuleEvidenceORM(
                rule_id=rule_evidence.rule_id,
                evidence_id=rule_evidence.evidence_id,
            )
            session.add(orm_rule_evidence)
            session.commit()
            session.refresh(orm_rule_evidence)
            return RuleEvidenceRead.model_validate(orm_rule_evidence)

    def get_by_rule_and_evidence(
        self, rule_id: str, evidence_id: str
    ) -> RuleEvidenceRead | None:
        """Get rule evidence link by composite key.

        Args:
            rule_id: Business rule ID.
            evidence_id: Evidence item ID.

        Returns:
            RuleEvidenceRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(RuleEvidenceORM).where(
                (RuleEvidenceORM.rule_id == rule_id)
                & (RuleEvidenceORM.evidence_id == evidence_id)
            )
            orm_rule_evidence = session.scalars(stmt).first()

            if orm_rule_evidence is None:
                return None

            return RuleEvidenceRead.model_validate(orm_rule_evidence)

    def list_by_rule_id(self, rule_id: str) -> list[RuleEvidenceRead]:
        """List all evidence links for a business rule.

        Args:
            rule_id: Business rule ID to filter by.

        Returns:
            List of rule evidence links for the business rule as RuleEvidenceRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(RuleEvidenceORM).where(RuleEvidenceORM.rule_id == rule_id)
            orm_rule_evidence_links = session.scalars(stmt).all()
            return [RuleEvidenceRead.model_validate(re) for re in orm_rule_evidence_links]

    def list_by_evidence_id(self, evidence_id: str) -> list[RuleEvidenceRead]:
        """List all rule links for an evidence item.

        Args:
            evidence_id: Evidence item ID to filter by.

        Returns:
            List of rule evidence links for the evidence item as RuleEvidenceRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(RuleEvidenceORM).where(RuleEvidenceORM.evidence_id == evidence_id)
            orm_rule_evidence_links = session.scalars(stmt).all()
            return [RuleEvidenceRead.model_validate(re) for re in orm_rule_evidence_links]

