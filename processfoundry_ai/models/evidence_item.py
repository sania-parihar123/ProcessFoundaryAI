"""Pydantic models for the evidence_items table."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class EvidenceItemBase(BaseModel):
    """Base evidence item model with common fields."""

    id: str = Field(..., description="Unique evidence identifier")
    project_id: str = Field(..., description="Project ID (foreign key)")
    document_section_id: str = Field(..., description="Document section ID (foreign key)")
    quote: str = Field(..., description="Relevant text supporting the claim")
    claim_type: str = Field(..., description="Category of the claim")
    confidence: Decimal = Field(..., description="Confidence score associated with the evidence")


class EvidenceItemCreate(EvidenceItemBase):
    """Model for creating a new evidence item."""

    model_config = {"from_attributes": True}


class EvidenceItemRead(EvidenceItemBase):
    """Model for reading an evidence item from the database."""

    model_config = {"from_attributes": True}
