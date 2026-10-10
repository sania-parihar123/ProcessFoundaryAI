"""Pydantic models for the documents table."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document model with common fields."""

    id: str = Field(..., description="Unique document identifier")
    project_id: str = Field(..., description="Project ID (foreign key)")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="File content type")
    checksum: str = Field(..., description="File integrity identifier")
    version: str = Field(..., description="Document version")
    storage_path: str = Field(..., description="Location of the stored file")


class DocumentCreate(DocumentBase):
    """Model for creating a new document."""

    model_config = {"from_attributes": True}


class DocumentRead(DocumentBase):
    """Model for reading a document from the database."""

    model_config = {"from_attributes": True}
