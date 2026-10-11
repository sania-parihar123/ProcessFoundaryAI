import json
from decimal import Decimal

from member2.schemas import (
    DiscoveredStep,
    EvidenceRecord,
    MemberTwoOutput,
    RuleRecord,
    SourceSection,
)
from member2.state_adapter import to_state_update


def _output_with_records() -> MemberTwoOutput:
    return MemberTwoOutput(
        project_id="demo-project",
        document_id="DOC-DEMO",
        sections=[
            SourceSection(
                id="DOC-DEMO-S001",
                document_id="DOC-DEMO",
                section_title="Requirements",
                text="Applicants must submit a form.",
            )
        ],
        evidence=[
            EvidenceRecord(
                id="demo-project-EVD-001",
                project_id="demo-project",
                document_section_id="DOC-DEMO-S001",
                quote="Applicants must submit a form.",
                claim_type="rule",
                confidence=Decimal("0.90"),
            )
        ],
        steps=[
            DiscoveredStep(
                step_id="demo-project-STEP-001",
                name="Submit form",
                evidence_ids=["demo-project-EVD-001"],
            )
        ],
        rules=[
            RuleRecord(
                rule_id="demo-project-BR-001",
                statement="Applicants must submit a form.",
                evidence_ids=["demo-project-EVD-001"],
            )
        ],
        warnings=["Sample warning"],
    )


def test_adapter_returns_exact_state_keys():
    state_update = to_state_update(_output_with_records())

    assert set(state_update) == {
        "project_id",
        "source_document_ids",
        "extracted_sections",
        "evidence_items",
        "as_is_process",
        "candidate_business_rules",
        "validation_errors",
    }


def test_lists_contain_plain_dicts_and_result_is_json_serializable():
    state_update = to_state_update(_output_with_records())

    for key in (
        "extracted_sections",
        "evidence_items",
        "as_is_process",
        "candidate_business_rules",
    ):
        assert all(type(record) is dict for record in state_update[key])

    json.dumps(state_update)


def test_confidence_is_string_not_decimal():
    state_update = to_state_update(_output_with_records())

    confidence = state_update["evidence_items"][0]["confidence"]
    assert confidence == "0.90"
    assert not isinstance(confidence, Decimal)


def test_empty_output_returns_empty_record_lists():
    output = MemberTwoOutput(project_id="demo-project", document_id="DOC-DEMO")

    state_update = to_state_update(output)

    assert state_update["source_document_ids"] == ["DOC-DEMO"]
    assert state_update["extracted_sections"] == []
    assert state_update["evidence_items"] == []
    assert state_update["as_is_process"] == []
    assert state_update["candidate_business_rules"] == []
    assert state_update["validation_errors"] == []
