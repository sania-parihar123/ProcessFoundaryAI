"""Validation report: finds broken or missing links. Pure checks, never changes data."""
from typing import Any, Dict, List

from .trace_graph import TraceGraph

SEVERITY = {"error": 0, "warning": 1}


def _f(severity: str, code: str, node: str, message: str) -> Dict[str, str]:
    return {"severity": severity, "code": code, "node_id": node, "message": message}


def validate(g: TraceGraph, state_update: Dict[str, Any] = None, require_tests: bool = False) -> Dict[str, Any]:
    state_update = state_update or {}
    findings: List[Dict[str, str]] = []

    for s, rel, d in g.dangling:
        findings.append(_f("error", "DANGLING_REFERENCE", s, f"{s} points to {d}, which does not exist."))

    for ntype, code in (("step", "STEP_NO_EVIDENCE"), ("rule", "RULE_NO_EVIDENCE"), ("requirement", "REQUIREMENT_NO_EVIDENCE")):
        for nid in g.of_type(ntype):
            if not g.evidence_for(nid):
                findings.append(_f("error", code, nid, f"{ntype} {nid} cannot be traced back to any evidence."))

    for nid in g.of_type("requirement"):
        if not any(r == "derived_from" for r, _ in g.out(nid)):
            findings.append(_f("warning", "REQUIREMENT_NO_SOURCE_STEP_OR_RULE", nid,
                               f"Requirement {nid} is not linked to a process step or rule."))
        if require_tests and not any(r == "verifies" for r, _ in g.incoming(nid)):
            findings.append(_f("warning", "REQUIREMENT_NO_TEST", nid, f"Requirement {nid} has no test."))

    for nid in g.of_type("evidence"):
        if not g.incoming(nid):
            findings.append(_f("warning", "EVIDENCE_UNUSED", nid, f"Evidence {nid} is not used by anything."))

    answered = {d for r, d in ((r, d) for s, r, d in g.edges if r == "answers")}
    for nid in g.of_type("question"):
        if nid not in answered:
            findings.append(_f("warning", "QUESTION_UNANSWERED", nid, f"Question {nid} has no answer yet."))

    if state_update.get("approval_status") == "approved":
        if not any(d.get("decision") == "approve" for d in state_update.get("decisions") or []):
            findings.append(_f("error", "APPROVED_WITHOUT_DECISION", "-", "Status is approved but no human approve decision is recorded."))
        if state_update.get("pending_question_ids"):
            findings.append(_f("error", "APPROVED_WITH_OPEN_QUESTIONS", "-", "Status is approved while questions are still pending."))

    findings.sort(key=lambda x: (SEVERITY[x["severity"]], x["code"], x["node_id"]))
    errors = sum(1 for x in findings if x["severity"] == "error")
    return {"ok": errors == 0, "errors": errors, "warnings": len(findings) - errors,
            "node_counts": {t: len(g.of_type(t)) for t in sorted({v["type"] for v in g.nodes.values()})},
            "findings": findings}
