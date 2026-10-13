"""Pydantic models for the artifact_links table."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ArtifactLinkBase(BaseModel):
    """Base artifact link model with common fields."""

    artifact_id: str = Field(..., description="Source artifact ID (foreign key)")
    target_type: str = Field(..., description="Type of target entity")
    target_id: str = Field(..., description="Identifier of the target entity")
    link_type: str = Field(..., description="Type of relationship")


class ArtifactLinkCreate(ArtifactLinkBase):
    """Model for creating a new artifact link."""

    model_config = {"from_attributes": True}


class ArtifactLinkRead(ArtifactLinkBase):
    """Model for reading an artifact link from the database."""

    model_config = {"from_attributes": True}
