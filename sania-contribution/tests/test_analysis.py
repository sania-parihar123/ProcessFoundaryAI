import os
import subprocess
import sys

from app.agents.analysis import analyze_conflicts, analyze_gaps, detect_conflicts, detect_gaps
from app.graph.state import ProcessFoundryState


def _state(**overrides: object) -> ProcessFoundryState:
    values: dict[str, object] = {
        "run_id": "run-001",
        "project_id": "project-001",
        "process_type": "scholarship",
    }
    values.update(overrides)
    return ProcessFoundryState(**values)


def test_complete_inputs_have_no_issues() -> None:
    result = analyze_gaps(
        _state(
            evidence_items=[{"evidence_id": "e-1", "claim": "published"}],
            as_is_process=[{"step_id": "submit"}],
            candidate_business_rules=[{"rule_id": "rule-1", "condition": "income"}],
            config={
                "required_process_steps": ["submit"],
                "required_fields": {
                    "evidence": ["evidence_id"],
                    "process": ["step_id"],
                    "rules": ["rule_id", "condition"],
                },
            },
        )
    )

    assert result["gap_issues"] == []


def test_empty_inputs_are_not_gaps_without_configuration() -> None:
    state = _state()

    assert analyze_gaps(state)["gap_issues"] == []
    assert analyze_conflicts(state)["conflict_issues"] == []


def test_missing_required_attendance_threshold_is_reported_only_when_configured() -> None:
    rule = {"rule_id": "attendance-rule", "condition": "eligibility"}

    without_requirement = detect_gaps(
        process_type="scholarship",
        candidate_business_rules=[rule],
    )
    with_requirement = detect_gaps(
        process_type="scholarship",
        candidate_business_rules=[rule],
        configuration={"required_fields": {"rules": ["attendance_threshold"]}},
    )

    assert without_requirement == []
    assert len(with_requirement) == 1
    assert with_requirement[0]["gap_type"] == "missing_information"
    assert "attendance_threshold" in with_requirement[0]["description"]


def test_ambiguous_record_is_reported_from_explicit_input() -> None:
    issues = detect_gaps(
        process_type="generic",
        evidence_items=[
            {
                "evidence_id": "e-1",
                "ambiguous": True,
                "alternatives": ["A", "B"],
            }
        ],
    )

    assert len(issues) == 1
    assert issues[0]["gap_type"] == "ambiguous_information"
    assert issues[0]["evidence_refs"] == ["e-1"]


def test_income_limit_conflict_preserves_both_claims() -> None:
    evidence = [
        {
            "evidence_id": "income-a",
            "source_id": "document-a",
            "assertion": {
                "subject": "scholarship.eligibility",
                "predicate": "family_income_limit",
                "operator": "equals",
                "value": 250000,
                "unit": "INR",
            },
        },
        {
            "evidence_id": "income-b",
            "source_id": "document-b",
            "assertion": {
                "subject": "scholarship.eligibility",
                "predicate": "family_income_limit",
                "operator": "equals",
                "value": 300000,
                "unit": "INR",
            },
        },
    ]

    issues = detect_conflicts(process_type="scholarship", evidence_items=evidence)

    assert len(issues) == 1
    assert issues[0]["conflict_type"] == "evidence_vs_evidence"
    assert issues[0]["status"] == "open"
    assert issues[0]["evidence_refs"] == ["income-a", "income-b"]
    assert issues[0]["source_refs"] == ["document-a", "document-b"]
    assert "250000" in issues[0]["description"]
    assert "300000" in issues[0]["description"]
    assert "authoritative_value" not in issues[0]


def test_missing_confidence_is_not_invented_or_reported_by_default() -> None:
    issues = detect_gaps(
        process_type="generic",
        evidence_items=[{"evidence_id": "e-1", "claim": "fact"}],
    )

    assert issues == []


def _scoped_evidence(scope: object = None, effective_context: object = None) -> list[dict[str, object]]:
    assertion: dict[str, object] = {
        "subject": "scholarship.eligibility",
        "predicate": "family_income_limit",
        "operator": "equals",
        "value": 250000,
    }
    if scope is not None:
        assertion["scope"] = scope
    if effective_context is not None:
        assertion["effective_context"] = effective_context
    other_assertion = {**assertion, "value": 300000}
    return [
        {"evidence_id": "income-a", "assertion": assertion},
        {"evidence_id": "income-b", "assertion": other_assertion},
    ]


def test_conflicting_claims_with_matching_scopes_are_detected() -> None:
    issues = detect_conflicts(
        process_type="scholarship",
        evidence_items=_scoped_evidence(
            scope={"applicant_type": "student"},
            effective_context={"academic_year": "2026"},
        ),
    )

    assert len(issues) == 1
    assert issues[0]["conflict_type"] == "evidence_vs_evidence"


def test_conflicting_claims_with_mismatched_scopes_are_not_detected() -> None:
    evidence = _scoped_evidence(scope={"applicant_type": "student"})
    evidence[1]["assertion"] = {
        **evidence[1]["assertion"],
        "scope": {"applicant_type": "researcher"},
    }

    assert detect_conflicts(
        process_type="scholarship",
        evidence_items=evidence,
    ) == []


def test_claim_with_scope_and_claim_without_scope_are_not_comparable() -> None:
    evidence = _scoped_evidence(scope={"applicant_type": "student"})
    del evidence[1]["assertion"]["scope"]

    assert detect_conflicts(
        process_type="scholarship",
        evidence_items=evidence,
    ) == []


def test_missing_confidence_is_reported_when_explicitly_required() -> None:
    issues = detect_gaps(
        process_type="generic",
        evidence_items=[{"evidence_id": "e-1", "claim": "fact"}],
        configuration={"require_confidence": True},
    )

    assert len(issues) == 1
    assert issues[0]["gap_type"] == "missing_information"


def test_repeated_analysis_has_stable_ids() -> None:
    state = _state(
        evidence_items=[
            {
                "evidence_id": "e-1",
                "assertion": {
                    "subject": "eligibility",
                    "predicate": "limit",
                    "operator": "equals",
                    "value": 1,
                },
            },
            {
                "evidence_id": "e-2",
                "assertion": {
                    "subject": "eligibility",
                    "predicate": "limit",
                    "operator": "equals",
                    "value": 2,
                },
            },
        ],
    )

    first = analyze_conflicts(state)["conflict_issues"]
    second = analyze_conflicts(state)["conflict_issues"]

    assert first == second
    assert first[0]["conflict_id"].startswith("conflict-")


def test_set_valued_inputs_have_stable_ids_across_hash_seeds() -> None:
    script = """
from app.agents.analysis import detect_conflicts

evidence = [
    {
        "evidence_id": "income-a",
        "assertion": {
            "subject": "eligibility",
            "predicate": "limit",
            "operator": "equals",
            "value": 1,
            "scope": {"groups": {"alpha", "beta", "gamma"}},
        },
    },
    {
        "evidence_id": "income-b",
        "assertion": {
            "subject": "eligibility",
            "predicate": "limit",
            "operator": "equals",
            "value": 2,
            "scope": {"groups": {"alpha", "beta", "gamma"}},
        },
    },
]
print(detect_conflicts(process_type="generic", evidence_items=evidence)[0]["conflict_id"])
"""
    workspace = os.path.dirname(os.path.dirname(__file__))
    outputs: list[str] = []
    for hash_seed in ("1", "2"):
        environment = os.environ.copy()
        environment["PYTHONHASHSEED"] = hash_seed
        environment["PYTHONPATH"] = workspace
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=workspace,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        outputs.append(result.stdout.strip())

    assert outputs[0] == outputs[1]
