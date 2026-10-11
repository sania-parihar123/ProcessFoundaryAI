"""Markdown views: traceability matrix, impact report, workflow history, validation report."""
from typing import Any, Dict, List

from .trace_graph import TraceGraph

BANNER = "> DRAFT - generated from linked records. Not approved.\n"


def _cell(text: str, n: int = 70) -> str:
    text = " ".join(str(text).split()).replace("|", "/")
    return text if len(text) <= n else text[: n - 1] + "…"


def traceability_matrix(g: TraceGraph) -> str:
    lines = ["# Traceability matrix", BANNER, "| Requirement | Statement | Steps / rules | Evidence | Tests |", "|---|---|---|---|---|"]
    for rq in sorted(g.of_type("requirement")):
        src = ", ".join(d for r, d in g.out(rq) if r == "derived_from") or "-"
        ev = ", ".join(sorted(g.evidence_for(rq))) or "**NONE**"
        tests = ", ".join(s for r, s in g.incoming(rq) if r == "verifies") or "-"
        lines.append(f"| {rq} | {_cell(g.nodes[rq]['label'])} | {src} | {ev} | {tests} |")
    return "\n".join(lines) + "\n"


def impact_report(g: TraceGraph, evidence_id: str) -> str:
    if evidence_id not in g.nodes:
        return f"Unknown id: {evidence_id}\n"
    down = sorted(g.downstream(evidence_id))
    lines = [f"# Impact of {evidence_id}", BANNER, f"Source: {_cell(g.nodes[evidence_id]['label'], 120)}", "",
             "If this evidence changes, review:"]
    lines += [f"- {n} ({g.nodes[n]['type']}): {_cell(g.nodes[n]['label'])}" for n in down] or ["- nothing depends on it"]
    return "\n".join(lines) + "\n"


def workflow_history(events: List[Dict[str, Any]]) -> str:
    lines = ["# Workflow history", BANNER, "| Time | Event | By | Subject | Details |", "|---|---|---|---|---|"]
    for e in events:
        details = ", ".join(f"{k}={v}" for k, v in (e.get("details") or {}).items())
        lines.append(f"| {e['timestamp']} | {e['event_type']} | {e['actor']} | {e['subject']} | {_cell(details, 80)} |")
    return "\n".join(lines) + "\n"


def validation_report(report: Dict[str, Any]) -> str:
    lines = ["# Validation report", BANNER, f"Result: **{'PASS' if report['ok'] else 'FAIL'}** - {report['errors']} errors, {report['warnings']} warnings", "",
             "Nodes: " + ", ".join(f"{k}={v}" for k, v in report["node_counts"].items()), ""]
    lines += [f"- [{f['severity'].upper()}] {f['code']} {f['node_id']}: {f['message']}" for f in report["findings"]] or ["No problems found."]
    return "\n".join(lines) + "\n"
