"""FastAPI routes for process version decision operations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.approval import ApprovalCreate, ApprovalRead
from processfoundry_ai.models.process_version import ProcessVersionRead
from processfoundry_ai.repositories.approval_repository import ApprovalRepository
from processfoundry_ai.repositories.process_version_repository import ProcessVersionRepository

process_decisions_router = APIRouter()


def get_db_config() -> DatabaseConfig:
    return DatabaseConfig.from_env()


class ProcessVersionDecisionRequest(BaseModel):
    """Payload to record an approval decision for a process version."""

    decision: str = Field(..., min_length=1, description="Decision: approved, changes_requested, or rejected")
    reviewer: str = Field(..., min_length=1, description="Identity of the reviewer")
    comment: str | None = Field(default=None, description="Optional reviewer comment")


class ProcessVersionDecisionResponse(BaseModel):
    """Response containing updated process version and created approval."""

    process_version: ProcessVersionRead
    approval: ApprovalRead


VALID_DECISIONS = {"approved", "changes_requested", "rejected"}


@process_decisions_router.post(
    "/{version_id}/decision",
    response_model=ProcessVersionDecisionResponse,
    status_code=status.HTTP_200_OK,
)
def record_process_version_decision(version_id: str, item: ProcessVersionDecisionRequest):
    """Record an approval, request-changes, or rejection decision on a process version."""
    config = get_db_config()
    version_repo = ProcessVersionRepository(config)
    version = version_repo.get_by_id(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Process version not found.")

    decision_norm = item.decision.strip().lower()
    if decision_norm not in VALID_DECISIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid decision '{item.decision}'. Allowed decisions: {', '.join(sorted(VALID_DECISIONS))}.",
        )

    # Record the decision in the approvals table
    approval_repo = ApprovalRepository(config)
    approval_payload = ApprovalCreate(
        id=str(uuid4()),
        project_id=version.project_id,
        target_type="process_version",
        target_id=version_id,
        decision=decision_norm,
        reviewer=item.reviewer.strip(),
        timestamp=datetime.now(timezone.utc),
        comment=item.comment.strip() if item.comment else None,
    )
    saved_approval = approval_repo.create(approval_payload)

    # Update process_version status to match the decision
    updated_version = version_repo.update(version_id, {"status": decision_norm})
    if updated_version is None:
        raise HTTPException(status_code=404, detail="Process version not found.")

    return ProcessVersionDecisionResponse(
        process_version=updated_version,
        approval=saved_approval,
    )
