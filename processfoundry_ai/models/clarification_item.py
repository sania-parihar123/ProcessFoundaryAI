"""Pydantic models for the clarification_items table."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ClarificationItemBase(BaseModel):
    """Base clarification item model with canonical fields."""

    id: str = Field(..., description="Unique clarification identifier")
    project_id: str = Field(..., description="Project ID (foreign key)")
    question: str = Field(..., description="Clarification question")
    reason: str = Field(..., description="Why the question is required")
    status: str = Field(..., description="Current status")
    answer: Optional[str] = Field(None, description="Human answer if resolved")
    answered_by: Optional[str] = Field(None, description="Reviewer identity")


class ClarificationItemCreate(ClarificationItemBase):
    """Model for creating a new clarification item."""

    model_config = {"from_attributes": True}


class ClarificationItemRead(ClarificationItemBase):
    """Model for reading a clarification item from the database."""

    model_config = {"from_attributes": True}
