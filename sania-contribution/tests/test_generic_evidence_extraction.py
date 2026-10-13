from app.agents.evidence_extraction import extract_evidence


def _section(text: str) -> dict[str, object]:
    return {
        "section_id": "document-generic:section-1",
        "document_id": "document-generic",
        "filename": "process.txt",
        "section": 1,
        "text": text,
        "source_locator": {
            "document_id": "document-generic",
            "section_id": "document-generic:section-1",
            "filename": "process.txt",
            "section": 1,
            "char_start": 0,
            "char_end": len(text),
            "line_start": 1,
            "line_end": 1,
            "newline_convention": "none",
        },
    }


_VOCABULARY = {
    "activity_verbs": [
        "submit",
        "review",
        "create",
        "provision",
        "notify",
        "escalate",
    ],
    "actor_labels": [
        "Employees",
        "Finance",
        "Human Resources",
        "IT",
        "Facilities",
        "Facilities manager",
    ],
}


def test_purchase_approval_uses_generic_kinds_and_exact_quotes() -> None:
    text = (
        "Employees submit purchase requests through the portal. "
        "Requests above USD 5,000 require department-head approval. "
        "Finance must review approved requests within three business days. "
        "Except for emergency purchases, the normal approval sequence applies."
    )

    evidence = extract_evidence(
        [_section(text)],
        strategy="generic",
        process_description="A purchase approval process.",
        vocabulary=_VOCABULARY,
    )

    assert {item["kind"] for item in evidence} >= {
        "activity",
        "requirement",
        "deadline",
        "exception",
    }
    for item in evidence:
        assert text[item["quote_char_start"]:item["quote_char_end"]] == item["quote"]
        assert item["source_refs"] == ["document-generic"]
        assert item["source_locations"][0]["section"] == 1


def test_generic_deadline_matching_requires_temporal_context() -> None:
    examples = [
        ("Requests must be submitted within five days.", "deadline"),
        (
            "Finance must complete the review within three business days.",
            "deadline",
        ),
        (
            "Complete the review before the employee start date.",
            "deadline",
        ),
        ("Submit the form by Friday.", "deadline"),
        ("Submit the form by the end of the month.", "deadline"),
        (
            "The application must be approved by an authorized reviewer.",
            "requirement",
        ),
        ("The application is reviewed by the committee.", "activity"),
    ]

    for text, expected_kind in examples:
        evidence = extract_evidence([_section(text)], strategy="generic")

        assert len(evidence) == 1
        assert evidence[0]["kind"] == expected_kind
        assert text[
            evidence[0]["quote_char_start"]:evidence[0]["quote_char_end"]
        ] == text
        assert evidence[0]["source_refs"] == ["document-generic"]
        assert evidence[0]["source_locations"][0]["section"] == 1


def test_generic_marker_precedence_preserves_activity_condition_and_statement() -> None:
    examples = [
        ("Employees submit purchase requests.", "activity"),
        ("If information is missing, contact the applicant.", "condition"),
        ("The system stores the submitted request.", "statement"),
    ]

    for text, expected_kind in examples:
        evidence = extract_evidence([_section(text)], strategy="generic")

        assert len(evidence) == 1
        assert evidence[0]["kind"] == expected_kind


def test_employee_onboarding_preserves_actors_without_inventing_roles() -> None:
    text = (
        "Human Resources creates the employee record after the signed offer "
        "is received. IT must provision access before the employee start date. "
        "A signed offer is required. "
        "If equipment is unavailable, the hiring manager must document the exception."
    )

    evidence = extract_evidence(
        [_section(text)],
        config={"extraction_strategy": "generic"},
        vocabulary={
            **_VOCABULARY,
            "activity_verbs": ["create", "provision", "document"],
        },
    )

    assert any(item["kind"] == "activity" for item in evidence)
    assert any(item["kind"] == "requirement" for item in evidence)
    assert any(
        actor["label"] == "Human Resources"
        for item in evidence
        for actor in item.get("actors", [])
    )
    assert all(
        "role" not in actor
        for item in evidence
        for actor in item.get("actors", [])
    )


def test_facilities_request_condition_and_unknown_remain_explicit() -> None:
    text = (
        "Facilities reviews maintenance requests every morning. "
        "If a safety issue is reported, escalate it to the Facilities manager. "
        "The response deadline is unclear."
    )

    evidence = extract_evidence(
        [_section(text)],
        strategy="generic",
        vocabulary={
            "activity_verbs": ["review", "escalate"],
            "actor_labels": ["Facilities", "Facilities manager"],
        },
    )

    assert any(item["kind"] == "activity" for item in evidence)
    assert any(item["kind"] == "condition" for item in evidence)
    unknown = next(item for item in evidence if item["status"] == "unresolved")
    assert unknown["kind"] == "statement"
    assert unknown["unknowns"][0]["field"] == "interpretation"
    assert "deadline is unclear" in unknown["quote"]


def test_configuration_guides_extraction_but_is_not_source_evidence() -> None:
    text = "The request is submitted through the portal."
    evidence = extract_evidence(
        [_section(text)],
        config={
            "extraction_strategy": "generic",
            "required_evidence": ["approval_threshold"],
            "expected_process_steps": ["approve request"],
        },
        process_description="A generic request process.",
        vocabulary={"activity_verbs": ["submit"]},
    )

    assert len(evidence) == 1
    assert evidence[0]["quote"] == text
    assert "approval_threshold" not in evidence[0]["quote"]
    assert "approve request" not in evidence[0]["quote"]


def test_generic_extraction_does_not_invent_unsupported_assertions() -> None:
    text = "Requests may vary depending on circumstances."

    evidence = extract_evidence(
        [_section(text)],
        strategy="generic",
    )

    assert len(evidence) == 1
    assert evidence[0]["status"] == "unresolved"
    assert "assertion" not in evidence[0]
    assert evidence[0]["unknowns"]


def test_configured_kind_markers_support_other_generic_kinds() -> None:
    evidence = extract_evidence(
        [
            _section(
                "The owner is recorded. "
                "The responsible party handles the request. "
                "The reference links two records. "
                "The submitted data is retained."
            )
        ],
        strategy="generic",
        vocabulary={
            "kind_markers": {
                "actor": ["owner"],
                "responsibility": ["responsible party"],
                "relationship": ["links"],
                "data": ["data"],
            }
        },
    )

    assert {item["kind"] for item in evidence} == {
        "actor",
        "responsibility",
        "relationship",
        "data",
    }


def test_generic_strategy_never_emits_scholarship_specific_assertions() -> None:
    evidence = extract_evidence(
        [
            _section(
                "Applicants must be enrolled in a programme. "
                "The scholarship committee reviews the request."
            )
        ],
        strategy="generic",
    )

    assert evidence
    assert all(
        item.get("assertion", {}).get("subject") != "scholarship.eligibility"
        for item in evidence
    )
    assert all(
        not str(item.get("assertion", {}).get("predicate", "")).startswith(
            ("family_", "enrollment_", "academic_", "attendance_", "human_review_")
        )
        for item in evidence
    )
