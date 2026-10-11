"""One-call entry point for the workflow."""
from typing import Any, Dict, Iterable, Optional

from .audit_log import AuditLog
from .trace_graph import build_graph
from .validator import validate
from . import views


def run_traceability(state_update: Dict[str, Any], requirements: Iterable[Dict[str, Any]] = (),
                     tests: Iterable[Dict[str, Any]] = (), audit: Optional[AuditLog] = None,
                     require_tests: bool = False) -> Dict[str, Any]:
    """Returns dict: report (validation), documents (markdown by name), audit_verify. Changes nothing in the inputs."""
    g = build_graph(state_update, requirements, tests)
    report = validate(g, state_update, require_tests)
    docs = {"TRACEABILITY_MATRIX.md": views.traceability_matrix(g), "VALIDATION_REPORT.md": views.validation_report(report)}
    result = {"report": report, "documents": docs, "graph": g}
    if audit is not None:
        audit.import_hitl(state_update)
        docs["WORKFLOW_HISTORY.md"] = views.workflow_history(audit.events)
        result["audit_verify"] = audit.verify()
    return result
