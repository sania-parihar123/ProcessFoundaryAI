from app.agents.evidence_extraction import extract_evidence
from app.agents.analysis import detect_conflicts


def _section(document_id: str, filename: str, text: str, page: int) -> dict[str, object]:
    return {
        "section_id": f"{document_id}:page-{page}",
        "document_id": document_id,
        "filename": filename,
        "page": page,
        "text": text,
    }


def test_supported_claims_preserve_quotes_and_provenance() -> None:
    evidence = extract_evidence(
        [
            _section(
                "document-a",
                "policy-a.txt",
                "Annual family income must not exceed ₹2,50,000. "
                "Minimum attendance of 75% is required.",
                2,
            )
        ]
    )

    assert len(evidence) == 2
    income = next(item for item in evidence if item["assertion"]["predicate"] == "family_income_limit")
    assert income["assertion"]["value"] == 250000
    assert income["quote"] == "Annual family income must not exceed ₹2,50,000"
    assert income["document_id"] == "document-a"
    assert income["filename"] == "policy-a.txt"
    assert income["page"] == 2
    assert income["source_refs"] == ["document-a"]


def test_competing_documents_remain_distinct_and_conflict_is_detected() -> None:
    evidence = extract_evidence(
        [
            _section("document-a", "a.txt", "Annual family income must not exceed ₹2,50,000.", 1),
            _section("document-b", "b.txt", "Annual family income must not exceed ₹3,00,000.", 1),
        ]
    )

    assert len({item["evidence_id"] for item in evidence}) == 2
    conflicts = detect_conflicts(process_type="scholarship", evidence_items=evidence)
    assert len(conflicts) == 1
    assert conflicts[0]["evidence_refs"] == sorted(
        item["evidence_id"] for item in evidence
    )
    assert "authoritative_value" not in conflicts[0]


def test_ambiguous_text_does_not_create_evidence() -> None:
    assert extract_evidence(
        [_section("document-a", "a.txt", "Income may vary depending on circumstances.", 1)]
    ) == []


def test_identical_input_has_stable_evidence_id() -> None:
    section = _section("document-a", "a.txt", "Annual family income must not exceed ₹2,50,000.", 1)

    first = extract_evidence([section])
    second = extract_evidence([section])

    assert first == second


def test_realistic_policy_requirements_are_extracted_generically() -> None:
    evidence = extract_evidence(
        [
            _section(
                "policy",
                "rules.txt",
                (
                    "Applicants must be enrolled in an undergraduate programme. "
                    "Applicants need a minimum academic score of 60%, except for "
                    "students with disabilities. Submit an income certificate. "
                    "The final decision will be made by the scholarship committee."
                ),
                1,
            )
        ]
    )

    predicates = {item["assertion"]["predicate"] for item in evidence}
    assert predicates == {
        "enrollment_requirement",
        "academic_threshold",
        "required_supporting_document",
        "human_review_responsibility",
    }
    academic = next(
        item for item in evidence
        if item["assertion"]["predicate"] == "academic_threshold"
    )
    assert academic["assertion"]["value"] == 60
    assert "except" in academic["quote"]
    assert academic["page"] == 1


def test_income_comparison_wording_and_general_income_are_safe() -> None:
    evidence = extract_evidence(
        [
            _section(
                "policy",
                "rules.txt",
                "Household income is no more than INR 3,00,000.",
                1,
            ),
            _section(
                "vague",
                "notes.txt",
                "Family income is considered during review.",
                1,
            ),
        ]
    )

    assert len(evidence) == 1
    assert evidence[0]["assertion"]["value"] == 300000
    assert evidence[0]["document_id"] == "policy"
