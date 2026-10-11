import copy
import json
from pathlib import Path

from traceability_audit.audit_log import AuditLog
from traceability_audit.public_api import run_traceability
from traceability_audit.trace_graph import build_graph
from traceability_audit.validator import validate
from traceability_audit import views

S = Path(__file__).parent.parent / "samples"
STATE = json.loads((S / "demo_state_update.json").read_text())
R = json.loads((S / "demo_requirements.json").read_text())
P = "demo-project"


def codes(report):
    return {(f["code"], f["node_id"]) for f in report["findings"]}


def make(state=None, reqs=None, tests=None):
    state = state or copy.deepcopy(STATE)
    reqs = R["requirements"] if reqs is None else reqs
    tests = R["tests"] if tests is None else tests
    g = build_graph(state, reqs, tests)
    return g, validate(g, state)


def test_clean_sample_passes_with_only_unused_warning():
    _, rep = make()
    assert rep["ok"] and rep["errors"] == 0
    assert codes(rep) == {("EVIDENCE_UNUSED", f"{P}-EVD-030")}


def test_node_counts():
    g, rep = make()
    assert rep["node_counts"]["requirement"] == 4 and rep["node_counts"]["evidence"] == 6


def test_full_chain_requirement_to_evidence():
    g, _ = make()
    assert g.evidence_for(f"{P}-REQ-006") == {f"{P}-EVD-010"}


def test_impact_analysis_finds_everything_built_on_evidence():
    g, _ = make()
    down = g.downstream(f"{P}-EVD-010")
    assert {f"{P}-BR-006", f"{P}-REQ-006", "test_deadline_enforced", f"{P}-ISS-002"} <= down


def test_dangling_reference_is_error():
    s = copy.deepcopy(STATE)
    s["candidate_business_rules"][0]["evidence_ids"] = [f"{P}-EVD-999"]
    _, rep = make(s)
    assert not rep["ok"]
    assert ("DANGLING_REFERENCE", f"{P}-BR-001") in codes(rep)
    assert ("RULE_NO_EVIDENCE", f"{P}-BR-001") in codes(rep)


def test_requirement_without_evidence_is_error():
    reqs = [{"requirement_id": f"{P}-REQ-100", "statement": "x"}]
    _, rep = make(reqs=reqs, tests=[])
    assert ("REQUIREMENT_NO_EVIDENCE", f"{P}-REQ-100") in codes(rep)


def test_requirement_evidence_via_rule_chain_counts():
    reqs = [{"requirement_id": f"{P}-REQ-100", "statement": "x", "related_rule_ids": [f"{P}-BR-001"]}]
    _, rep = make(reqs=reqs, tests=[])
    assert ("REQUIREMENT_NO_EVIDENCE", f"{P}-REQ-100") not in codes(rep)


def test_missing_source_link_warns_and_tests_optional():
    reqs = [{"requirement_id": f"{P}-REQ-100", "statement": "x", "evidence_ids": [f"{P}-EVD-001"]}]
    g = build_graph(STATE, reqs, [])
    rep = validate(g, STATE, require_tests=True)
    c = codes(rep)
    assert ("REQUIREMENT_NO_SOURCE_STEP_OR_RULE", f"{P}-REQ-100") in c
    assert ("REQUIREMENT_NO_TEST", f"{P}-REQ-100") in c
    assert ("REQUIREMENT_NO_TEST", f"{P}-REQ-100") not in codes(validate(g, STATE))


def test_unanswered_question_warns():
    s = copy.deepcopy(STATE)
    s["human_answers"] = s["human_answers"][:1]
    _, rep = make(s)
    assert ("QUESTION_UNANSWERED", f"{P}-Q-002") in codes(rep)


def test_approved_without_decision_or_with_open_questions_is_error():
    s = copy.deepcopy(STATE)
    s["decisions"] = []
    _, rep = make(s)
    assert ("APPROVED_WITHOUT_DECISION", "-") in codes(rep)
    s = copy.deepcopy(STATE)
    s["pending_question_ids"] = [f"{P}-Q-002"]
    _, rep = make(s)
    assert ("APPROVED_WITH_OPEN_QUESTIONS", "-") in codes(rep)


def test_empty_input_is_safe():
    g = build_graph({})
    rep = validate(g, {})
    assert rep["ok"] and rep["findings"] == []


def test_inputs_not_modified():
    s = copy.deepcopy(STATE)
    run_traceability(s, R["requirements"], R["tests"])
    assert s == STATE


def test_matrix_marks_missing_evidence():
    reqs = [{"requirement_id": f"{P}-REQ-100", "statement": "a | b"}]
    g = build_graph(STATE, reqs, [])
    md = views.traceability_matrix(g)
    assert "**NONE**" in md and "a / b" in md and "DRAFT" in md


def test_impact_report_unknown_id():
    g, _ = make()
    assert "Unknown id" in views.impact_report(g, "nope")


def test_audit_chain_valid_then_detects_tampering():
    log = AuditLog(P)
    log.record("run_started", "system", "workflow")
    log.record("note", "Dr. Rao", "x", {"a": 1})
    assert log.verify()["ok"]
    log.events[0]["actor"] = "someone else"
    v = log.verify()
    assert not v["ok"] and v["broken_at"] == 0


def test_audit_detects_deleted_event():
    log = AuditLog(P)
    for i in range(3):
        log.record("e", "a", str(i))
    del log.events[1]
    assert not log.verify()["ok"]


def test_audit_requires_actor_and_type():
    log = AuditLog(P)
    for args in (("", "a"), ("e", "")):
        try:
            log.record(*args)
            assert False
        except ValueError:
            pass


def test_import_hitl_idempotent_and_ordered():
    log = AuditLog(P)
    n = log.import_hitl(STATE)
    assert n == 5                       # 2 questions + 2 answers + 1 decision
    assert log.import_hitl(STATE) == 0
    assert log.verify()["ok"]
    assert [e["event_id"] for e in log.events][0].endswith("EVT-0001")


def test_save_load_roundtrip(tmp_path):
    log = AuditLog(P)
    log.import_hitl(STATE)
    log.save(tmp_path / "a.json")
    again = AuditLog.load(tmp_path / "a.json")
    assert again.events == log.events and again.verify()["ok"]


def test_run_traceability_returns_documents_and_history():
    log = AuditLog(P)
    out = run_traceability(STATE, R["requirements"], R["tests"], audit=log)
    assert set(out["documents"]) == {"TRACEABILITY_MATRIX.md", "VALIDATION_REPORT.md", "WORKFLOW_HISTORY.md"}
    assert out["audit_verify"]["ok"]
    assert "decision_recorded" in out["documents"]["WORKFLOW_HISTORY.md"]
