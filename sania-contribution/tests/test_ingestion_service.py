from io import BytesIO

from app.agents.ingestion_service import ingest_documents


class Upload(BytesIO):
    def __init__(self, name: str, content: bytes):
        super().__init__(content)
        self.name = name


def test_multiple_documents_flow_into_state_and_graph() -> None:
    result = ingest_documents(
        [
            Upload("a.txt", b"Annual family income must not exceed Rs. 250000."),
            Upload("b.txt", b"Annual family income must not exceed Rs. 300000."),
        ],
        project_id="project-1",
    )

    assert len(result.documents) == 2
    assert len(result.sections) == 2
    assert len(result.evidence_items) == 2
    assert result.state is not None
    assert result.state.source_document_ids == [
        document["document_id"] for document in result.documents
    ]
    assert result.state.conflict_issues[0]["evidence_refs"] == sorted(
        item["evidence_id"] for item in result.evidence_items
    )


def test_empty_upload_does_not_run_analysis() -> None:
    result = ingest_documents([])

    assert result.state is None
    assert result.documents == []
    assert result.evidence_items == []
    assert "No documents" in result.message


def test_file_errors_are_preserved_without_fabricated_findings() -> None:
    result = ingest_documents([Upload("bad.csv", b"not supported")])

    assert result.state is None
    assert len(result.errors) == 1
    assert result.errors[0].filename == "bad.csv"
    assert result.errors[0].code == "unsupported_type"
    assert result.evidence_items == []


def test_text_without_supported_claim_is_distinguished_from_empty_upload() -> None:
    result = ingest_documents([Upload("notes.txt", b"General scholarship notes.")])

    assert result.state is not None
    assert result.sections
    assert result.evidence_items == []
    assert "no recognized scholarship evidence" in result.message


def test_proposal_is_unapproved_and_provenance_backed() -> None:
    result = ingest_documents(
        [
            Upload(
                "policy.txt",
                (
                    b"Applicants must be enrolled in a degree programme. "
                    b"Submit an income certificate. "
                    b"Final approval will be made by the scholarship committee."
                ),
            )
        ]
    )

    assert result.state is not None
    proposal = result.state.workflow_proposal
    assert proposal["status"] == "draft"
    assert len(proposal["steps"]) >= 3
    assert any("enrollment" in step["step"].lower() for step in proposal["steps"])
    assert proposal["required_inputs"]
    assert proposal["roles"] == ["the scholarship committee"]
    assert proposal["source_refs"] == [result.documents[0]["document_id"]]
    assert len(proposal["requirements"]) == len(result.evidence_items)
    assert all(
        requirement["evidence_refs"] and requirement["source_refs"]
        for requirement in proposal["requirements"]
    )
    assert "cannot yet" not in proposal["explanation"]


def test_proposal_keeps_conflicts_and_configured_gaps_visible() -> None:
    result = ingest_documents(
        [
            Upload("a.txt", b"Annual family income must not exceed Rs. 250000."),
            Upload("b.txt", b"Annual family income must not exceed Rs. 300000."),
        ],
        config={
            "required_fields": {"evidence": ["attendance_threshold"]},
        },
    )

    assert result.state is not None
    proposal = result.state.workflow_proposal
    assert proposal["conflicts"]
    assert len(proposal["conflicts"][0]["competing_assertions"]) == 2
    assert proposal["unresolved_questions"]
    assert len(proposal["decision_points"]) == 2
    assert all(
        point["description"] and point["evidence_refs"] and point["source_refs"]
        for point in proposal["decision_points"]
    )
