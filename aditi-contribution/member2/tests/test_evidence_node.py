from decimal import Decimal

from member2 import evidence_node
from member2.schemas import EvidenceRecord


def _section(text: str = "The clerk verifies the application.") -> dict:
    return {
        "id": "DOC-DEMO-S001",
        "document_id": "DOC-DEMO",
        "page_number": None,
        "section_title": "Procedure",
        "text": text,
    }


def _raw_evidence(*items: dict) -> evidence_node.RawEvidenceList:
    return evidence_node.RawEvidenceList(
        items=[evidence_node.RawEvidence(**item) for item in items]
    )


def test_real_quote_is_accepted(monkeypatch):
    monkeypatch.setattr(
        evidence_node,
        "call_llm",
        lambda **kwargs: _raw_evidence(
            {
                "quote": "The clerk verifies the application.",
                "claim_type": "step",
                "confidence_label": "high",
            }
        ),
    )

    records = evidence_node.extract_evidence(_section(), "demo-project")

    assert len(records) == 1
    assert records[0].quote == "The clerk verifies the application."
    assert isinstance(records[0], EvidenceRecord)


def test_fabricated_quote_is_rejected_and_reported(monkeypatch, capsys):
    monkeypatch.setattr(
        evidence_node,
        "call_llm",
        lambda **kwargs: _raw_evidence(
            {
                "quote": "The committee approves every application.",
                "claim_type": "rule",
                "confidence_label": "medium",
            }
        ),
    )

    records = evidence_node.extract_evidence(_section(), "demo-project")

    assert records == []
    assert "Rejected quote not found" in capsys.readouterr().out


def test_ids_use_project_and_count_from_counter_start(monkeypatch):
    monkeypatch.setattr(
        evidence_node,
        "call_llm",
        lambda **kwargs: _raw_evidence(
            {
                "quote": "The clerk verifies the application.",
                "claim_type": "step",
                "confidence_label": "high",
            },
            {
                "quote": "verifies the application",
                "claim_type": "actor",
                "confidence_label": "low",
            },
        ),
    )

    records = evidence_node.extract_evidence(_section(), "demo-project", counter_start=7)

    assert [record.id for record in records] == [
        "demo-project-EVD-007",
        "demo-project-EVD-008",
    ]
    assert all(record.project_id == "demo-project" for record in records)
    assert all(record.document_section_id == "DOC-DEMO-S001" for record in records)


def test_confidence_label_converts_to_decimal(monkeypatch):
    monkeypatch.setattr(
        evidence_node,
        "call_llm",
        lambda **kwargs: _raw_evidence(
            {
                "quote": "The clerk verifies the application.",
                "claim_type": "step",
                "confidence_label": "medium",
            }
        ),
    )

    records = evidence_node.extract_evidence(_section(), "demo-project")

    assert records[0].confidence == Decimal("0.60")
    assert isinstance(records[0].confidence, Decimal)


def test_none_result_returns_empty_list_and_warns(monkeypatch, capsys):
    monkeypatch.setattr(evidence_node, "call_llm", lambda **kwargs: None)

    records = evidence_node.extract_evidence(_section(), "demo-project")

    assert records == []
    assert "Warning" in capsys.readouterr().out


def test_heading_only_section_is_skipped_without_calling_llm(monkeypatch):
    def unexpected_call(**kwargs):
        raise AssertionError("LLM should not be called for a heading-only section")

    monkeypatch.setattr(evidence_node, "call_llm", unexpected_call)

    assert evidence_node.extract_evidence(_section(" \n\t "), "demo-project") == []
