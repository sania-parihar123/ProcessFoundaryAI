"""Pydantic models for the process_versions table."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ProcessVersionBase(BaseModel):
    """Base process version model."""

    id: str = Field(..., description="Unique process version identifier")
    project_id: str = Field(..., description="Project ID (foreign key)")
    version: str = Field(..., description="Version number or identifier")
    as_is_json: Optional[Any] = Field(None, description="Canonical As-Is process model payload")
    to_be_json: Optional[Any] = Field(None, description="Canonical To-Be model payload")
    status: str = Field(..., description="Current status of the process version")


class ProcessVersionCreate(ProcessVersionBase):
    """Model for creating a new process version."""

    model_config = {"from_attributes": True}


class ProcessVersionRead(ProcessVersionBase):
    """Model for reading a process version from the database."""

    model_config = {"from_attributes": True}
