"""Pydantic models for the approvals table."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ApprovalBase(BaseModel):
    """Base approval model with common fields."""

    id: str = Field(..., description="Unique approval identifier")
    project_id: str = Field(..., description="Project ID (foreign key)")
    target_type: str = Field(..., description="Type of object being approved")
    target_id: str = Field(..., description="Object identifier")
    decision: str = Field(..., description="Approved, rejected, or requested changes")
    reviewer: str = Field(..., description="Reviewer identity")
    timestamp: datetime = Field(..., description="Approval timestamp")
    comment: str | None = Field(None, description="Optional reviewer comment")


class ApprovalCreate(ApprovalBase):
    """Model for creating a new approval record."""

    model_config = {"from_attributes": True}


class ApprovalRead(ApprovalBase):
    """Model for reading an approval record from the database."""

    model_config = {"from_attributes": True}
