"""Pydantic models for the artifacts table."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ArtifactBase(BaseModel):
    """Base artifact model with canonical fields."""

    id: str = Field(..., description="Unique artifact identifier")
    project_id: str = Field(..., description="Project ID (foreign key)")
    artifact_type: str = Field(..., description="Type of artifact")
    version: str = Field(..., description="Artifact version")
    content_json: Optional[Any] = Field(None, description="Structured artifact payload")
    markdown: Optional[str] = Field(None, description="Markdown export content")
    status: str = Field(..., description="Artifact status")


class ArtifactCreate(ArtifactBase):
    """Model for creating a new artifact."""

    model_config = {"from_attributes": True}


class ArtifactRead(ArtifactBase):
    """Model for reading an artifact from the database."""

    model_config = {"from_attributes": True}
