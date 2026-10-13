"""Pydantic models for the process_steps table."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProcessStepBase(BaseModel):
    """Base process step model with common fields."""

    id: str = Field(..., description="Unique process step identifier")
    process_version_id: str = Field(..., description="Process version ID (foreign key)")
    step_key: str = Field(..., description="Stable step identifier")
    name: str = Field(..., description="Human-readable step name")
    actor: str = Field(..., description="Responsible actor or role")
    step_type: str = Field(..., description="Step category or workflow type")
    sequence: int = Field(..., description="Order within the process")


class ProcessStepCreate(ProcessStepBase):
    """Model for creating a new process step."""

    model_config = {"from_attributes": True}


class ProcessStepRead(ProcessStepBase):
    """Model for reading a process step from the database."""

    model_config = {"from_attributes": True}
