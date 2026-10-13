from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.agent_run import AgentRunCreate, AgentRunRead
from processfoundry_ai.models.approval import ApprovalCreate, ApprovalRead
from processfoundry_ai.models.artifact import ArtifactCreate, ArtifactRead
from processfoundry_ai.models.business_rule import BusinessRuleCreate, BusinessRuleRead
from processfoundry_ai.models.clarification_item import ClarificationItemCreate, ClarificationItemRead
from processfoundry_ai.models.process_step import ProcessStepCreate, ProcessStepRead
from processfoundry_ai.models.process_version import ProcessVersionCreate, ProcessVersionRead
from processfoundry_ai.models.requirement import RequirementCreate, RequirementRead
from processfoundry_ai.models.test_case import TestCaseCreate, TestCaseRead
from processfoundry_ai.repositories.agent_run_repository import AgentRunRepository
from processfoundry_ai.repositories.approval_repository import ApprovalRepository
from processfoundry_ai.repositories.artifact_repository import ArtifactRepository
from processfoundry_ai.repositories.business_rule_repository import BusinessRuleRepository
from processfoundry_ai.repositories.clarification_item_repository import ClarificationItemRepository
from processfoundry_ai.repositories.process_step_repository import ProcessStepRepository
from processfoundry_ai.repositories.process_version_repository import ProcessVersionRepository
from processfoundry_ai.repositories.project_repository import ProjectRepository
from processfoundry_ai.repositories.requirement_repository import RequirementRepository
from processfoundry_ai.repositories.test_case_repository import TestCaseRepository

process_versions_router = APIRouter()
business_rules_router = APIRouter()
clarification_items_router = APIRouter()
requirements_router = APIRouter()
artifacts_router = APIRouter()
approvals_router = APIRouter()
agent_runs_router = APIRouter()
process_steps_router = APIRouter()
test_cases_router = APIRouter()


def get_db_config() -> DatabaseConfig:
    return DatabaseConfig.from_env()


class ProcessVersionCreateRequest(BaseModel):
    version: str = Field(..., min_length=1)
    as_is_json: dict | None = None
    to_be_json: dict | None = None
    status: str = Field(default="draft", min_length=1)


class BusinessRuleCreateRequest(BaseModel):
    rule_key: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    condition_json: dict | None = None
    status: str = Field(default="draft", min_length=1)


class ClarificationItemCreateRequest(BaseModel):
    question: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    status: str = Field(default="open", min_length=1)
    answer: str | None = None
    answered_by: str | None = None


class ClarificationItemAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1)
    answered_by: str = Field(..., min_length=1)
    status: str = Field(default="answered", min_length=1)


class RequirementCreateRequest(BaseModel):
    requirement_key: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    priority: str = Field(..., min_length=1)
    status: str = Field(default="draft", min_length=1)


class ArtifactCreateRequest(BaseModel):
    artifact_type: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    content_json: dict | None = None
    markdown: str | None = None
    status: str = Field(default="draft", min_length=1)


class ApprovalCreateRequest(BaseModel):
    target_type: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    reviewer: str = Field(..., min_length=1)
    comment: str | None = None


class AgentRunCreateRequest(BaseModel):
    node_name: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    input_summary: str | None = None
    output_ref: str | None = None
    error: str | None = None


class ProcessStepCreateRequest(BaseModel):
    step_key: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    actor: str = Field(..., min_length=1)
    step_type: str = Field(..., min_length=1)
    sequence: int = Field(..., ge=0)


class TestCaseCreateRequest(BaseModel):
    test_key: str = Field(..., min_length=1)
    requirement_id: str = Field(..., min_length=1)
    scenario: str = Field(..., min_length=1)
    expected_result: str = Field(..., min_length=1)


