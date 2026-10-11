from member2 import rules_node
from member2.schemas import EvidenceRecord, RuleRecord


def _evidence(
    evidence_id: str,
    quote: str,
    claim_type: str = "rule",
    section_id: str = "DOC-DEMO-S001",
) -> EvidenceRecord:
    return EvidenceRecord(
        id=evidence_id,
        project_id="demo-project",
        document_section_id=section_id,
        quote=quote,
        claim_type=claim_type,
        confidence="0.90",
    )


def _raw_rules(*rules: dict) -> rules_node.RawRuleList:
    return rules_node.RawRuleList(
        rules=[rules_node.RawRule(**rule) for rule in rules]
    )


def _rule(statement: str, evidence_ids: list[str]) -> dict:
    return {
        "statement": statement,
        "condition": None,
        "action": None,
        "scope": None,
        "effective_context": None,
        "evidence_ids": evidence_ids,
    }


def _rule_with_fields(
    statement: str,
    evidence_ids: list[str],
    *,
    condition: str | None = None,
    action: str | None = None,
    scope: str | None = None,
    effective_context: str | None = None,
) -> dict:
    return {
        "statement": statement,
        "condition": condition,
        "action": action,
        "scope": scope,
        "effective_context": effective_context,
        "evidence_ids": evidence_ids,
    }


def test_valid_rules_get_project_ids_and_needs_review_status(monkeypatch):
    evidence = [
        _evidence("demo-project-EVD-001", "Submit the form before 1 June."),
        _evidence("demo-project-EVD-002", "Include a signed statement."),
    ]
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule("Submit the form before 1 June.", ["demo-project-EVD-001"]),
            _rule("Include a signed statement.", ["demo-project-EVD-002"]),
        ),
    )

    rules = rules_node.extract_rules(evidence, "demo-project")

    assert [rule.rule_id for rule in rules] == [
        "demo-project-BR-001",
        "demo-project-BR-002",
    ]
    assert all(isinstance(rule, RuleRecord) for rule in rules)
    assert all(rule.status == "needs_review" for rule in rules)


def test_unknown_evidence_id_is_removed(monkeypatch, capsys):
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule(
                "Submit the form before 1 June.",
                ["demo-project-EVD-001", "unknown-EVD"],
            )
        ),
    )

    rules = rules_node.extract_rules(
        [_evidence("demo-project-EVD-001", "Submit the form before 1 June.")],
        "demo-project",
    )

    assert len(rules) == 1
    assert rules[0].evidence_ids == ["demo-project-EVD-001"]
    assert "removed unknown evidence ID" in capsys.readouterr().out


def test_rule_with_only_unknown_evidence_ids_is_rejected(monkeypatch, capsys):
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule("Unsubstantiated requirement.", ["unknown-EVD"])
        ),
    )

    rules = rules_node.extract_rules(
        [_evidence("demo-project-EVD-001", "Some source text.")],
        "demo-project",
    )

    assert rules == []
    assert "Rejected rule" in capsys.readouterr().out


def test_conflicting_rules_both_survive(monkeypatch):
    evidence = [
        _evidence("demo-project-EVD-001", "Submit the form before 1 June.", "deadline"),
        _evidence("demo-project-EVD-002", "Submit the form before 15 June.", "deadline"),
    ]
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule("Submit the form before 1 June.", ["demo-project-EVD-001"]),
            _rule("Submit the form before 15 June.", ["demo-project-EVD-002"]),
        ),
    )

    rules = rules_node.extract_rules(evidence, "demo-project")

    assert [rule.statement for rule in rules] == [
        "Submit the form before 1 June.",
        "Submit the form before 15 June.",
    ]
    assert [rule.rule_id for rule in rules] == [
        "demo-project-BR-001",
        "demo-project-BR-002",
    ]


def test_none_result_returns_empty_list_and_warns(monkeypatch, capsys):
    monkeypatch.setattr(rules_node, "call_llm", lambda **kwargs: None)

    rules = rules_node.extract_rules(
        [_evidence("demo-project-EVD-001", "Some source text.")],
        "demo-project",
    )

    assert rules == []
    assert "Warning" in capsys.readouterr().out


