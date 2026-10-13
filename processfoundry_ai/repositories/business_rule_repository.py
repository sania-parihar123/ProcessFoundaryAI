"""Repository for business rule CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import BusinessRule as BusinessRuleORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.business_rule import BusinessRuleCreate, BusinessRuleRead


class BusinessRuleRepository:
    """Repository for business_rules table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, business_rule: BusinessRuleCreate) -> BusinessRuleRead:
        """Create a new business rule.

        Args:
            business_rule: Business rule data to create (BusinessRuleCreate model).

        Returns:
            Created business rule as BusinessRuleRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_business_rule = BusinessRuleORM(
                id=business_rule.id,
                project_id=business_rule.project_id,
                rule_key=business_rule.rule_key,
                description=business_rule.description,
                condition_json=business_rule.condition_json,
                status=business_rule.status,
            )
            session.add(orm_business_rule)
            session.commit()
            session.refresh(orm_business_rule)
            return BusinessRuleRead.model_validate(orm_business_rule)

    def get_by_id(self, business_rule_id: str) -> BusinessRuleRead | None:
        """Get business rule by ID.

        Args:
            business_rule_id: Business rule ID to retrieve.

        Returns:
            BusinessRuleRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(BusinessRuleORM).where(BusinessRuleORM.id == business_rule_id)
            orm_business_rule = session.scalars(stmt).first()

            if orm_business_rule is None:
                return None

            return BusinessRuleRead.model_validate(orm_business_rule)

    def list_by_project(self, project_id: str) -> list[BusinessRuleRead]:
        """List all business rules for a project.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of business rules for the project as BusinessRuleRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(BusinessRuleORM).where(BusinessRuleORM.project_id == project_id)
            orm_business_rules = session.scalars(stmt).all()
            return [BusinessRuleRead.model_validate(br) for br in orm_business_rules]

    def update(self, business_rule_id: str, updates: dict) -> BusinessRuleRead | None:
        """Update a business rule by ID.

        Args:
            business_rule_id: Business rule ID to update.
            updates: Dictionary of fields to update with their new values.

        Returns:
            Updated business rule as BusinessRuleRead model, or None if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_business_rule = session.get(BusinessRuleORM, business_rule_id)
            if orm_business_rule is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_business_rule, field):
                    setattr(orm_business_rule, field, value)

            session.commit()
            session.refresh(orm_business_rule)
            return BusinessRuleRead.model_validate(orm_business_rule)

    def delete(self, business_rule_id: str) -> bool:
        """Delete a business rule by ID.

        Args:
            business_rule_id: Business rule ID to delete.

        Returns:
            True if the business rule was deleted, False if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_business_rule = session.get(BusinessRuleORM, business_rule_id)
            if orm_business_rule is None:
                return False
            session.delete(orm_business_rule)
            session.commit()
            return True
