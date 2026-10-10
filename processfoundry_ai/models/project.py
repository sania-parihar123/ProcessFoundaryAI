"""Pydantic models for the projects table."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ProjectBase(BaseModel):
    """Base project model with common fields."""

    id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name (must not be empty or whitespace only)")
    process_type: str = Field(..., description="Type of college process")
    description: str = Field(..., description="Project description")
    status: str = Field(..., description="Current project status")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate and normalize project name.
        
        Rejects empty strings and strings containing only whitespace.
        Strips leading and trailing whitespace for consistency.
        
        Args:
            value: The project name to validate.
            
        Returns:
            The normalized (stripped) project name.
            
        Raises:
            ValueError: If name is empty or contains only whitespace.
        """
        if not isinstance(value, str):
            raise ValueError("Project name must be a string")
        
        stripped = value.strip()
        if not stripped:
            raise ValueError("Project name must not be empty or contain only whitespace")
        
        return stripped


class ProjectCreate(ProjectBase):
    """Model for creating a new project."""

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")

    model_config = {"from_attributes": True}


class ProjectRead(ProjectBase):
    """Model for reading a project from the database."""

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")

    model_config = {"from_attributes": True}
