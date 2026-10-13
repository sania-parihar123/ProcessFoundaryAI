"""Pydantic models for the test_cases table."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TestCaseBase(BaseModel):
    """Base test case model with common fields."""

    id: str = Field(..., description="Unique test case identifier")
    project_id: str = Field(..., description="Project ID (foreign key)")
    test_key: str = Field(..., description="Stable test identifier")
    requirement_id: str = Field(..., description="Linked requirement ID (foreign key)")
    scenario: str = Field(..., description="Scenario description")
    expected_result: str = Field(..., description="Expected outcome")


class TestCaseCreate(TestCaseBase):
    """Model for creating a new test case."""

    model_config = {"from_attributes": True}


class TestCaseRead(TestCaseBase):
    """Model for reading a test case from the database."""

    model_config = {"from_attributes": True}