def test_user_prompt_lists_all_evidence_in_source_input(monkeypatch):
    expected_evidence = [
        _evidence("demo-project-EVD-001", "Submit the form.", "step"),
        _evidence("demo-project-EVD-002", "The deadline is 1 June.", "deadline"),
    ]
    captured = []

    def fake_call_llm(**kwargs):
        captured.append(kwargs)
        return _raw_rules()

    monkeypatch.setattr(rules_node, "call_llm", fake_call_llm)

    rules_node.extract_rules(expected_evidence, "demo-project")

    assert captured[0]["response_model"] is rules_node.RawRuleList
    assert captured[0]["user_prompt"] == (
        "<source>\n"
        "demo-project-EVD-002 | deadline | The deadline is 1 June."
        "\n</source>"
    )


def test_evidence_from_two_sections_causes_two_grouped_calls(monkeypatch):
    evidence = [
        _evidence("demo-project-EVD-001", "First section fact.", section_id="DOC-S001"),
        _evidence("demo-project-EVD-002", "Second section fact.", section_id="DOC-S002"),
    ]
    captured_prompts = []

    def fake_call_llm(**kwargs):
        captured_prompts.append(kwargs["user_prompt"])
        return _raw_rules()

    monkeypatch.setattr(rules_node, "call_llm", fake_call_llm)

    rules_node.extract_rules(evidence, "demo-project")

    assert captured_prompts == [
        "<source>\ndemo-project-EVD-001 | rule | First section fact.\n</source>",
        "<source>\ndemo-project-EVD-002 | rule | Second section fact.\n</source>",
    ]


def test_rule_ids_continue_across_section_groups(monkeypatch):
    evidence = [
        _evidence("demo-project-EVD-001", "First section requirement.", section_id="DOC-S001"),
        _evidence("demo-project-EVD-002", "Second section requirement.", section_id="DOC-S002"),
    ]
    responses = iter(
        (
            _raw_rules(_rule("First requirement.", ["demo-project-EVD-001"])),
            _raw_rules(_rule("Second requirement.", ["demo-project-EVD-002"])),
        )
    )
    monkeypatch.setattr(rules_node, "call_llm", lambda **kwargs: next(responses))

    rules = rules_node.extract_rules(evidence, "demo-project")

    assert [rule.rule_id for rule in rules] == [
        "demo-project-BR-001",
        "demo-project-BR-002",
    ]


def test_failed_section_group_does_not_stop_later_groups(monkeypatch, capsys):
    evidence = [
        _evidence("demo-project-EVD-001", "First section requirement.", section_id="DOC-S001"),
        _evidence("demo-project-EVD-002", "Second section requirement.", section_id="DOC-S002"),
    ]
    responses = iter(
        (
            None,
            _raw_rules(_rule("Second requirement.", ["demo-project-EVD-002"])),
        )
    )
    monkeypatch.setattr(rules_node, "call_llm", lambda **kwargs: next(responses))

    rules = rules_node.extract_rules(evidence, "demo-project")

    assert [rule.statement for rule in rules] == ["Second section requirement."]
    assert [rule.rule_id for rule in rules] == ["demo-project-BR-001"]
    assert "DOC-S001" in capsys.readouterr().out


def test_optional_field_null_string_becomes_none(monkeypatch):
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule_with_fields(
                "Applicants must submit a form.",
                ["demo-project-EVD-001"],
                condition="null",
            )
        ),
    )

    rules = rules_node.extract_rules(
        [_evidence("demo-project-EVD-001", "Applicants must submit a form.")],
        "demo-project",
    )

    assert rules[0].condition is None


def test_optional_field_matching_claim_type_becomes_none(monkeypatch):
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule_with_fields(
                "Applicants must submit a form.",
                ["demo-project-EVD-001"],
                condition="deadline",
            )
        ),
    )

    rules = rules_node.extract_rules(
        [_evidence("demo-project-EVD-001", "Applicants must submit a form.")],
        "demo-project",
    )

    assert rules[0].condition is None


