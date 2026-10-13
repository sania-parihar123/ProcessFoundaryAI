from io import BytesIO

from docx import Document

from app.agents.evidence_extraction import extract_evidence
from app.agents.analysis import detect_conflicts
from app.agents.document_ingestion import extract_document


def _section(document_id: str, filename: str, text: str, page: int) -> dict[str, object]:
    return {
        "section_id": f"{document_id}:page-{page}",
        "document_id": document_id,
        "filename": filename,
        "page": page,
        "text": text,
    }


class Upload(BytesIO):
    def __init__(self, name: str, content: bytes):
        super().__init__(content)
        self.name = name


def test_text_and_docx_evidence_quotes_match_structured_source_fragments() -> None:
    text_document = extract_document(
        Upload(
            "policy.txt",
            b"Annual family income must not exceed Rs. 250000.\n",
        )
    )
    docx = Document()
    docx.add_paragraph("Annual family income must not exceed Rs. 250000.")
    docx_buffer = BytesIO()
    docx.save(docx_buffer)
    docx_document = extract_document(
        Upload("policy.docx", docx_buffer.getvalue())
    )

    for document in (text_document, docx_document):
        evidence = extract_evidence(document.sections, strategy="scholarship_compat")
        assert len(evidence) == 1
        item = evidence[0]
        locator = item["source_locations"][0]
        source_text = next(
            section["text"]
            for section in document.sections
            if section["section_id"] == item["section_id"]
        )
        assert source_text[locator["char_start"]:locator["char_end"]] == item["quote"]
        assert item["quote_char_start"] == locator["char_start"]
        assert item["quote_char_end"] == locator["char_end"]
        if document.file_type == "txt":
            assert locator["line_start"] == 1
            assert locator["line_end"] == 1


def test_pdf_evidence_quote_matches_page_text() -> None:
    stream = (
        b"BT /F1 12 Tf 72 720 Td "
        b"(Annual family income must not exceed Rs. 250000.) Tj ET"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    content = b"%PDF-1.4\n"
    offsets = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(content))
        content += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(content)
    content += b"xref\n0 6\n0000000000 65535 f \n"
    content += b"".join(
        f"{offset:010d} 00000 n \n".encode() for offset in offsets
    )
    content += (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref).encode()
        + b"\n%%EOF"
    )

    document = extract_document(Upload("policy.pdf", content))
    item = extract_evidence(document.sections, strategy="scholarship_compat")[0]
    locator = item["source_locations"][0]
    page_text = document.sections[0]["text"]

    assert locator["page"] == 1
    assert page_text[locator["char_start"]:locator["char_end"]] == item["quote"]


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
        ],
        strategy="scholarship_compat",
    )

    assert len(evidence) == 2
    income = next(item for item in evidence if item["assertion"]["predicate"] == "family_income_limit")
    assert income["assertion"]["value"] == 250000
    assert income["quote"] == "Annual family income must not exceed ₹2,50,000"
    assert income["document_id"] == "document-a"
    assert income["filename"] == "policy-a.txt"
    assert income["page"] == 2
    assert income["source_refs"] == ["document-a"]


def test_scholarship_compatibility_adapter_preserves_contract_fields() -> None:
    section = _section(
        "document-a",
        "policy-a.txt",
        "Applicants must be enrolled in an undergraduate programme.",
        2,
    )
    section["source_locator"] = {
        "document_id": "document-a",
        "section_id": "document-a:page-2",
        "filename": "policy-a.txt",
        "page": 2,
        "section": 2,
    }
    evidence = extract_evidence(
        [section],
        strategy="scholarship_compat",
    )

    item = evidence[0]
    assert item["assertion"]["subject"] == "scholarship.eligibility"
    assert item["assertion"]["predicate"] == "enrollment_requirement"
    assert item["kind"] == "requirement"
    assert item["source_refs"] == ["document-a"]
    assert item["source_locations"][0]["page"] == 2
    assert item["source_locations"][0]["char_start"] >= 0


def test_competing_documents_remain_distinct_and_conflict_is_detected() -> None:
    evidence = extract_evidence(
        [
            _section("document-a", "a.txt", "Annual family income must not exceed ₹2,50,000.", 1),
            _section("document-b", "b.txt", "Annual family income must not exceed ₹3,00,000.", 1),
        ],
        strategy="scholarship_compat",
    )

    assert len({item["evidence_id"] for item in evidence}) == 2
    conflicts = detect_conflicts(process_type="scholarship", evidence_items=evidence)
    assert len(conflicts) == 1
    assert conflicts[0]["evidence_refs"] == sorted(
        item["evidence_id"] for item in evidence
    )
    assert "authoritative_value" not in conflicts[0]


def test_default_evidence_strategy_is_generic() -> None:
    evidence = extract_evidence(
        [
            _section(
                "document-a",
                "specimens.txt",
                "Custodians accession samples through the intake ledger.",
                1,
            )
        ],
        vocabulary={"activity_verbs": ["accession"]},
    )

    assert evidence[0]["kind"] == "activity"
    assert evidence[0]["assertion"]["subject"] == "process"
    assert evidence[0]["assertion"]["predicate"] == "activity"


def test_ambiguous_text_does_not_create_evidence() -> None:
    assert extract_evidence(
        [_section("document-a", "a.txt", "Income may vary depending on circumstances.", 1)],
        strategy="scholarship_compat",
    ) == []


def test_identical_input_has_stable_evidence_id() -> None:
    section = _section("document-a", "a.txt", "Annual family income must not exceed ₹2,50,000.", 1)

    first = extract_evidence([section], strategy="scholarship_compat")
    second = extract_evidence([section], strategy="scholarship_compat")

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
        ],
        strategy="scholarship_compat",
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
        ],
        strategy="scholarship_compat",
    )

    assert len(evidence) == 1
    assert evidence[0]["assertion"]["value"] == 300000
    assert evidence[0]["document_id"] == "policy"
