"""Repository for agent run CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import AgentRun as AgentRunORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.agent_run import AgentRunCreate, AgentRunRead


class AgentRunRepository:
    """Repository for agent_runs table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, agent_run: AgentRunCreate) -> AgentRunRead:
        """Create a new agent run record.

        Args:
            agent_run: Agent run data to create (AgentRunCreate model).

        Returns:
            Created agent run as AgentRunRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_agent_run = AgentRunORM(
                id=agent_run.id,
                project_id=agent_run.project_id,
                node_name=agent_run.node_name,
                status=agent_run.status,
                input_summary=agent_run.input_summary,
                output_ref=agent_run.output_ref,
                error=agent_run.error,
                created_at=agent_run.created_at,
                updated_at=agent_run.updated_at,
            )
            session.add(orm_agent_run)
            session.commit()
            session.refresh(orm_agent_run)
            return AgentRunRead.model_validate(orm_agent_run)

    def get_by_id(self, agent_run_id: str) -> AgentRunRead | None:
        """Get agent run record by ID.

        Args:
            agent_run_id: Agent run record ID to retrieve.

        Returns:
            AgentRunRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(AgentRunORM).where(AgentRunORM.id == agent_run_id)
            orm_agent_run = session.scalars(stmt).first()

            if orm_agent_run is None:
                return None

            return AgentRunRead.model_validate(orm_agent_run)

    def list_by_project(self, project_id: str) -> list[AgentRunRead]:
        """List all agent runs for a project ordered by creation date descending.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of agent runs for the project as AgentRunRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = (
                select(AgentRunORM)
                .where(AgentRunORM.project_id == project_id)
                .order_by(AgentRunORM.created_at.desc())
            )
            orm_agent_runs = session.scalars(stmt).all()
            return [AgentRunRead.model_validate(ar) for ar in orm_agent_runs]

    def update(self, agent_run_id: str, updates: dict) -> AgentRunRead | None:
        """Update an agent run record by ID."""
        with session_context(self.config) as session:
            orm_agent_run = session.get(AgentRunORM, agent_run_id)
            if orm_agent_run is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_agent_run, field):
                    setattr(orm_agent_run, field, value)

            session.commit()
            session.refresh(orm_agent_run)
            return AgentRunRead.model_validate(orm_agent_run)

    def delete(self, agent_run_id: str) -> bool:
        """Delete an agent run record by ID."""
        with session_context(self.config) as session:
            orm_agent_run = session.get(AgentRunORM, agent_run_id)
            if orm_agent_run is None:
                return False
            session.delete(orm_agent_run)
            session.commit()
            return True
