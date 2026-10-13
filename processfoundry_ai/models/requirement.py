"""Pydantic models for the requirements table."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RequirementBase(BaseModel):
    """Base requirement model with canonical fields."""

    id: str = Field(..., description="Unique requirement identifier")
    project_id: str = Field(..., description="Project ID (foreign key)")
    requirement_key: str = Field(..., description="Stable requirement identifier")
    type: str = Field(..., description="Requirement category")
    statement: str = Field(..., description="Requirement statement")
    priority: str = Field(..., description="Requirement priority")
    status: str = Field(..., description="Requirement status")


class RequirementCreate(RequirementBase):
    """Model for creating a new requirement."""

    model_config = {"from_attributes": True}


class RequirementRead(RequirementBase):
    """Model for reading a requirement from the database."""

    model_config = {"from_attributes": True}
