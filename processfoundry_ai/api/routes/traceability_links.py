from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.artifact_link import ArtifactLinkCreate, ArtifactLinkRead
from processfoundry_ai.models.requirement_link import RequirementLinkCreate, RequirementLinkRead
from processfoundry_ai.models.rule_evidence import RuleEvidenceCreate, RuleEvidenceRead
from processfoundry_ai.repositories.artifact_link_repository import ArtifactLinkRepository
from processfoundry_ai.repositories.artifact_repository import ArtifactRepository
from processfoundry_ai.repositories.business_rule_repository import BusinessRuleRepository
from processfoundry_ai.repositories.evidence_item_repository import EvidenceItemRepository
from processfoundry_ai.repositories.project_repository import ProjectRepository
from processfoundry_ai.repositories.requirement_link_repository import RequirementLinkRepository
from processfoundry_ai.repositories.requirement_repository import RequirementRepository
from processfoundry_ai.repositories.rule_evidence_repository import RuleEvidenceRepository

rule_evidence_router = APIRouter()
requirement_links_router = APIRouter()
artifact_links_router = APIRouter()
traceability_router = APIRouter()


def get_db_config() -> DatabaseConfig:
    return DatabaseConfig.from_env()


class RuleEvidenceCreateRequest(BaseModel):
    evidence_id: str = Field(..., min_length=1)


class RequirementLinkCreateRequest(BaseModel):
    target_id: str = Field(..., min_length=1)
    link_type: str = Field(..., min_length=1)


class ArtifactLinkCreateRequest(BaseModel):
    target_type: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    link_type: str = Field(..., min_length=1)


@rule_evidence_router.post(
    "",
    response_model=RuleEvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_rule_evidence(project_id: str, business_rule_id: str, item: RuleEvidenceCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    rule = BusinessRuleRepository(config).get_by_id(business_rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Business rule not found.")
    if rule.project_id != project_id:
        raise HTTPException(status_code=404, detail="Business rule not found for this project.")

    evidence = EvidenceItemRepository(config).get_by_id(item.evidence_id)
    if evidence is None or evidence.project_id != project_id:
        raise HTTPException(status_code=404, detail="Evidence item not found for this project.")

    payload = RuleEvidenceCreate(rule_id=business_rule_id, evidence_id=item.evidence_id)
    return RuleEvidenceRepository(config).create(payload)


@rule_evidence_router.get("", response_model=list[RuleEvidenceRead])
def list_rule_evidence(project_id: str, business_rule_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    rule = BusinessRuleRepository(config).get_by_id(business_rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Business rule not found.")
    if rule.project_id != project_id:
        raise HTTPException(status_code=404, detail="Business rule not found for this project.")

    links = RuleEvidenceRepository(config).list_by_rule_id(business_rule_id)
    return links[offset: offset + limit]


@rule_evidence_router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule_evidence(project_id: str, business_rule_id: str, evidence_id: str):
    config = get_db_config()
    rule = BusinessRuleRepository(config).get_by_id(business_rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Business rule not found.")
    if rule.project_id != project_id:
        raise HTTPException(status_code=404, detail="Business rule not found for this project.")

    link = RuleEvidenceRepository(config).get_by_rule_and_evidence(business_rule_id, evidence_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Rule evidence link not found.")

    # The repository does not support delete-by-key; use the table session in place.
    from processfoundry_ai.database.models import RuleEvidence as RuleEvidenceORM
    from processfoundry_ai.database.session import session_context

    with session_context(config) as session:
        row = session.get(RuleEvidenceORM, {"rule_id": business_rule_id, "evidence_id": evidence_id})
        if row is None:
            raise HTTPException(status_code=404, detail="Rule evidence link not found.")
        session.delete(row)
        session.commit()
    return None


@requirement_links_router.post(
    "",
    response_model=RequirementLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def create_requirement_link(project_id: str, requirement_id: str, item: RequirementLinkCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    requirement = RequirementRepository(config).get_by_id(requirement_id)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    if requirement.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement not found for this project.")

    payload = RequirementLinkCreate(
        source_requirement_id=requirement_id,
        target_id=item.target_id,
        link_type=item.link_type,
    )
    return RequirementLinkRepository(config).create(payload)


@requirement_links_router.get("", response_model=list[RequirementLinkRead])
def list_requirement_links(project_id: str, requirement_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    requirement = RequirementRepository(config).get_by_id(requirement_id)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    if requirement.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement not found for this project.")

    links = RequirementLinkRepository(config).list_by_source_requirement(requirement_id)
    return links[offset: offset + limit]


@artifact_links_router.post(
    "",
    response_model=ArtifactLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def create_artifact_link(project_id: str, artifact_id: str, item: ArtifactLinkCreateRequest):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    artifact = ArtifactRepository(config).get_by_id(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    if artifact.project_id != project_id:
        raise HTTPException(status_code=404, detail="Artifact not found for this project.")

    payload = ArtifactLinkCreate(
        artifact_id=artifact_id,
        target_type=item.target_type,
        target_id=item.target_id,
        link_type=item.link_type,
    )
    return ArtifactLinkRepository(config).create(payload)


@artifact_links_router.get("", response_model=list[ArtifactLinkRead])
def list_artifact_links(project_id: str, artifact_id: str, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0)):
    config = get_db_config()
    artifact = ArtifactRepository(config).get_by_id(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    if artifact.project_id != project_id:
        raise HTTPException(status_code=404, detail="Artifact not found for this project.")

    links = ArtifactLinkRepository(config).list_by_artifact_id(artifact_id)
    return links[offset: offset + limit]


@traceability_router.get("/traceability", response_model=dict)
def get_project_traceability(project_id: str):
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    evidence = EvidenceItemRepository(config).list_by_project(project_id)
    rules = BusinessRuleRepository(config).list_by_project(project_id)
    requirements = RequirementRepository(config).list_by_project(project_id)
    artifacts = ArtifactRepository(config).list_by_project(project_id)
    traceability = {
        "project_id": project_id,
        "evidence_items": [item.model_dump() for item in evidence],
        "business_rules": [rule.model_dump() for rule in rules],
        "requirements": [requirement.model_dump() for requirement in requirements],
        "artifacts": [artifact.model_dump() for artifact in artifacts],
    }

    rule_links = []
    requirement_links = []
    artifact_links = []
    for rule in rules:
        rule_links.extend(
            [row.model_dump() for row in RuleEvidenceRepository(config).list_by_rule_id(rule.id)]
        )
    for requirement in requirements:
        requirement_links.extend(
            [row.model_dump() for row in RequirementLinkRepository(config).list_by_source_requirement(requirement.id)]
        )
    for artifact in artifacts:
        artifact_links.extend(
            [row.model_dump() for row in ArtifactLinkRepository(config).list_by_artifact_id(artifact.id)]
        )

    traceability["rule_evidence_links"] = rule_links
    traceability["requirement_links"] = requirement_links
    traceability["artifact_links"] = artifact_links
    return traceability
