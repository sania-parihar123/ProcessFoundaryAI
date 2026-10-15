"""State contract for ProcessFoundry AI graph runs."""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Any, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


Record: TypeAlias = dict[str, Any]
NonEmptyId: TypeAlias = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ApprovalStatus(StrEnum):
    """Approval states that may be assigned by an authorized human boundary."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"


class LifecycleStatus(StrEnum):
    """Lifecycle states used by the planned graph routers."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED_FOR_HUMAN = "paused_for_human"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class TraceEvent(BaseModel):
    """An observable event emitted by a graph node or state transition."""

    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    node: str | None = None
    message: str = Field(min_length=1)
    details: Record = Field(default_factory=dict)


class ProcessFoundryState(BaseModel):
    """Process-neutral state shared by ProcessFoundry's planned graph nodes.

    Records supplied by Member 1 and Member 2 remain provisional dictionaries
    until their reviewed contracts are available.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    run_id: NonEmptyId = Field(min_length=1)
    project_id: NonEmptyId = Field(min_length=1)
    process_type: NonEmptyId = Field(min_length=1)
    process_description: str = ""

    source_document_ids: list[NonEmptyId] = Field(default_factory=list)
    extracted_sections: list[Record] = Field(default_factory=list)
    evidence_items: list[Record] = Field(default_factory=list)
    as_is_process: list[Record] = Field(default_factory=list)
    candidate_business_rules: list[Record] = Field(default_factory=list)

    input_bundle: Record = Field(default_factory=dict)
    source_index: Record = Field(default_factory=dict)
    gap_issues: list[Record] = Field(default_factory=list)
    conflict_issues: list[Record] = Field(default_factory=list)
    clarification_questions: list[Record] = Field(default_factory=list)
    human_answers: list[Record] = Field(default_factory=list)
    verified_facts: list[Record] = Field(default_factory=list)
    to_be_process: list[Record] = Field(default_factory=list)

    automation_assessment: Record = Field(default_factory=dict)
    requirements: list[Record] = Field(default_factory=list)
    artifacts: list[Record] = Field(default_factory=list)
    workflow_proposal: Record = Field(default_factory=dict)

    validation_errors: list[str] = Field(default_factory=list)
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    lifecycle_status: LifecycleStatus = LifecycleStatus.CREATED
    current_node: str | None = None
    next_action: str = "initialize"
    pending_question_ids: list[NonEmptyId] = Field(default_factory=list)
    retry_count: int = Field(default=0, ge=0)
    last_error: Record = Field(default_factory=dict)
    trace_events: list[TraceEvent] = Field(default_factory=list)
    config: Record = Field(default_factory=dict)
    schema_version: str = "1"
    decisions: list[Record] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
