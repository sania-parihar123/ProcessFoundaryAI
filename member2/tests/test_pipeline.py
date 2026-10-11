from decimal import Decimal

from member2 import pipeline
from member2.schemas import DiscoveredStep, EvidenceRecord, RuleRecord


def _section(section_id: str = "DOC-DEMO-S001") -> dict:
    return {
        "id": section_id,
        "document_id": "DOC-DEMO",
        "page_number": None,
        "section_title": "Process",
        "text": "Applicants must submit the form.",
    }


def _evidence(section_id: str = "DOC-DEMO-S001") -> EvidenceRecord:
    return EvidenceRecord(
        id="demo-project-EVD-001",
        project_id="demo-project",
        document_section_id=section_id,
        quote="Applicants must submit the form.",
        claim_type="rule",
        confidence=Decimal("0.90"),
    )


def test_full_run_fills_all_four_output_lists(monkeypatch):
    section = _section()
    evidence = _evidence()
    step = DiscoveredStep(
        step_id="demo-project-STEP-001",
        name="Submit form",
        actor="Applicants",
        evidence_ids=[evidence.id],
    )
    rule = RuleRecord(
        rule_id="demo-project-BR-001",
        statement=evidence.quote,
        evidence_ids=[evidence.id],
    )
    monkeypatch.setattr(pipeline, "parse_document", lambda *args, **kwargs: [section])
    evidence_calls = []

    def fake_extract_evidence(section_arg, project_id, counter_start):
        evidence_calls.append((section_arg, project_id, counter_start))
        return [evidence]

    monkeypatch.setattr(pipeline, "extract_evidence", fake_extract_evidence)
    monkeypatch.setattr(pipeline, "build_as_is", lambda evidence, project_id: [step])
    monkeypatch.setattr(pipeline, "extract_rules", lambda evidence, project_id: [rule])

    result = pipeline.run_member2_pipeline(
        "document.txt",
        project_id="demo-project",
        document_id="DOC-DEMO",
    )

    assert result.document_id == "DOC-DEMO"
    assert len(result.sections) == len(result.evidence) == len(result.steps) == len(result.rules) == 1
    assert result.warnings == []
    assert evidence_calls == [(section, "demo-project", 1)]


def test_parse_error_returns_empty_lists_and_warning(monkeypatch):
    def raise_parse_error(*args, **kwargs):
        raise pipeline.ParseError("file is missing")

    monkeypatch.setattr(pipeline, "parse_document", raise_parse_error)

    result = pipeline.run_member2_pipeline(
        "missing.txt",
        project_id="demo-project",
        document_id="DOC-DEMO",
    )

    assert result.sections == []
    assert result.evidence == []
    assert result.steps == []
    assert result.rules == []
    assert any("file is missing" in warning for warning in result.warnings)


def test_empty_evidence_result_adds_warning(monkeypatch):
    monkeypatch.setattr(pipeline, "parse_document", lambda *args, **kwargs: [_section()])
    monkeypatch.setattr(pipeline, "extract_evidence", lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, "build_as_is", lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, "extract_rules", lambda *args, **kwargs: [])

    result = pipeline.run_member2_pipeline(
        "document.txt",
        project_id="demo-project",
        document_id="DOC-DEMO",
    )

    assert result.evidence == []
    assert any("Evidence extraction returned no evidence" in warning for warning in result.warnings)


def test_model_exceptions_are_reported_and_pipeline_returns(monkeypatch):
    monkeypatch.setattr(pipeline, "parse_document", lambda *args, **kwargs: [_section()])
    monkeypatch.setattr(
        pipeline,
        "extract_evidence",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("model unavailable")),
    )
    monkeypatch.setattr(pipeline, "build_as_is", lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, "extract_rules", lambda *args, **kwargs: [])

    result = pipeline.run_member2_pipeline("document.txt", project_id="demo-project")

    assert result.evidence == []
    assert any("model unavailable" in warning for warning in result.warnings)
