"""Pydantic models for the rule_evidence table."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RuleEvidenceBase(BaseModel):
    """Base rule-evidence link model with canonical fields."""

    rule_id: str = Field(..., description="Business rule ID (foreign key)")
    evidence_id: str = Field(..., description="Evidence item ID (foreign key)")


class RuleEvidenceCreate(RuleEvidenceBase):
    """Model for creating a new rule-evidence link."""

    model_config = {"from_attributes": True}


class RuleEvidenceRead(RuleEvidenceBase):
    """Model for reading a rule-evidence link from the database."""

    model_config = {"from_attributes": True}
