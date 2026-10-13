"""Repository for process step CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import ProcessStep as ProcessStepORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.process_step import ProcessStepCreate, ProcessStepRead


class ProcessStepRepository:
    """Repository for process_steps table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, process_step: ProcessStepCreate) -> ProcessStepRead:
        """Create a new process step.

        Args:
            process_step: Process step data to create (ProcessStepCreate model).

        Returns:
            Created process step as ProcessStepRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_process_step = ProcessStepORM(
                id=process_step.id,
                process_version_id=process_step.process_version_id,
                step_key=process_step.step_key,
                name=process_step.name,
                actor=process_step.actor,
                step_type=process_step.step_type,
                sequence=process_step.sequence,
            )
            session.add(orm_process_step)
            session.commit()
            session.refresh(orm_process_step)
            return ProcessStepRead.model_validate(orm_process_step)

    def get_by_id(self, process_step_id: str) -> ProcessStepRead | None:
        """Get process step by ID.

        Args:
            process_step_id: Process step ID to retrieve.

        Returns:
            ProcessStepRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(ProcessStepORM).where(ProcessStepORM.id == process_step_id)
            orm_process_step = session.scalars(stmt).first()

            if orm_process_step is None:
                return None

            return ProcessStepRead.model_validate(orm_process_step)

    def list_by_process_version(self, process_version_id: str) -> list[ProcessStepRead]:
        """List all process steps for a process version ordered by sequence.

        Args:
            process_version_id: Process version ID to filter by.

        Returns:
            List of process steps for the process version as ProcessStepRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = (
                select(ProcessStepORM)
                .where(ProcessStepORM.process_version_id == process_version_id)
                .order_by(ProcessStepORM.sequence)
            )
            orm_process_steps = session.scalars(stmt).all()
            return [ProcessStepRead.model_validate(ps) for ps in orm_process_steps]

    def update(self, process_step_id: str, updates: dict) -> ProcessStepRead | None:
        """Update a process step by ID."""
        with session_context(self.config) as session:
            orm_process_step = session.get(ProcessStepORM, process_step_id)
            if orm_process_step is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_process_step, field):
                    setattr(orm_process_step, field, value)

            session.commit()
            session.refresh(orm_process_step)
            return ProcessStepRead.model_validate(orm_process_step)

    def delete(self, process_step_id: str) -> bool:
        """Delete a process step by ID."""
        with session_context(self.config) as session:
            orm_process_step = session.get(ProcessStepORM, process_step_id)
            if orm_process_step is None:
                return False
            session.delete(orm_process_step)
            session.commit()
            return True
