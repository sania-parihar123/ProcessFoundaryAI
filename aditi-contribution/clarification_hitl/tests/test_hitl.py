import json
from pathlib import Path

import pytest

from clarification_hitl.question_builder import build_questions
from clarification_hitl.store import ClarificationStore, HitlError

SAMPLE = Path(__file__).parent.parent / "samples" / "demo_state_update.json"


@pytest.fixture
def update():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


@pytest.fixture
def store(update):
    s = ClarificationStore(update["project_id"])
    s.load_from_state(update)
    return s


def test_builder_finds_expected_questions(update):
    kinds = [q.kind for q in build_questions(update)]
    assert kinds.count("missing_actor") == 3
    assert kinds.count("conflicting_rules") == 1
    assert kinds.count("ambiguous_term") == 1


def test_conflict_kept_with_both_options(store):
    q = next(q for q in store.questions.values() if q.kind == "conflicting_rules")
    assert "31 March" in q.options and "15 April" in q.options
    assert len(q.rule_ids) == 2


def test_ids_prefixed_and_unique(store):
    ids = list(store.questions)
    assert len(ids) == len(set(ids))
    assert all(i.startswith("demo-project-Q-") for i in ids)


def test_add_twice_no_duplicates(store, update):
    assert store.load_from_state(update) == []
    assert len(store.questions) == 5


def test_empty_update_gives_no_questions():
    assert build_questions({"project_id": "p"}) == []


def test_answer_requires_name_role_text(store):
    qid = store.pending_question_ids()[0]
    with pytest.raises(HitlError):
        store.record_answer(qid, "  ", "A", "r")
    with pytest.raises(HitlError):
        store.record_answer(qid, "Clerk", "", "r")
    with pytest.raises(HitlError):
        store.record_answer(qid, "Clerk", "A", "")
    with pytest.raises(HitlError):
        store.record_answer("nope", "Clerk", "A", "r")


def test_answer_idempotent_and_supersede(store):
    qid = store.pending_question_ids()[0]
    a1 = store.record_answer(qid, "Clerk", "A", "owner")
    assert store.record_answer(qid, "Clerk", "A", "owner") is a1
    assert len(store.answers) == 1
    a2 = store.record_answer(qid, "HOD", "A", "owner")
    assert a1.superseded and not a2.superseded
    assert store.current_answer(qid) is a2
    assert len(store.answers) == 2          # history kept


def test_option_questions_reject_invalid_choice(store):
    q = next(q for q in store.questions.values() if q.options)
    with pytest.raises(HitlError):
        store.record_answer(q.question_id, "1 January", "A", "owner")
    store.record_answer(q.question_id, "31 March", "A", "owner")


def test_cannot_approve_with_open_questions(store):
    with pytest.raises(HitlError):
        store.record_decision("requirements", "approve", "Dr", "approver")
    assert store.approval_status() == "pending"


def test_role_check_and_reason_required(store):
    for qid in list(store.pending_question_ids()):
        q = store.questions[qid]
        store.record_answer(qid, q.options[0] if q.options else "x", "A", "owner")
    with pytest.raises(HitlError):
        store.record_decision("requirements", "approve", "Bob", "student")
    with pytest.raises(HitlError):
        store.record_decision("requirements", "reject", "Dr", "approver", "")
    store.record_decision("requirements", "reject", "Dr", "approver", "Missing rules")
    assert store.approval_status() == "rejected"


def test_approval_only_after_human_decision(store):
    for qid in list(store.pending_question_ids()):
        q = store.questions[qid]
        store.record_answer(qid, q.options[0] if q.options else "x", "A", "owner")
    assert store.is_ready_to_resume()
    assert store.approval_status() == "pending"      # answers alone never approve
    store.record_decision("requirements", "approve", "Dr", "approver")
    assert store.approval_status() == "approved"


def test_stale_reopens_and_cancels_approval(store):
    for qid in list(store.pending_question_ids()):
        q = store.questions[qid]
        store.record_answer(qid, q.options[0] if q.options else "x", "A", "owner")
    store.record_decision("requirements", "approve", "Dr", "approver")
    first = next(iter(store.questions))
    store.mark_stale([first])
    assert store.approval_status() == "pending"
    assert first in store.pending_question_ids()
    store.record_answer(first, "New answer", "A", "owner")
    assert store.is_ready_to_resume()


def test_state_update_keys_and_status(store):
    out = store.to_state_update()
    assert out["lifecycle_status"] == "paused_for_human"
    assert out["approval_status"] == "pending"
    assert len(out["pending_question_ids"]) == 5
    assert set(out) == {"clarification_questions", "human_answers", "decisions",
                        "pending_question_ids", "approval_status", "lifecycle_status"}
    json.dumps(out)       # must be JSON-serialisable


def test_save_and_load_roundtrip(store, tmp_path):
    qid = store.pending_question_ids()[0]
    store.record_answer(qid, "Clerk", "A", "owner")
    store.save(tmp_path / "s.json")
    s2 = ClarificationStore.load(tmp_path / "s.json")
    assert s2.to_state_update() == store.to_state_update()
