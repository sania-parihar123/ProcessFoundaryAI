"""Pydantic models for the business_rules table."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class BusinessRuleBase(BaseModel):
    """Base business rule model with canonical fields."""

    id: str = Field(..., description="Unique business rule identifier")
    project_id: str = Field(..., description="Project ID (foreign key)")
    rule_key: str = Field(..., description="Stable business rule identifier")
    description: str = Field(..., description="Rule statement")
    condition_json: Optional[Any] = Field(None, description="Condition metadata or rule logic")
    status: str = Field(..., description="Current status of the business rule")


class BusinessRuleCreate(BusinessRuleBase):
    """Model for creating a new business rule."""

    model_config = {"from_attributes": True}


class BusinessRuleRead(BusinessRuleBase):
    """Model for reading a business rule from the database."""

    model_config = {"from_attributes": True}
