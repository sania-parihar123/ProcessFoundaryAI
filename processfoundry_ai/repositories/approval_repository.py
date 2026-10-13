"""Repository for approval CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import Approval as ApprovalORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.approval import ApprovalCreate, ApprovalRead


class ApprovalRepository:
    """Repository for approvals table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, approval: ApprovalCreate) -> ApprovalRead:
        """Create a new approval record.

        Args:
            approval: Approval data to create (ApprovalCreate model).

        Returns:
            Created approval as ApprovalRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_approval = ApprovalORM(
                id=approval.id,
                project_id=approval.project_id,
                target_type=approval.target_type,
                target_id=approval.target_id,
                decision=approval.decision,
                reviewer=approval.reviewer,
                timestamp=approval.timestamp,
                comment=approval.comment,
            )
            session.add(orm_approval)
            session.commit()
            session.refresh(orm_approval)
            return ApprovalRead.model_validate(orm_approval)

    def get_by_id(self, approval_id: str) -> ApprovalRead | None:
        """Get approval record by ID.

        Args:
            approval_id: Approval record ID to retrieve.

        Returns:
            ApprovalRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ApprovalORM).where(ApprovalORM.id == approval_id)
            orm_approval = session.scalars(stmt).first()

            if orm_approval is None:
                return None

            return ApprovalRead.model_validate(orm_approval)

    def list_by_project(self, project_id: str) -> list[ApprovalRead]:
        """List all approval records for a project ordered by timestamp descending.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of approval records for the project as ApprovalRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = (
                select(ApprovalORM)
                .where(ApprovalORM.project_id == project_id)
                .order_by(ApprovalORM.timestamp.desc())
            )
            orm_approvals = session.scalars(stmt).all()
            return [ApprovalRead.model_validate(a) for a in orm_approvals]

    def update(self, approval_id: str, updates: dict) -> ApprovalRead | None:
        """Update an approval record by ID.

        Args:
            approval_id: Approval record ID to update.
            updates: Dictionary of fields and values to update.

        Returns:
            Updated approval as ApprovalRead model, or None if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_approval = session.get(ApprovalORM, approval_id)
            if orm_approval is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_approval, field):
                    setattr(orm_approval, field, value)

            session.commit()
            session.refresh(orm_approval)
            return ApprovalRead.model_validate(orm_approval)

    def delete(self, approval_id: str) -> bool:
        """Delete an approval record by ID.

        Args:
            approval_id: Approval record ID to delete.

        Returns:
            True if deleted, False if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_approval = session.get(ApprovalORM, approval_id)
            if orm_approval is None:
                return False
            session.delete(orm_approval)
            session.commit()
            return True