@process_versions_router.post(
    "",
    response_model=ProcessVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_process_version(project_id: str, item: ProcessVersionCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    payload = ProcessVersionCreate(
        id=str(uuid4()),
        project_id=project_id,
        version=item.version,
        as_is_json=item.as_is_json,
        to_be_json=item.to_be_json,
        status=item.status,
    )
    return ProcessVersionRepository(config).create(payload)


@process_versions_router.get("", response_model=list[ProcessVersionRead])
def list_process_versions(project_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    versions = ProcessVersionRepository(config).list_by_project(project_id)
    return versions[offset: offset + limit]


@process_versions_router.get("/{process_version_id}", response_model=ProcessVersionRead)
def get_process_version(project_id: str, process_version_id: str):
    config = get_db_config()
    version = ProcessVersionRepository(config).get_by_id(process_version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Process version not found.")
    if version.project_id != project_id:
        raise HTTPException(status_code=404, detail="Process version not found for this project.")
    return version


@process_versions_router.patch("/{process_version_id}", response_model=ProcessVersionRead)
def update_process_version(project_id: str, process_version_id: str, item: ProcessVersionCreateRequest):
    config = get_db_config()
    current = ProcessVersionRepository(config).get_by_id(process_version_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Process version not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Process version not found for this project.")

    updates = {
        "version": item.version,
        "as_is_json": item.as_is_json,
        "to_be_json": item.to_be_json,
        "status": item.status,
    }
    updated = ProcessVersionRepository(config).update(process_version_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="Process version not found.")
    return updated


@process_versions_router.delete("/{process_version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process_version(project_id: str, process_version_id: str):
    config = get_db_config()
    current = ProcessVersionRepository(config).get_by_id(process_version_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Process version not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Process version not found for this project.")

    deleted = ProcessVersionRepository(config).delete(process_version_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Process version not found.")
    return None


@process_steps_router.post(
    "",
    response_model=ProcessStepRead,
    status_code=status.HTTP_201_CREATED,
)
def create_process_step(process_version_id: str, item: ProcessStepCreateRequest):
    config = get_db_config()
    version = ProcessVersionRepository(config).get_by_id(process_version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Process version not found.")

    payload = ProcessStepCreate(
        id=str(uuid4()),
        process_version_id=process_version_id,
        step_key=item.step_key,
        name=item.name,
        actor=item.actor,
        step_type=item.step_type,
        sequence=item.sequence,
    )
    return ProcessStepRepository(config).create(payload)


@process_steps_router.get("", response_model=list[ProcessStepRead])
def list_process_steps(process_version_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    if ProcessVersionRepository(config).get_by_id(process_version_id) is None:
        raise HTTPException(status_code=404, detail="Process version not found.")

    steps = ProcessStepRepository(config).list_by_process_version(process_version_id)
    return steps[offset: offset + limit]


@process_steps_router.get("/{step_id}", response_model=ProcessStepRead)
def get_process_step(process_version_id: str, step_id: str):
    config = get_db_config()
    step = ProcessStepRepository(config).get_by_id(step_id)
    if step is None:
        raise HTTPException(status_code=404, detail="Process step not found.")
    if step.process_version_id != process_version_id:
        raise HTTPException(status_code=404, detail="Process step not found for this process version.")
    return step


@process_steps_router.patch("/{step_id}", response_model=ProcessStepRead)
def update_process_step(process_version_id: str, step_id: str, item: ProcessStepCreateRequest):
    config = get_db_config()
    current = ProcessStepRepository(config).get_by_id(step_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Process step not found.")
    if current.process_version_id != process_version_id:
        raise HTTPException(status_code=404, detail="Process step not found for this process version.")

    updates = {
        "step_key": item.step_key,
        "name": item.name,
        "actor": item.actor,
        "step_type": item.step_type,
        "sequence": item.sequence,
    }
    updated = ProcessStepRepository(config).update(step_id, updates)
    return updated or (_ for _ in ()).throw(HTTPException(status_code=404, detail="Process step not found."))


@process_steps_router.delete("/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process_step(process_version_id: str, step_id: str):
    config = get_db_config()
    current = ProcessStepRepository(config).get_by_id(step_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Process step not found.")
    if current.process_version_id != process_version_id:
        raise HTTPException(status_code=404, detail="Process step not found for this process version.")

    deleted = ProcessStepRepository(config).delete(step_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Process step not found.")
    return None


@business_rules_router.post("", response_model=BusinessRuleRead, status_code=status.HTTP_201_CREATED)
def create_business_rule(project_id: str, item: BusinessRuleCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    payload = BusinessRuleCreate(
        id=str(uuid4()),
        project_id=project_id,
        rule_key=item.rule_key,
        description=item.description,
        condition_json=item.condition_json,
        status=item.status,
    )
    return BusinessRuleRepository(config).create(payload)


@business_rules_router.get("", response_model=list[BusinessRuleRead])
def list_business_rules(project_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    rules = BusinessRuleRepository(config).list_by_project(project_id)
    return rules[offset: offset + limit]


@business_rules_router.get("/{business_rule_id}", response_model=BusinessRuleRead)
def get_business_rule(project_id: str, business_rule_id: str):
    config = get_db_config()
    rule = BusinessRuleRepository(config).get_by_id(business_rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Business rule not found.")
    if rule.project_id != project_id:
        raise HTTPException(status_code=404, detail="Business rule not found for this project.")
    return rule


@business_rules_router.patch("/{business_rule_id}", response_model=BusinessRuleRead)
def update_business_rule(project_id: str, business_rule_id: str, item: BusinessRuleCreateRequest):
    config = get_db_config()
    current = BusinessRuleRepository(config).get_by_id(business_rule_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Business rule not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Business rule not found for this project.")

    updates = {
        "rule_key": item.rule_key,
        "description": item.description,
        "condition_json": item.condition_json,
        "status": item.status,
    }
    updated = BusinessRuleRepository(config).update(business_rule_id, updates)
    return updated or (_ for _ in ()).throw(HTTPException(status_code=404, detail="Business rule not found."))


@business_rules_router.delete("/{business_rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business_rule(project_id: str, business_rule_id: str):
    config = get_db_config()
    current = BusinessRuleRepository(config).get_by_id(business_rule_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Business rule not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Business rule not found for this project.")

    deleted = BusinessRuleRepository(config).delete(business_rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Business rule not found.")
    return None


@clarification_items_router.post("", response_model=ClarificationItemRead, status_code=status.HTTP_201_CREATED)
def create_clarification_item(project_id: str, item: ClarificationItemCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    payload = ClarificationItemCreate(
        id=str(uuid4()),
        project_id=project_id,
        question=item.question,
        reason=item.reason,
        status=item.status,
        answer=item.answer,
        answered_by=item.answered_by,
    )
    return ClarificationItemRepository(config).create(payload)


@clarification_items_router.get("", response_model=list[ClarificationItemRead])
def list_clarification_items(project_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    items = ClarificationItemRepository(config).list_by_project(project_id)
    return items[offset: offset + limit]


@clarification_items_router.get("/{clarification_item_id}", response_model=ClarificationItemRead)
def get_clarification_item(project_id: str, clarification_item_id: str):
    config = get_db_config()
    item = ClarificationItemRepository(config).get_by_id(clarification_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Clarification item not found.")
    if item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Clarification item not found for this project.")
    return item


@clarification_items_router.patch("/{clarification_item_id}/answer", response_model=ClarificationItemRead)
def answer_clarification_item(project_id: str, clarification_item_id: str, item: ClarificationItemAnswerRequest):
    config = get_db_config()
    current = ClarificationItemRepository(config).get_by_id(clarification_item_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Clarification item not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Clarification item not found for this project.")

    updates = {
        "answer": item.answer,
        "answered_by": item.answered_by,
        "status": item.status,
    }
    updated = ClarificationItemRepository(config).update(clarification_item_id, updates)
    return updated or (_ for _ in ()).throw(HTTPException(status_code=404, detail="Clarification item not found."))


@clarification_items_router.delete("/{clarification_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clarification_item(project_id: str, clarification_item_id: str):
    config = get_db_config()
    current = ClarificationItemRepository(config).get_by_id(clarification_item_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Clarification item not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Clarification item not found for this project.")

    deleted = ClarificationItemRepository(config).delete(clarification_item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Clarification item not found.")
    return None


@requirements_router.post("", response_model=RequirementRead, status_code=status.HTTP_201_CREATED)
def create_requirement(project_id: str, item: RequirementCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    payload = RequirementCreate(
        id=str(uuid4()),
        project_id=project_id,
        requirement_key=item.requirement_key,
        type=item.type,
        statement=item.statement,
        priority=item.priority,
        status=item.status,
    )
    return RequirementRepository(config).create(payload)


@requirements_router.get("", response_model=list[RequirementRead])
def list_requirements(project_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    requirements = RequirementRepository(config).list_by_project(project_id)
    return requirements[offset: offset + limit]


@requirements_router.get("/{requirement_id}", response_model=RequirementRead)
def get_requirement(project_id: str, requirement_id: str):
    config = get_db_config()
    requirement = RequirementRepository(config).get_by_id(requirement_id)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    if requirement.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement not found for this project.")
    return requirement


@requirements_router.patch("/{requirement_id}", response_model=RequirementRead)
def update_requirement(project_id: str, requirement_id: str, item: RequirementCreateRequest):
    config = get_db_config()
    current = RequirementRepository(config).get_by_id(requirement_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement not found for this project.")

    updates = {
        "requirement_key": item.requirement_key,
        "type": item.type,
        "statement": item.statement,
        "priority": item.priority,
        "status": item.status,
    }
    updated = RequirementRepository(config).update(requirement_id, updates)
    return updated or (_ for _ in ()).throw(HTTPException(status_code=404, detail="Requirement not found."))


@requirements_router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_requirement(project_id: str, requirement_id: str):
    config = get_db_config()
    current = RequirementRepository(config).get_by_id(requirement_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement not found for this project.")

    deleted = RequirementRepository(config).delete(requirement_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    return None


@artifacts_router.post("", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
def create_artifact(project_id: str, item: ArtifactCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    payload = ArtifactCreate(
        id=str(uuid4()),
        project_id=project_id,
        artifact_type=item.artifact_type,
        version=item.version,
        content_json=item.content_json,
        markdown=item.markdown,
        status=item.status,
    )
    return ArtifactRepository(config).create(payload)


@artifacts_router.get("", response_model=list[ArtifactRead])
def list_artifacts(project_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    artifacts = ArtifactRepository(config).list_by_project(project_id)
    return artifacts[offset: offset + limit]


@artifacts_router.get("/{artifact_id}", response_model=ArtifactRead)
def get_artifact(project_id: str, artifact_id: str):
    config = get_db_config()
    artifact = ArtifactRepository(config).get_by_id(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    if artifact.project_id != project_id:
        raise HTTPException(status_code=404, detail="Artifact not found for this project.")
    return artifact


@artifacts_router.patch("/{artifact_id}", response_model=ArtifactRead)
def update_artifact(project_id: str, artifact_id: str, item: ArtifactCreateRequest):
    config = get_db_config()
    current = ArtifactRepository(config).get_by_id(artifact_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Artifact not found for this project.")

    updates = {
        "artifact_type": item.artifact_type,
        "version": item.version,
        "content_json": item.content_json,
        "markdown": item.markdown,
        "status": item.status,
    }
    updated = ArtifactRepository(config).update(artifact_id, updates)
    return updated or (_ for _ in ()).throw(HTTPException(status_code=404, detail="Artifact not found."))


@artifacts_router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact(project_id: str, artifact_id: str):
    config = get_db_config()
    current = ArtifactRepository(config).get_by_id(artifact_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Artifact not found for this project.")

    deleted = ArtifactRepository(config).delete(artifact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return None


@approvals_router.post("", response_model=ApprovalRead, status_code=status.HTTP_201_CREATED)
def create_approval(project_id: str, item: ApprovalCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    payload = ApprovalCreate(
        id=str(uuid4()),
        project_id=project_id,
        target_type=item.target_type,
        target_id=item.target_id,
        decision=item.decision,
        reviewer=item.reviewer,
        timestamp=datetime.now(timezone.utc),
        comment=item.comment,
    )
    return ApprovalRepository(config).create(payload)


@approvals_router.get("", response_model=list[ApprovalRead])
def list_approvals(project_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    approvals = ApprovalRepository(config).list_by_project(project_id)
    return approvals[offset: offset + limit]


@approvals_router.get("/{approval_id}", response_model=ApprovalRead)
def get_approval(project_id: str, approval_id: str):
    config = get_db_config()
    approval = ApprovalRepository(config).get_by_id(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found.")
    if approval.project_id != project_id:
        raise HTTPException(status_code=404, detail="Approval not found for this project.")
    return approval


@approvals_router.patch("/{approval_id}", response_model=ApprovalRead)
def update_approval(project_id: str, approval_id: str, item: ApprovalCreateRequest):
    config = get_db_config()
    current = ApprovalRepository(config).get_by_id(approval_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Approval not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Approval not found for this project.")

    updates = {
        "target_type": item.target_type,
        "target_id": item.target_id,
        "decision": item.decision,
        "reviewer": item.reviewer,
        "comment": item.comment,
    }
    updated = ApprovalRepository(config).update(approval_id, updates)
    return updated or (_ for _ in ()).throw(HTTPException(status_code=404, detail="Approval not found."))


@approvals_router.delete("/{approval_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_approval(project_id: str, approval_id: str):
    config = get_db_config()
    current = ApprovalRepository(config).get_by_id(approval_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Approval not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Approval not found for this project.")

    deleted = ApprovalRepository(config).delete(approval_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Approval not found.")
    return None


@agent_runs_router.post("", response_model=AgentRunRead, status_code=status.HTTP_201_CREATED)
def create_agent_run(project_id: str, item: AgentRunCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    payload = AgentRunCreate(
        id=str(uuid4()),
        project_id=project_id,
        node_name=item.node_name,
        status=item.status,
        input_summary=item.input_summary,
        output_ref=item.output_ref,
        error=item.error,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return AgentRunRepository(config).create(payload)


@agent_runs_router.get("", response_model=list[AgentRunRead])
def list_agent_runs(project_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    runs = AgentRunRepository(config).list_by_project(project_id)
    return runs[offset: offset + limit]


@agent_runs_router.get("/{agent_run_id}", response_model=AgentRunRead)
def get_agent_run(project_id: str, agent_run_id: str):
    config = get_db_config()
    run = AgentRunRepository(config).get_by_id(agent_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    if run.project_id != project_id:
        raise HTTPException(status_code=404, detail="Agent run not found for this project.")
    return run


@agent_runs_router.patch("/{agent_run_id}", response_model=AgentRunRead)
def update_agent_run(project_id: str, agent_run_id: str, item: AgentRunCreateRequest):
    config = get_db_config()
    current = AgentRunRepository(config).get_by_id(agent_run_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Agent run not found for this project.")

    updates = {
        "node_name": item.node_name,
        "status": item.status,
        "input_summary": item.input_summary,
        "output_ref": item.output_ref,
        "error": item.error,
        "updated_at": datetime.now(timezone.utc),
    }
    updated = AgentRunRepository(config).update(agent_run_id, updates)
    return updated or (_ for _ in ()).throw(HTTPException(status_code=404, detail="Agent run not found."))


@agent_runs_router.delete("/{agent_run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_run(project_id: str, agent_run_id: str):
    config = get_db_config()
    current = AgentRunRepository(config).get_by_id(agent_run_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Agent run not found for this project.")

    deleted = AgentRunRepository(config).delete(agent_run_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    return None


@test_cases_router.post("", response_model=TestCaseRead, status_code=status.HTTP_201_CREATED)
def create_test_case(project_id: str, item: TestCaseCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    requirement = RequirementRepository(config).get_by_id(item.requirement_id)
    if requirement is None or requirement.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement not found for this project.")

    payload = TestCaseCreate(
        id=str(uuid4()),
        project_id=project_id,
        test_key=item.test_key,
        requirement_id=item.requirement_id,
        scenario=item.scenario,
        expected_result=item.expected_result,
    )
    return TestCaseRepository(config).create(payload)


@test_cases_router.get("", response_model=list[TestCaseRead])
def list_test_cases(project_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    tests = TestCaseRepository(config).list_by_project(project_id)
    return tests[offset: offset + limit]


@test_cases_router.get("/{test_case_id}", response_model=TestCaseRead)
def get_test_case(project_id: str, test_case_id: str):
    config = get_db_config()
    case = TestCaseRepository(config).get_by_id(test_case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Test case not found.")
    if case.project_id != project_id:
        raise HTTPException(status_code=404, detail="Test case not found for this project.")
    return case


@test_cases_router.patch("/{test_case_id}", response_model=TestCaseRead)
def update_test_case(project_id: str, test_case_id: str, item: TestCaseCreateRequest):
    config = get_db_config()
    current = TestCaseRepository(config).get_by_id(test_case_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Test case not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Test case not found for this project.")

    requirement = RequirementRepository(config).get_by_id(item.requirement_id)
    if requirement is None or requirement.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement not found for this project.")

    updates = {
        "test_key": item.test_key,
        "requirement_id": item.requirement_id,
        "scenario": item.scenario,
        "expected_result": item.expected_result,
    }
    updated = TestCaseRepository(config).update(test_case_id, updates)
    return updated or (_ for _ in ()).throw(HTTPException(status_code=404, detail="Test case not found."))


@test_cases_router.delete("/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case(project_id: str, test_case_id: str):
    config = get_db_config()
    current = TestCaseRepository(config).get_by_id(test_case_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Test case not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Test case not found for this project.")

    deleted = TestCaseRepository(config).delete(test_case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Test case not found.")
    return None
