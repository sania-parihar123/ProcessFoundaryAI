"""Pydantic models for the agent_runs table."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AgentRunBase(BaseModel):
    """Base agent run model with common fields."""

    id: str = Field(..., description="Unique run identifier")
    project_id: str = Field(..., description="Project ID (foreign key)")
    node_name: str = Field(..., description="Agent / node name")
    status: str = Field(..., description="Execution state")
    input_summary: str | None = Field(None, description="Summary of inputs")
    output_ref: str | None = Field(None, description="Reference to output or artifact")
    error: str | None = Field(None, description="Error or failure details")
    created_at: datetime = Field(..., description="Run creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class AgentRunCreate(AgentRunBase):
    """Model for creating a new agent run record."""

    model_config = {"from_attributes": True}


class AgentRunRead(AgentRunBase):
    """Model for reading an agent run record from the database."""

    model_config = {"from_attributes": True}
