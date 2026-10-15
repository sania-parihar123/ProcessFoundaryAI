import pytest
from pydantic import ValidationError

from app.contracts.evidence import (
    ActorReference,
    Assertion,
    Condition,
    EvidenceItem,
    EvidenceKind,
    EvidenceStatus,
    ExceptionInfo,
    Responsibility,
    SourceLocator,
    TemporalInformation,
    UnknownInformation,
)


def test_all_generic_evidence_kinds_are_valid() -> None:
    for kind in EvidenceKind:
        item = EvidenceItem(
            evidence_id=f"evidence-{kind.value}",
            kind=kind,
            quote="The source states this process fact.",
        )

        assert item.kind is kind
        assert item.status is EvidenceStatus.EXTRACTED


def test_optional_generic_evidence_fields_are_typed() -> None:
    item = EvidenceItem(
        evidence_id="evidence-1",
        kind=EvidenceKind.DECISION,
        status=EvidenceStatus.AMBIGUOUS,
        quote="A manager decides whether the request proceeds.",
        normalized_interpretation="A decision is required.",
        source_refs=["document-1"],
        source_locations=[
            SourceLocator(
                document_id="document-1",
                section_id="document-1:section-2",
                section=2,
            )
        ],
        assertion=Assertion(
            subject="request",
            predicate="approval",
            operator="requires",
            value=True,
        ),
        actors=[ActorReference(label="Manager", role="approver")],
        conditions=[
            Condition(
                expression="amount > threshold",
                evidence_refs=["evidence-2"],
            )
        ],
        exceptions=[
            ExceptionInfo(
                description="Emergency requests may follow another path.",
            )
        ],
        temporal=TemporalInformation(deadline="within 3 business days"),
        responsibilities=[
            Responsibility(actor_refs=["manager"], action="decide")
        ],
        confidence=0.8,
        related_evidence_refs=["evidence-2"],
        unknowns=[
            UnknownInformation(
                field="threshold",
                question="What threshold applies?",
            )
        ],
    )

    assert item.assertion is not None
    assert item.assertion.value is True
    assert item.actors[0].label == "Manager"
    assert item.temporal is not None
    assert item.temporal.deadline == "within 3 business days"
    assert item.unknowns[0].field == "threshold"


def test_exact_quote_preserves_source_whitespace() -> None:
    item = EvidenceItem(
        evidence_id="evidence-quote",
        kind=EvidenceKind.STATEMENT,
        quote="  Exact source quotation.  ",
    )

    assert item.quote == "  Exact source quotation.  "


@pytest.mark.parametrize(
    "locator",
    [
        SourceLocator(document_id="pdf-1", page=3),
        SourceLocator(document_id="docx-1", paragraph=4),
        SourceLocator(document_id="txt-1", section=1, line_start=10, line_end=12),
        SourceLocator(document_id="txt-2", char_start=20, char_end=42),
        SourceLocator(
            document_id="xlsx-1",
            worksheet_name="Rules",
            row_number=7,
            cell_coordinates=["A7", "C7"],
        ),
    ],
)
def test_source_location_variants_do_not_fabricate_other_locations(
    locator: SourceLocator,
) -> None:
    present = locator.model_dump(exclude_none=True)

    assert present["document_id"]
    assert set(present).issubset(
        {
            "document_id",
            "section_id",
            "filename",
            "page",
            "paragraph",
            "section",
            "line_start",
            "line_end",
            "char_start",
            "char_end",
            "newline_convention",
            "heading",
            "table_id",
            "worksheet_name",
            "row_number",
            "cell_coordinates",
        }
    )


def test_invalid_evidence_is_rejected() -> None:
    with pytest.raises(ValidationError):
        EvidenceItem(
            evidence_id=" ",
            kind=EvidenceKind.STATEMENT,
            quote="A valid quote.",
        )

    with pytest.raises(ValidationError):
        EvidenceItem(
            evidence_id="evidence-1",
            kind="not-a-kind",
            quote="A valid quote.",
        )

    with pytest.raises(ValidationError):
        EvidenceItem(
            evidence_id="evidence-1",
            kind=EvidenceKind.STATEMENT,
            quote="A valid quote.",
            confidence=1.5,
        )

    with pytest.raises(ValidationError):
        SourceLocator(document_id="document-1", page=0)


def test_legacy_fields_remain_available() -> None:
    item = EvidenceItem(
        evidence_id="evidence-legacy",
        kind=EvidenceKind.REQUIREMENT,
        quote="Submit the required form.",
        source_id="document-1",
        source_refs=["document-1", "document-1:Sheet1!A2"],
        document_id="document-1",
        filename="rules.xlsx",
        section_id="document-1:worksheet-Sheet1:row-2",
        worksheet_name="Sheet1",
        row_number=2,
        cells=[{"coordinate": "A2", "value": "Submit the required form."}],
        cell_references=["A2"],
        assertion={
            "subject": "request",
            "predicate": "required_form",
            "operator": "requires",
            "value": "form",
        },
    )

    assert item.source_id == "document-1"
    assert item.source_refs == ["document-1", "document-1:Sheet1!A2"]
    assert item.document_id == "document-1"
    assert item.section_id == "document-1:worksheet-Sheet1:row-2"
    assert item.worksheet_name == "Sheet1"
    assert item.row_number == 2
    assert item.cells == [{"coordinate": "A2", "value": "Submit the required form."}]
    assert item.cell_references == ["A2"]
    assert item.assertion is not None
    assert item.assertion.predicate == "required_form"
