"""Repository modules for CRUD operations on database tables.

These modules implement query/insert/update/delete operations for each table.
They depend on the models in processfoundry_ai.models and the connection
utilities in processfoundry_ai.database.
"""

from __future__ import annotations

from processfoundry_ai.repositories.document_repository import (
    DocumentRepository,
)
from processfoundry_ai.repositories.document_section_repository import (
    DocumentSectionRepository,
)
from processfoundry_ai.repositories.evidence_item_repository import (
    EvidenceItemRepository,
)
from processfoundry_ai.repositories.project_repository import (
    ProjectRepository,
)

__all__ = [
    "ProjectRepository",
    "DocumentRepository",
    "DocumentSectionRepository",
    "EvidenceItemRepository",
]


