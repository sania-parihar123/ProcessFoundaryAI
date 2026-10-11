from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel

SCHEMA_VERSION = "0.1"

class SourceSection(BaseModel):
    id: str                              # matches her document_sections.id
    document_id: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    text: str

class EvidenceRecord(BaseModel):
    id: str                              # "EVD-001", assigned by code, never by the LLM
    project_id: str                      # passed in by the caller
    document_section_id: str
    quote: str                           # exact text from the source
    claim_type: Literal["step", "rule", "actor", "deadline", "form", "other"]
    confidence: Decimal                  # converted from high/medium/low by my code

class StepLink(BaseModel):
    to_step_id: str
    condition: Optional[str] = None

class DiscoveredStep(BaseModel):
    schema_version: str = SCHEMA_VERSION
    step_id: str                         # "STEP-001"
    name: str
    actor: Optional[str] = None          # None if the source doesn't say
    state: Optional[str] = None
    inputs: list[str] = []
    outputs: list[str] = []
    next_steps: list[StepLink] = []
    evidence_ids: list[str]
    unknowns: list[str] = []

class RuleRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    rule_id: str                         # "BR-001"
    statement: str
    condition: Optional[str] = None
    action: Optional[str] = None
    scope: Optional[str] = None
    effective_context: Optional[str] = None
    evidence_ids: list[str]
    status: Literal["needs_review"] = "needs_review"   # never "approved"


class MemberTwoOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    project_id: str
    document_id: str
    sections: list[SourceSection] = []
    evidence: list[EvidenceRecord] = []
    steps: list[DiscoveredStep] = []
    rules: list[RuleRecord] = []
    warnings: list[str] = []