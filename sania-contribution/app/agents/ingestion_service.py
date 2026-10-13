"""Application boundary from uploaded documents to the analysis graph."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Sequence
from uuid import uuid4

from app.graph.build_graph import build_graph
from app.graph.state import ProcessFoundryState

from .generic_workflow_proposal import build_generic_workflow_proposal
from .scholarship_workflow_compatibility import (
    build_scholarship_workflow_proposal,
)
from .document_ingestion import (
    DEFAULT_MAX_FILE_SIZE_BYTES,
    DocumentIngestionError,
    ExtractedDocument,
    extract_document,
)
from .evidence_extraction import extract_evidence


@dataclass(frozen=True)
class UploadError:
    filename: str
    code: str
    message: str


@dataclass(frozen=True)
class IngestionResult:
    documents: list[dict[str, Any]]
    sections: list[dict[str, Any]]
    evidence_items: list[dict[str, Any]]
    errors: list[UploadError]
    state: ProcessFoundryState | None
    process_type: str = "generic-process"

    @property
    def message(self) -> str:
        if not self.documents:
            return "No documents were successfully extracted."
        if not self.sections:
            return "Documents were accepted, but no extractable text was found."
        if not self.evidence_items:
            if self.process_type == "scholarship":
                return "Text was extracted, but no recognized scholarship evidence was found."
            return "Text was extracted, but no recognized process evidence was found."
        return f"Extracted {len(self.evidence_items)} evidence item(s) from {len(self.documents)} document(s)."


def _proposal_id(evidence_items: list[dict[str, Any]], state: ProcessFoundryState) -> str:
    payload = {
        "evidence_ids": sorted(item["evidence_id"] for item in evidence_items),
        "gap_ids": sorted(
            issue.get("gap_id", "")
            for issue in state.gap_issues
            if isinstance(issue, dict)
        ),
        "conflict_ids": sorted(
            issue.get("conflict_id", "")
            for issue in state.conflict_issues
            if isinstance(issue, dict)
        ),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"proposal-{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _workflow_proposal(
    evidence_items: list[dict[str, Any]],
    state: ProcessFoundryState,
) -> dict[str, Any]:
    """Build a process-neutral proposal or a legacy scholarship projection."""

    proposal_id = _proposal_id(evidence_items, state)
    if state.process_type == "scholarship":
        return build_scholarship_workflow_proposal(
            evidence_items,
            state,
            proposal_id=proposal_id,
        )
    return build_generic_workflow_proposal(
        evidence_items,
        state,
        proposal_id=proposal_id,
    )


def ingest_documents(
    uploads: Sequence[Any],
    *,
    project_id: str = "uploaded-project",
    process_type: str = "generic-process",
    config: dict[str, Any] | None = None,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> IngestionResult:
    """Extract multiple uploads and run graph analysis only when input exists."""

    documents: list[ExtractedDocument] = []
    errors: list[UploadError] = []
    for upload in uploads:
        filename = getattr(upload, "name", "<unnamed upload>")
        try:
            documents.append(
                extract_document(
                    upload,
                    max_file_size_bytes=max_file_size_bytes,
                )
            )
        except DocumentIngestionError as exc:
            errors.append(UploadError(str(filename), exc.code, exc.message))

    sections = [section for document in documents for section in document.sections]
    extraction_config = dict(config or {})
    strategy = extraction_config.get("extraction_strategy")
    if strategy is None:
        strategy = (
            "scholarship_compat"
            if process_type == "scholarship"
            else "generic"
        )
    evidence_items = extract_evidence(
        sections,
        config=extraction_config,
        process_description=extraction_config.get("process_description"),
        vocabulary=extraction_config.get("vocabulary"),
        required_evidence=extraction_config.get("required_evidence"),
        expected_process_steps=extraction_config.get("expected_process_steps"),
        strategy=strategy,
    )
    state = None
    if documents:
        source_index = {
            document.document_id: document.metadata() for document in documents
        }
        initial_state = ProcessFoundryState(
            run_id=f"upload-run-{uuid4().hex[:12]}",
            project_id=project_id,
            process_type=process_type,
            source_document_ids=[document.document_id for document in documents],
            source_index=source_index,
            extracted_sections=sections,
            evidence_items=evidence_items,
            config=dict(config or {}),
        )
        state = build_graph().invoke(initial_state)
        state = ProcessFoundryState.model_validate(state)
        state.workflow_proposal = _workflow_proposal(evidence_items, state)
    return IngestionResult(
        documents=[document.metadata() for document in documents],
        sections=sections,
        evidence_items=evidence_items,
        errors=errors,
        state=state,
        process_type=process_type,
    )
