"""Pydantic models for the document_sections table."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DocumentSectionBase(BaseModel):
    """Base document section model with common fields."""

    id: str = Field(..., description="Unique section identifier")
    document_id: str = Field(..., description="Document ID (foreign key)")
    page_number: Optional[int] = Field(None, description="Source page number, when available")
    section_title: Optional[str] = Field(None, description="Section heading, when available")
    text: str = Field(..., description="Extracted text content")


class DocumentSectionCreate(DocumentSectionBase):
    """Model for creating a new document section."""

    model_config = {"from_attributes": True}


class DocumentSectionRead(DocumentSectionBase):
    """Model for reading a document section from the database."""

    model_config = {"from_attributes": True}
