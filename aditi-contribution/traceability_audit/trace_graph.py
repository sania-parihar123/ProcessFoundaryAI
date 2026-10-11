"""Builds a trace graph from plain dicts. No LLM, no imports from other modules.

Inputs (all optional except project_id handling):
  state_update  : dict with evidence_items, as_is_process{steps}, candidate_business_rules,
                  gap_issues, conflict_issues, clarification_questions, human_answers, decisions
  requirements  : list of dicts (id + evidence ids + related step/rule ids)
  tests         : optional list of {"test_id", "requirement_ids"} (e.g. test names -> requirement)
Field names are read tolerantly (several spellings) because the shared schema is still being agreed.
"""
from typing import Any, Dict, Iterable, List, Set, Tuple


def _first(d: Dict[str, Any], *names, default=None):
    for n in names:
        if d.get(n) not in (None, "", []):
            return d[n]
    return default


def _ids(d: Dict[str, Any], *names) -> List[str]:
    v = _first(d, *names, default=[])
    if isinstance(v, str):
        v = [v]
    return [str(x) for x in v]


def node_id(rec: Dict[str, Any], *names) -> str:
    return str(_first(rec, *names, default=""))


class TraceGraph:
    """Nodes: id -> {type, label}.  Edges: (from_id, relation, to_id). Direction: derived -> source."""

    def __init__(self):
        self.nodes: Dict[str, Dict[str, str]] = {}
        self.edges: List[Tuple[str, str, str]] = []
        self.dangling: List[Tuple[str, str, str]] = []   # edges pointing at ids that do not exist

    def add_node(self, nid: str, ntype: str, label: str = "") -> None:
        if nid:
            self.nodes[nid] = {"type": ntype, "label": label}

    def add_edge(self, src: str, rel: str, dst: str) -> None:
        if src and dst and (src, rel, dst) not in self.edges:
            self.edges.append((src, rel, dst))

    def finish(self) -> None:
        self.dangling = [e for e in self.edges if e[2] not in self.nodes or e[0] not in self.nodes]
        self.edges = [e for e in self.edges if e not in self.dangling]

    def out(self, nid: str) -> List[Tuple[str, str]]:
        return [(r, d) for s, r, d in self.edges if s == nid]

    def incoming(self, nid: str) -> List[Tuple[str, str]]:
        return [(r, s) for s, r, d in self.edges if d == nid]

    def of_type(self, ntype: str) -> List[str]:
        return [n for n, v in self.nodes.items() if v["type"] == ntype]

    def evidence_for(self, nid: str) -> Set[str]:
        """All evidence reachable by following edges from this node (full chain back to the source)."""
        seen, stack, found = set(), [nid], set()
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            if self.nodes.get(cur, {}).get("type") == "evidence":
                found.add(cur)
            stack.extend(d for _, d in self.out(cur))
        return found

    def downstream(self, nid: str) -> Set[str]:
        """Everything built on top of this node (impact analysis): what is affected if it changes."""
        seen, stack = set(), [nid]
        while stack:
            cur = stack.pop()
            for _, s in self.incoming(cur):
                if s not in seen:
                    seen.add(s)
                    stack.append(s)
        return seen


def build_graph(state_update: Dict[str, Any], requirements: Iterable[Dict[str, Any]] = (),
                tests: Iterable[Dict[str, Any]] = ()) -> TraceGraph:
    g = TraceGraph()

    for e in state_update.get("evidence_items") or []:
        g.add_node(node_id(e, "evidence_id", "id"), "evidence", str(_first(e, "claim", "text", default="")))

    steps = (state_update.get("as_is_process") or {}).get("steps", [])
    for s in steps:
        sid = node_id(s, "step_id", "id")
        g.add_node(sid, "step", str(_first(s, "name", "title", default="")))
        for ev in _ids(s, "evidence_ids"):
            g.add_edge(sid, "supported_by", ev)

    for r in state_update.get("candidate_business_rules") or []:
        rid = node_id(r, "rule_id", "id")
        g.add_node(rid, "rule", str(_first(r, "statement", "description", default="")))
        for ev in _ids(r, "evidence_ids"):
            g.add_edge(rid, "supported_by", ev)

    for key, ntype in (("gap_issues", "issue"), ("conflict_issues", "issue")):
        for i in state_update.get(key) or []:
            iid = node_id(i, "issue_id", "id")
            g.add_node(iid, ntype, str(_first(i, "description", "title", default="")))
            for ev in _ids(i, "evidence_ids"):
                g.add_edge(iid, "raised_from", ev)
            for rid in _ids(i, "rule_ids"):
                g.add_edge(iid, "concerns", rid)
            for sid in _ids(i, "step_ids"):
                g.add_edge(iid, "concerns", sid)

    for q in state_update.get("clarification_questions") or []:
        qid = node_id(q, "question_id", "id")
        g.add_node(qid, "question", str(_first(q, "text", default="")))
        for ev in _ids(q, "evidence_ids"):
            g.add_edge(qid, "raised_from", ev)
        for sid in _ids(q, "step_ids"):
            g.add_edge(qid, "concerns", sid)
        for rid in _ids(q, "rule_ids"):
            g.add_edge(qid, "concerns", rid)

    for a in state_update.get("human_answers") or []:
        aid = node_id(a, "answer_id", "id")
        g.add_node(aid, "answer", str(_first(a, "answer_text", default="")))
        g.add_edge(aid, "answers", str(a.get("question_id", "")))

    for rq in requirements:
        rqid = node_id(rq, "requirement_id", "id", "req_id")
        g.add_node(rqid, "requirement", str(_first(rq, "statement", "text", "description", default="")))
        for ev in _ids(rq, "evidence_ids"):
            g.add_edge(rqid, "supported_by", ev)
        for sid in _ids(rq, "step_ids", "related_step_ids", "source_step_ids"):
            g.add_edge(rqid, "derived_from", sid)
        for rid in _ids(rq, "rule_ids", "related_rule_ids", "source_rule_ids"):
            g.add_edge(rqid, "derived_from", rid)

    for t in tests:
        tid = node_id(t, "test_id", "id")
        g.add_node(tid, "test", str(_first(t, "name", default=tid)))
        for rqid in _ids(t, "requirement_ids"):
            g.add_edge(tid, "verifies", rqid)

    for d in state_update.get("decisions") or []:
        did = node_id(d, "decision_id", "id")
        g.add_node(did, "decision", f"{d.get('decision', '')} by {d.get('decided_by', '')}")

    g.finish()
    return g
