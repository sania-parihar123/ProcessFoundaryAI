from decimal import Decimal

from member2 import public_api
from member2.schemas import DiscoveredStep, EvidenceRecord, RuleRecord


def test_extract_evidence_uses_continuing_counter(monkeypatch):
    calls = []

    def fake_extract(section, project_id, counter_start=1):
        calls.append((section["id"], project_id, counter_start))
        if section["id"] == "SEC-001":
            return [
                EvidenceRecord(
                    id=f"{project_id}-EVD-{counter_start:03d}",
                    project_id=project_id,
                    document_section_id=section["id"],
                    quote="First quote",
                    claim_type="step",
                    confidence=Decimal("0.90"),
                ),
                EvidenceRecord(
                    id=f"{project_id}-EVD-{counter_start + 1:03d}",
                    project_id=project_id,
                    document_section_id=section["id"],
                    quote="Second quote",
                    claim_type="step",
                    confidence=Decimal("0.90"),
                ),
            ]
        return [
            EvidenceRecord(
                id=f"{project_id}-EVD-{counter_start:03d}",
                project_id=project_id,
                document_section_id=section["id"],
                quote="Third quote",
                claim_type="rule",
                confidence=Decimal("0.60"),
            )
        ]

    monkeypatch.setattr(public_api.evidence_node, "extract_evidence", fake_extract)

    document_sections = [{"id": "SEC-001", "text": "alpha"}, {"id": "SEC-002", "text": "beta"}]
    items = public_api.extract_evidence(document_sections, "demo-project")

    assert [item.id for item in items] == ["demo-project-EVD-001", "demo-project-EVD-002", "demo-project-EVD-003"]
    assert calls == [("SEC-001", "demo-project", 1), ("SEC-002", "demo-project", 3)]


def test_build_as_is_calls_wrapper(monkeypatch):
    evidence = [
        EvidenceRecord(
            id="demo-project-EVD-001",
            project_id="demo-project",
            document_section_id="SEC-001",
            quote="The clerk checks the form.",
            claim_type="step",
            confidence=Decimal("0.90"),
        )
    ]
    expected = [
        DiscoveredStep(
            step_id="demo-project-STEP-001",
            name="Check form",
            actor="clerk",
            inputs=[],
            outputs=[],
            next_steps=[],
            evidence_ids=["demo-project-EVD-001"],
        )
    ]

    monkeypatch.setattr(public_api.as_is_node, "build_as_is", lambda items, project_id: expected)

    result = public_api.build_as_is(evidence, "demo-project")

    assert result == expected


def test_extract_business_rules_calls_wrapper(monkeypatch):
    evidence = [
        EvidenceRecord(
            id="demo-project-EVD-001",
            project_id="demo-project",
            document_section_id="SEC-001",
            quote="Applications must be filed by Friday.",
            claim_type="rule",
            confidence=Decimal("0.90"),
        )
    ]
    expected = [
        RuleRecord(
            rule_id="demo-project-BR-001",
            statement="Applications must be filed by Friday.",
            condition=None,
            action=None,
            scope=None,
            effective_context=None,
            evidence_ids=["demo-project-EVD-001"],
            status="needs_review",
        )
    ]

    monkeypatch.setattr(public_api.rules_node, "extract_rules", lambda items, project_id: expected)

    result = public_api.extract_business_rules(evidence, None, "demo-project")

    assert result == expected