def test_optional_field_matching_statement_becomes_none(monkeypatch):
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule_with_fields(
                "Applicants must submit a form",
                ["demo-project-EVD-001"],
                action="  APPLICANTS   must submit a form ",
            )
        ),
    )

    rules = rules_node.extract_rules(
        [_evidence("demo-project-EVD-001", "Applicants must submit a form.")],
        "demo-project",
    )

    assert rules[0].action is None


def test_genuine_condition_and_action_are_kept_and_stripped(monkeypatch):
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule_with_fields(
                "Applications must be submitted before the deadline.",
                ["demo-project-EVD-001"],
                condition="  When the applicant is enrolled ",
                action=" Submit the application on time ",
                scope=" null ",
                effective_context=" UNKNOWN ",
            )
        ),
    )

    rules = rules_node.extract_rules(
        [_evidence("demo-project-EVD-001", "Applications must be submitted before the deadline.")],
        "demo-project",
    )

    assert rules[0].condition == "When the applicant is enrolled"
    assert rules[0].action == "Submit the application on time"
    assert rules[0].scope is None
    assert rules[0].effective_context is None


def test_single_evidence_repairs_split_statement_and_condition(monkeypatch):
    quote = "The application must be submitted by 15 April"
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule_with_fields(
                "The application deadline is",
                ["demo-project-EVD-001"],
                condition="15 April",
            )
        ),
    )

    rules = rules_node.extract_rules(
        [_evidence("demo-project-EVD-001", quote, "deadline")],
        "demo-project",
    )

    assert rules[0].statement == quote
    assert rules[0].condition is None


def test_single_evidence_repairs_missing_spaces_in_statement(monkeypatch):
    quote = "The family income certificate must be submitted."
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule("The family incomecertificate must be submitted.", ["demo-project-EVD-001"])
        ),
    )

    rules = rules_node.extract_rules(
        [_evidence("demo-project-EVD-001", quote, "form")],
        "demo-project",
    )

    assert rules[0].statement == quote


def test_step_evidence_is_filtered_before_model_call(monkeypatch):
    evidence = [
        _evidence("demo-project-EVD-001", "The clerk reviews the form.", "step"),
        _evidence("demo-project-EVD-002", "Applications close on 15 April.", "deadline"),
    ]
    captured_prompts = []

    def fake_call_llm(**kwargs):
        captured_prompts.append(kwargs["user_prompt"])
        return _raw_rules()

    monkeypatch.setattr(rules_node, "call_llm", fake_call_llm)

    rules_node.extract_rules(evidence, "demo-project")

    assert captured_prompts == [
        "<source>\ndemo-project-EVD-002 | deadline | Applications close on 15 April.\n</source>"
    ]


def test_multiple_evidence_items_keep_model_statement(monkeypatch):
    evidence = [
        _evidence("demo-project-EVD-001", "Applications must be submitted by 15 April."),
        _evidence("demo-project-EVD-002", "Late applications will not be accepted."),
    ]
    model_statement = "Applications have a deadline and late submissions are not accepted."
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule(model_statement, ["demo-project-EVD-001", "demo-project-EVD-002"])
        ),
    )

    rules = rules_node.extract_rules(evidence, "demo-project")

    assert rules[0].statement == model_statement


def test_evidence_id_effective_context_is_removed_but_real_context_is_kept(monkeypatch):
    monkeypatch.setattr(
        rules_node,
        "call_llm",
        lambda **kwargs: _raw_rules(
            _rule_with_fields(
                "Applicants must meet the requirement.",
                ["demo-project-EVD-001"],
                effective_context="demo-project-EVD-020",
            ),
            _rule_with_fields(
                "Applicants must meet the requirement.",
                ["demo-project-EVD-001"],
                effective_context="academic year 2026",
            ),
        ),
    )

    rules = rules_node.extract_rules(
        [_evidence("demo-project-EVD-001", "Applicants must meet the requirement.")],
        "demo-project",
    )

    assert rules[0].effective_context is None
    assert rules[1].effective_context == "academic year 2026"
