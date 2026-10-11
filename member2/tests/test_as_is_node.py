from member2 import as_is_node
from member2.schemas import EvidenceRecord


def _evidence(evidence_id: str = "demo-project-EVD-001", quote: str = "The clerk checks the form.") -> EvidenceRecord:
    return EvidenceRecord(
        id=evidence_id,
        project_id="demo-project",
        document_section_id="DOC-DEMO-S001",
        quote=quote,
        claim_type="step",
        confidence="0.90",
    )


def _raw_steps(*steps: dict) -> as_is_node.RawStepList:
    return as_is_node.RawStepList(
        steps=[as_is_node.RawStep(**step) for step in steps]
    )


def test_valid_steps_get_project_ids_and_ordered_links(monkeypatch):
    evidence = [
        _evidence("demo-project-EVD-001", "The clerk checks the form."),
        _evidence("demo-project-EVD-002", "The manager approves the record."),
    ]
    monkeypatch.setattr(
        as_is_node,
        "call_llm",
        lambda **kwargs: _raw_steps(
            {
                "name": "Check form",
                "actor": "clerk",
                "inputs": ["form"],
                "outputs": ["checked form"],
                "evidence_ids": ["demo-project-EVD-001"],
            },
            {
                "name": "Approve record",
                "actor": "manager",
                "inputs": ["checked form"],
                "outputs": ["approved record"],
                "evidence_ids": ["demo-project-EVD-002"],
            },
        ),
    )

    steps = as_is_node.build_as_is(evidence, "demo-project")

    assert [step.step_id for step in steps] == [
        "demo-project-STEP-001",
        "demo-project-STEP-002",
    ]
    assert [step.next_steps[0].to_step_id for step in steps[:1]] == [
        "demo-project-STEP-002"
    ]
    assert steps[-1].next_steps == []


def test_unknown_evidence_id_is_removed(monkeypatch, capsys):
    monkeypatch.setattr(
        as_is_node,
        "call_llm",
        lambda **kwargs: _raw_steps(
            {
                "name": "Check form",
                "actor": "clerk",
                "inputs": [],
                "outputs": [],
                "evidence_ids": ["demo-project-EVD-001", "unknown-EVD"],
            }
        ),
    )

    steps = as_is_node.build_as_is([_evidence()], "demo-project")

    assert len(steps) == 1
    assert steps[0].evidence_ids == ["demo-project-EVD-001"]
    assert "removed unknown evidence ID" in capsys.readouterr().out


def test_step_with_only_unknown_evidence_ids_is_rejected(monkeypatch, capsys):
    monkeypatch.setattr(
        as_is_node,
        "call_llm",
        lambda **kwargs: _raw_steps(
            {
                "name": "Unsupported step",
                "actor": None,
                "inputs": [],
                "outputs": [],
                "evidence_ids": ["unknown-EVD"],
            }
        ),
    )

    steps = as_is_node.build_as_is([_evidence()], "demo-project")

    assert steps == []
    assert "Rejected step" in capsys.readouterr().out


def test_null_actor_stays_none(monkeypatch):
    monkeypatch.setattr(
        as_is_node,
        "call_llm",
        lambda **kwargs: _raw_steps(
            {
                "name": "Check form",
                "actor": None,
                "inputs": [],
                "outputs": [],
                "evidence_ids": ["demo-project-EVD-001"],
            }
        ),
    )

    steps = as_is_node.build_as_is([_evidence()], "demo-project")

    assert steps[0].actor is None
    assert steps[0].unknowns == ["actor not stated in source"]


def test_actor_is_not_marked_unknown(monkeypatch):
    monkeypatch.setattr(
        as_is_node,
        "call_llm",
        lambda **kwargs: _raw_steps(
            {
                "name": "Check form",
                "actor": "clerk",
                "inputs": [],
                "outputs": [],
                "evidence_ids": ["demo-project-EVD-001"],
            }
        ),
    )

    steps = as_is_node.build_as_is([_evidence()], "demo-project")

    assert steps[0].actor == "clerk"
    assert steps[0].unknowns == []


def test_none_result_returns_empty_list_and_warns(monkeypatch, capsys):
    monkeypatch.setattr(as_is_node, "call_llm", lambda **kwargs: None)

    steps = as_is_node.build_as_is([_evidence()], "demo-project")

    assert steps == []
    assert "Warning" in capsys.readouterr().out


def test_actor_not_supported_by_quotes_is_cleared(monkeypatch, capsys):
    monkeypatch.setattr(
        as_is_node,
        "call_llm",
        lambda **kwargs: _raw_steps(
            {
                "name": "Check form",
                "actor": "committee",
                "inputs": [],
                "outputs": [],
                "evidence_ids": ["demo-project-EVD-001"],
            }
        ),
    )

    steps = as_is_node.build_as_is([_evidence()], "demo-project")

    assert steps[0].actor is None
    assert "removed unsupported actor" in capsys.readouterr().out


def test_leading_the_is_removed_from_actor_names(monkeypatch):
    evidence = [
        _evidence("demo-project-EVD-001", "The student submits the form."),
        _evidence("demo-project-EVD-002", "The Head of Department (HOD) reviews the form."),
    ]
    monkeypatch.setattr(
        as_is_node,
        "call_llm",
        lambda **kwargs: _raw_steps(
            {
                "name": "Submit form",
                "actor": "The student",
                "inputs": [],
                "outputs": [],
                "evidence_ids": ["demo-project-EVD-001"],
            },
            {
                "name": "Review form",
                "actor": "The Head of Department (HOD)",
                "inputs": [],
                "outputs": [],
                "evidence_ids": ["demo-project-EVD-002"],
            },
        ),
    )

    steps = as_is_node.build_as_is(evidence, "demo-project")

    assert [step.actor for step in steps] == ["student", "Head of Department (HOD)"]


def test_evidence_id_is_removed_from_inputs_but_real_input_is_kept(monkeypatch):
    monkeypatch.setattr(
        as_is_node,
        "call_llm",
        lambda **kwargs: _raw_steps(
            {
                "name": "Review application",
                "actor": None,
                "inputs": ["demo-project-EVD-001", "application form"],
                "outputs": [],
                "evidence_ids": ["demo-project-EVD-001"],
            }
        ),
    )

    steps = as_is_node.build_as_is([_evidence()], "demo-project")

    assert steps[0].inputs == ["application form"]
