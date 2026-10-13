"""Repository for test case CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.models import TestCase as TestCaseORM
from processfoundry_ai.database.session import session_context
from processfoundry_ai.models.test_case import TestCaseCreate, TestCaseRead


class TestCaseRepository:
    """Repository for test_cases table operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize repository with database config.

        Args:
            config: Database configuration.
        """
        self.config = config

    def create(self, test_case: TestCaseCreate) -> TestCaseRead:
        """Create a new test case.

        Args:
            test_case: Test case data to create (TestCaseCreate model).

        Returns:
            Created test case as TestCaseRead model.

        Raises:
            SQLAlchemyError: If database operation fails or foreign key constraint is violated.
        """
        with session_context(self.config) as session:
            orm_test_case = TestCaseORM(
                id=test_case.id,
                project_id=test_case.project_id,
                test_key=test_case.test_key,
                requirement_id=test_case.requirement_id,
                scenario=test_case.scenario,
                expected_result=test_case.expected_result,
            )
            session.add(orm_test_case)
            session.commit()
            session.refresh(orm_test_case)
            return TestCaseRead.model_validate(orm_test_case)

    def get_by_id(self, test_case_id: str) -> TestCaseRead | None:
        """Get test case by ID.

        Args:
            test_case_id: Test case ID to retrieve.

        Returns:
            TestCaseRead if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(TestCaseORM).where(TestCaseORM.id == test_case_id)
            orm_test_case = session.scalars(stmt).first()

            if orm_test_case is None:
                return None

            return TestCaseRead.model_validate(orm_test_case)

    def list_by_project(self, project_id: str) -> list[TestCaseRead]:
        """List all test cases for a project.

        Args:
            project_id: Project ID to filter by.

        Returns:
            List of test cases for the project as TestCaseRead models.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            stmt = select(TestCaseORM).where(TestCaseORM.project_id == project_id)
            orm_test_cases = session.scalars(stmt).all()
            return [TestCaseRead.model_validate(tc) for tc in orm_test_cases]

    def update(self, test_case_id: str, updates: dict) -> TestCaseRead | None:
        """Update a test case by ID.

        Args:
            test_case_id: Test case ID to update.
            updates: Dictionary of fields to update with their new values.

        Returns:
            Updated test case as TestCaseRead model if found and updated, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_test_case = session.get(TestCaseORM, test_case_id)
            if orm_test_case is None:
                return None

            for field, value in updates.items():
                if value is not None and hasattr(orm_test_case, field):
                    setattr(orm_test_case, field, value)

            session.commit()
            session.refresh(orm_test_case)
            return TestCaseRead.model_validate(orm_test_case)

    def delete(self, test_case_id: str) -> bool:
        """Delete a test case by ID.

        Args:
            test_case_id: Test case ID to delete.

        Returns:
            True if the test case was deleted, False if not found.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        with session_context(self.config) as session:
            orm_test_case = session.get(TestCaseORM, test_case_id)
            if orm_test_case is None:
                return False
            session.delete(orm_test_case)
            session.commit()
            return True
