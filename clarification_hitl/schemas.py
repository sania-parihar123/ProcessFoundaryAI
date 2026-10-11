"""Plain data records for the human-in-the-loop (HITL) step.

Rule: a human decision is only ever created by record_decision() in store.py.
Nothing in this folder ever sets approval to "approved" on its own.
"""
from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


QuestionKind = Literal["missing_actor", "conflicting_rules", "ambiguous_term", "missing_info", "other"]
QuestionStatus = Literal["open", "answered", "stale"]


class ClarificationQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str
    project_id: str
    kind: QuestionKind
    text: str
    reason: str = ""
    fingerprint: str                      # same problem -> same fingerprint (no duplicate questions)
    step_ids: List[str] = Field(default_factory=list)
    rule_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    options: List[str] = Field(default_factory=list)   # optional multiple-choice answers
    status: QuestionStatus = "open"
    created_at: str = Field(default_factory=now_iso)


class HumanAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer_id: str
    question_id: str
    answer_text: str
    answered_by: str
    role: str
    answered_at: str = Field(default_factory=now_iso)
    superseded: bool = False              # True once a newer answer replaces it (old one is kept)


class HumanDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision_id: str
    subject: str                          # what was decided on, e.g. "requirements" or a rule id
    decision: Literal["approve", "reject", "request_changes"]
    decided_by: str
    role: str
    reason: str = ""
    decided_at: str = Field(default_factory=now_iso)
