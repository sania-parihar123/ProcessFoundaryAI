"""Pydantic models for the requirement_links table."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RequirementLinkBase(BaseModel):
    """Base requirement-link model."""

    source_requirement_id: str = Field(..., description="Source requirement ID (foreign key)")
    target_id: str = Field(..., description="Target entity identifier")
    link_type: str = Field(..., description="Type of relationship")


class RequirementLinkCreate(RequirementLinkBase):
    """Model for creating a new requirement link."""

    model_config = {"from_attributes": True}


class RequirementLinkRead(RequirementLinkBase):
    """Model for reading a requirement link from the database."""

    model_config = {"from_attributes": True}
