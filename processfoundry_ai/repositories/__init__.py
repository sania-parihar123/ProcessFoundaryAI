"""Repository modules for CRUD operations on database tables.

These modules implement query/insert/update/delete operations for each table.
They depend on the models in processfoundry_ai.models and the connection
utilities in processfoundry_ai.database.
"""

from __future__ import annotations

from processfoundry_ai.repositories.agent_run_repository import AgentRunRepository
from processfoundry_ai.repositories.approval_repository import ApprovalRepository
from processfoundry_ai.repositories.artifact_link_repository import ArtifactLinkRepository
from processfoundry_ai.repositories.artifact_repository import ArtifactRepository
from processfoundry_ai.repositories.business_rule_repository import BusinessRuleRepository
from processfoundry_ai.repositories.clarification_item_repository import (
    ClarificationItemRepository,
)
from processfoundry_ai.repositories.document_repository import DocumentRepository
from processfoundry_ai.repositories.document_section_repository import (
    DocumentSectionRepository,
)
from processfoundry_ai.repositories.evidence_item_repository import (
    EvidenceItemRepository,
)
from processfoundry_ai.repositories.process_step_repository import ProcessStepRepository
from processfoundry_ai.repositories.process_version_repository import (
    ProcessVersionRepository,
)
from processfoundry_ai.repositories.project_repository import ProjectRepository
from processfoundry_ai.repositories.requirement_link_repository import (
    RequirementLinkRepository,
)
from processfoundry_ai.repositories.requirement_repository import RequirementRepository
from processfoundry_ai.repositories.rule_evidence_repository import RuleEvidenceRepository
from processfoundry_ai.repositories.test_case_repository import TestCaseRepository

__all__ = [
    "ProjectRepository",
    "DocumentRepository",
    "DocumentSectionRepository",
    "EvidenceItemRepository",
    "ProcessVersionRepository",
    "ProcessStepRepository",
    "BusinessRuleRepository",
    "RuleEvidenceRepository",
    "RequirementRepository",
    "RequirementLinkRepository",
    "ClarificationItemRepository",
    "ArtifactRepository",
    "ArtifactLinkRepository",
    "TestCaseRepository",
    "ApprovalRepository",
    "AgentRunRepository",
]


