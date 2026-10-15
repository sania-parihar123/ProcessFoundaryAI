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
        process_type="scholarship",
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
    result = ingest_documents(
        [Upload("notes.txt", b"General scholarship notes.")],
        process_type="scholarship",
    )

    assert result.state is not None
    assert result.sections
    assert result.evidence_items == []
    assert "no recognized scholarship evidence" in result.message


def test_non_scholarship_process_uses_generic_extraction_boundary() -> None:
    result = ingest_documents(
        [
            Upload(
                "process.txt",
                b"Employees submit requests through the portal.",
            )
        ],
        process_type="service-request",
        config={"vocabulary": {"activity_verbs": ["submit"]}},
    )

    assert result.state is not None
    assert result.evidence_items[0]["kind"] == "activity"
    assert result.process_type == "service-request"
    assert "scholarship" not in result.message


def test_non_scholarship_proposal_uses_generic_workflow_fields() -> None:
    result = ingest_documents(
        [
            Upload(
                "purchase.txt",
                (
                    b"Employees submit purchase requests through the portal. "
                    b"Finance must review requests within three business days."
                ),
            )
        ],
        process_type="purchase-approval",
        config={
            "vocabulary": {
                "activity_verbs": ["submit", "review"],
                "actor_labels": ["Employees", "Finance"],
            }
        },
    )

    assert result.state is not None
    proposal = result.state.workflow_proposal
    assert proposal["status"] == "draft"
    assert proposal["process_type"] == "purchase-approval"
    assert proposal["steps"]
    assert proposal["deadlines"]
    assert proposal["source_refs"] == [result.documents[0]["document_id"]]
    assert all("scholarship" not in str(step).lower() for step in proposal["steps"])


def test_default_path_uses_generic_proposal_for_unfamiliar_process() -> None:
    result = ingest_documents(
        [
            Upload(
                "specimen-intake.txt",
                (
                    b"Specimen custodians accession samples through the intake ledger. "
                    b"Quality control reviews each accession within two business days."
                ),
            )
        ],
        config={
            "vocabulary": {
                "activity_verbs": ["accession", "review"],
                "actor_labels": ["Specimen custodians", "Quality control"],
            }
        },
    )

    assert result.state is not None
    assert result.process_type == "generic-process"
    assert result.evidence_items
    assert all(
        item.get("assertion", {}).get("subject") != "scholarship.eligibility"
        for item in result.evidence_items
    )
    proposal = result.state.workflow_proposal
    assert proposal["process_type"] == "generic-process"
    assert proposal["status"] == "draft"
    assert proposal["steps"]
    assert proposal["deadlines"]
    assert proposal["source_refs"] == [result.documents[0]["document_id"]]
    assert "scholarship" not in str(proposal).lower()


def test_default_path_extracts_steps_for_multiple_generic_processes() -> None:
    examples = [
        (
            "permit-review.txt",
            b"Inspectors review permit requests through the online portal. "
            b"Records staff issue the permit after approval.",
        ),
        (
            "clinic-intake.txt",
            b"Clinic staff register new patients at reception. "
            b"Nurses verify the intake form before scheduling an appointment.",
        ),
    ]

    for filename, content in examples:
        result = ingest_documents([Upload(filename, content)])

        assert result.state is not None
        proposal = result.state.workflow_proposal
        assert proposal["process_type"] == "generic-process"
        assert proposal["steps"]
        assert all(step["evidence_refs"] for step in proposal["steps"])
        assert all(step["source_refs"] for step in proposal["steps"])
        assert all(step["source_locations"] for step in proposal["steps"])


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
        ],
        process_type="scholarship",
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
        process_type="scholarship",
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
