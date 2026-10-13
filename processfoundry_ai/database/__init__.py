"""Database layer for ProcessFoundry AI."""

from processfoundry_ai.database.base import Base
from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.connection import get_connection, health_check
from processfoundry_ai.database.models import (
    AgentRun,
    Approval,
    Artifact,
    ArtifactLink,
    BusinessRule,
    ClarificationItem,
    Document,
    DocumentSection,
    EvidenceItem,
    ProcessStep,
    ProcessVersion,
    Project,
    Requirement,
    RequirementLink,
    RuleEvidence,
    TestCase,
)
from processfoundry_ai.database.session import (
    dispose_engine,
    get_engine,
    get_session,
    get_session_factory,
    session_context,
)

__all__ = [
    "DatabaseConfig",
    "get_connection",
    "health_check",
    "Base",
    "Project",
    "Document",
    "DocumentSection",
    "EvidenceItem",
    "ProcessVersion",
    "ProcessStep",
    "BusinessRule",
    "RuleEvidence",
    "ClarificationItem",
    "Requirement",
    "RequirementLink",
    "Artifact",
    "ArtifactLink",
    "TestCase",
    "Approval",
    "AgentRun",
    "get_engine",
    "get_session_factory",
    "get_session",
    "session_context",
    "dispose_engine",
]
