from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Requirement(BaseModel):
    id: str
    project_id: str
    req_type: Literal["business", "functional", "workflow"]
    title: str
    statement: str
    priority: Literal["Must", "Should", "Could"]
    rule_ids: list[str]
    step_ids: list[str]
    evidence_ids: list[str]
    status: Literal["draft", "needs_clarification"] = "draft"
    acceptance_criteria: list[str] = Field(default_factory=list)

    @field_validator("status", mode="before")
    @classmethod
    def reject_approved_status(cls, value: str) -> str:
        if value == "approved":
            raise ValueError("Requirements must never be marked approved.")
        return value


class OpenQuestion(BaseModel):
    id: str
    project_id: str
    question: str
    reason: str
    related_ids: list[str]


class RequirementsOutput(BaseModel):
    schema_version: str = "0.1"
    project_id: str
    requirements: list[Requirement]
    open_questions: list[OpenQuestion]
    warnings: list[str]
