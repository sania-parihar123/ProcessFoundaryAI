from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.document_section import DocumentSectionCreate, DocumentSectionRead
from processfoundry_ai.models.evidence_item import EvidenceItemCreate, EvidenceItemRead
from processfoundry_ai.repositories.document_repository import DocumentRepository
from processfoundry_ai.repositories.document_section_repository import DocumentSectionRepository
from processfoundry_ai.repositories.evidence_item_repository import EvidenceItemRepository
from processfoundry_ai.repositories.project_repository import ProjectRepository


document_sections_router = APIRouter()
evidence_items_router = APIRouter()


def get_db_config() -> DatabaseConfig:
    return DatabaseConfig.from_env()


class DocumentSectionCreateRequest(BaseModel):
    page_number: int | None = None
    section_title: str | None = None
    text: str = Field(..., min_length=1)


class EvidenceItemCreateRequest(BaseModel):
    document_section_id: str = Field(..., min_length=1)
    quote: str = Field(..., min_length=1)
    claim_type: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)


@document_sections_router.post(
    "",
    response_model=DocumentSectionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_document_section(project_id: str, document_id: str, item: DocumentSectionCreateRequest):
    config = get_db_config()
    project = ProjectRepository(config).get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    document = DocumentRepository(config).get_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    if document.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found for this project.")

    try:
        section = DocumentSectionCreate(
            id=str(uuid4()),
            document_id=document_id,
            page_number=item.page_number,
            section_title=item.section_title,
            text=item.text,
        )
        return DocumentSectionRepository(config).create(section)
    except Exception as exc:  # pragma: no cover - repository surfaces SQLAlchemyError
        raise HTTPException(status_code=503, detail=f"Could not save the document section: {exc}") from exc


@document_sections_router.get("", response_model=list[DocumentSectionRead])
def list_document_sections(
    project_id: str,
    document_id: str,
    limit: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
):
    config = get_db_config()
    project = ProjectRepository(config).get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    document = DocumentRepository(config).get_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    if document.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found for this project.")

    sections = DocumentSectionRepository(config).list_by_document(document_id)
    return sections[offset: offset + limit]


@document_sections_router.get("/{section_id}", response_model=DocumentSectionRead)
def get_document_section(project_id: str, document_id: str, section_id: str):
    config = get_db_config()
    section = DocumentSectionRepository(config).get_by_id(section_id)
    if section is None:
        raise HTTPException(status_code=404, detail="Document section not found.")

    document = DocumentRepository(config).get_by_id(section.document_id)
    if document is None or document.project_id != project_id or document.id != document_id:
        raise HTTPException(status_code=404, detail="Document section not found for this project.")

    return section


@document_sections_router.patch("/{section_id}", response_model=DocumentSectionRead)
def update_document_section(project_id: str, document_id: str, section_id: str, item: DocumentSectionCreateRequest):
    config = get_db_config()
    current = DocumentSectionRepository(config).get_by_id(section_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Document section not found.")

    document = DocumentRepository(config).get_by_id(current.document_id)
    if document is None or document.project_id != project_id or document.id != document_id:
        raise HTTPException(status_code=404, detail="Document section not found for this project.")

    updates = {
        "page_number": item.page_number,
        "section_title": item.section_title,
        "text": item.text,
    }
    updated = DocumentSectionRepository(config).update(section_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="Document section not found.")
    return updated


@document_sections_router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_section(project_id: str, document_id: str, section_id: str):
    config = get_db_config()
    current = DocumentSectionRepository(config).get_by_id(section_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Document section not found.")

    document = DocumentRepository(config).get_by_id(current.document_id)
    if document is None or document.project_id != project_id or document.id != document_id:
        raise HTTPException(status_code=404, detail="Document section not found for this project.")

    deleted = DocumentSectionRepository(config).delete(section_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document section not found.")
    return None


@evidence_items_router.post(
    "",
    response_model=EvidenceItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_evidence_item(project_id: str, item: EvidenceItemCreateRequest):
    config = get_db_config()
    project = ProjectRepository(config).get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    section = DocumentSectionRepository(config).get_by_id(item.document_section_id)
    if section is None:
        raise HTTPException(status_code=404, detail="Document section not found.")

    document = DocumentRepository(config).get_by_id(section.document_id)
    if document is None or document.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document section not found for this project.")

    evidence = EvidenceItemCreate(
        id=str(uuid4()),
        project_id=project_id,
        document_section_id=item.document_section_id,
        quote=item.quote,
        claim_type=item.claim_type,
        confidence=item.confidence,
    )
    return EvidenceItemRepository(config).create(evidence)


@evidence_items_router.get("", response_model=list[EvidenceItemRead])
def list_evidence_items(
    project_id: str,
    limit: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
):
    config = get_db_config()
    project = ProjectRepository(config).get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    items = EvidenceItemRepository(config).list_by_project(project_id)
    return items[offset: offset + limit]


@evidence_items_router.get("/{evidence_id}", response_model=EvidenceItemRead)
def get_evidence_item(project_id: str, evidence_id: str):
    config = get_db_config()
    evidence = EvidenceItemRepository(config).get_by_id(evidence_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence item not found.")
    if evidence.project_id != project_id:
        raise HTTPException(status_code=404, detail="Evidence item not found for this project.")
    return evidence


@evidence_items_router.patch("/{evidence_id}", response_model=EvidenceItemRead)
def update_evidence_item(project_id: str, evidence_id: str, item: EvidenceItemCreateRequest):
    config = get_db_config()
    current = EvidenceItemRepository(config).get_by_id(evidence_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Evidence item not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Evidence item not found for this project.")

    section = DocumentSectionRepository(config).get_by_id(item.document_section_id)
    if section is None:
        raise HTTPException(status_code=404, detail="Document section not found.")
    document = DocumentRepository(config).get_by_id(section.document_id)
    if document is None or document.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document section not found for this project.")

    updates = {
        "document_section_id": item.document_section_id,
        "quote": item.quote,
        "claim_type": item.claim_type,
        "confidence": item.confidence,
    }
    updated = EvidenceItemRepository(config).update(evidence_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="Evidence item not found.")
    return updated


@evidence_items_router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence_item(project_id: str, evidence_id: str):
    config = get_db_config()
    current = EvidenceItemRepository(config).get_by_id(evidence_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Evidence item not found.")
    if current.project_id != project_id:
        raise HTTPException(status_code=404, detail="Evidence item not found for this project.")

    deleted = EvidenceItemRepository(config).delete(evidence_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Evidence item not found.")
    return None
