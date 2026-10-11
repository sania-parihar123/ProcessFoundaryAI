"""Application boundary from uploaded documents to the analysis graph."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Sequence
from uuid import uuid4

from app.graph.build_graph import build_graph
from app.graph.state import ProcessFoundryState

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

    @property
    def message(self) -> str:
        if not self.documents:
            return "No documents were successfully extracted."
        if not self.sections:
            return "Documents were accepted, but no extractable text was found."
        if not self.evidence_items:
            return "Text was extracted, but no recognized scholarship evidence was found."
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
    """Build a reviewable proposal strictly from extracted evidence and issues."""

    steps: list[dict[str, Any]] = []
    roles: list[str] = []
    inputs: list[dict[str, Any]] = []
    decision_points: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    source_refs: set[str] = set()

    for item in evidence_items:
        assertion = item.get("assertion", {})
        predicate = assertion.get("predicate")
        refs = list(item.get("source_refs", []))
        evidence_id = item["evidence_id"]
        quote = str(item.get("quote", "")).strip()
        source_refs.update(refs)
        if predicate == "enrollment_requirement":
            steps.append(
                {
                    "step": "Verify the applicant's enrollment.",
                    "description": (
                        f"Confirm that the applicant meets the stated enrollment "
                        f"requirement: {quote}"
                    ),
                    "supported_by": [evidence_id],
                    "source_refs": refs,
                    "requirement": assertion.get("value"),
                }
            )
        elif predicate == "academic_threshold":
            description = (
                f"Check the academic threshold stated in the source: {quote}"
            )
            decision_points.append(
                {
                    "check": "Academic eligibility",
                    "description": description,
                    "evidence_refs": [evidence_id],
                    "source_refs": refs,
                }
            )
            steps.append(
                {
                    "step": "Check academic eligibility.",
                    "description": description,
                    "supported_by": [evidence_id],
                    "source_refs": refs,
                }
            )
        elif predicate == "family_income_limit":
            description = (
                f"Check the family or household income limit stated in the source: "
                f"{quote}"
            )
            decision_points.append(
                {
                    "check": "Family or household income eligibility",
                    "description": description,
                    "claim": str(assertion.get("value", "")),
                    "evidence_refs": [evidence_id],
                    "source_refs": refs,
                }
            )
            steps.append(
                {
                    "step": "Check family or household income eligibility.",
                    "description": description,
                    "supported_by": [evidence_id],
                    "source_refs": refs,
                }
            )
        elif predicate == "required_supporting_document":
            inputs.append(
                {
                    "document": assertion.get("value"),
                    "description": f"Verify the required document: {quote}",
                    "evidence_refs": [evidence_id],
                    "source_refs": refs,
                }
            )
            steps.append(
                {
                    "step": "Collect and verify supporting documents.",
                    "description": f"Verify the required document: {quote}",
                    "supported_by": [evidence_id],
                    "source_refs": refs,
                }
            )
        elif predicate == "human_review_responsibility":
            role = str(assertion.get("value", "")).strip()
            if role and role not in roles:
                roles.append(role)
            steps.append(
                {
                    "step": "Conduct human review or final decision.",
                    "description": f"Follow the responsibility stated in the source: {quote}",
                    "supported_by": [evidence_id],
                    "source_refs": refs,
                    "responsible_role": role,
                }
            )
        if assertion.get("exception"):
            exceptions.append(
                {
                    "description": assertion["exception"],
                    "evidence_refs": [evidence_id],
                    "source_refs": refs,
                }
            )

    unresolved_questions = [
        {
            "issue_id": issue.get("gap_id", issue.get("conflict_id")),
            "description": issue.get("description", ""),
            "evidence_refs": list(issue.get("evidence_refs", [])),
            "source_refs": list(issue.get("source_refs", [])),
        }
        for issue in [*state.gap_issues, *state.conflict_issues]
        if isinstance(issue, dict) and issue.get("status") != "resolved_by_human"
    ]
    conflicts = [
        {
            "conflict_id": issue.get("conflict_id"),
            "description": issue.get("description", ""),
            "competing_assertions": issue.get("competing_assertions", []),
            "evidence_refs": issue.get("evidence_refs", []),
            "source_refs": issue.get("source_refs", []),
        }
        for issue in state.conflict_issues
        if isinstance(issue, dict) and issue.get("status") != "resolved_by_human"
    ]
    explanation = (
        "Workflow steps are supported by extracted evidence and remain subject to review."
        if steps or decision_points or inputs
        else "A workflow cannot yet be reliably proposed because no supported process requirements were extracted."
    )
    return {
        "proposal_id": _proposal_id(evidence_items, state),
        "status": "draft",
        "steps": steps,
        "requirements": [
            {
                "description": str(item.get("quote", "")).strip(),
                "evidence_refs": [item["evidence_id"]],
                "source_refs": list(item.get("source_refs", [])),
            }
            for item in evidence_items
        ],
        "roles": roles,
        "required_inputs": inputs,
        "decision_points": decision_points,
        "exceptions": exceptions,
        "unresolved_questions": unresolved_questions,
        "conflicts": conflicts,
        "source_refs": sorted(source_refs),
        "explanation": explanation,
    }


def ingest_documents(
    uploads: Sequence[Any],
    *,
    project_id: str = "uploaded-project",
    process_type: str = "scholarship",
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
    evidence_items = extract_evidence(sections)
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
    )
