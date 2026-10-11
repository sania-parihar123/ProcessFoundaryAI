from requirements_artifacts.artifact_schemas import RequirementsOutput


CLARIFICATION = "Not stated in the source documents. Needs clarification."
DRAFT_BANNER = "Status: DRAFT. AI-generated, not approved."


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _section_text(state_update: dict, title_fragment: str) -> str | None:
    fragment = title_fragment.casefold()
    for section in state_update.get("extracted_sections", []):
        title = section.get("section_title") or ""
        if fragment in title.casefold() and section.get("text"):
            return section["text"]
    return None


def _heading_content(text: str | None) -> str:
    return text if text else CLARIFICATION


def _open_questions_markdown(requirements: RequirementsOutput) -> str:
    if not requirements.open_questions:
        return CLARIFICATION
    return "\n".join(
        f"- {question.question} Reason: {question.reason} "
        f"(Related: {', '.join(question.related_ids)})"
        for question in requirements.open_questions
    )


def _acceptance_criteria_markdown(requirements: RequirementsOutput) -> str:
    criteria = [
        criterion
        for requirement in requirements.requirements
        for criterion in requirement.acceptance_criteria
    ]
    return "\n".join(f"- {criterion}" for criterion in criteria) or CLARIFICATION


def _document_header(document_title: str, requirements: RequirementsOutput) -> str:
    return "\n".join(
        [
            DRAFT_BANNER,
            f"Project ID: {requirements.project_id}",
            f"Schema version: {requirements.schema_version}",
            "",
            f"# {document_title}",
        ]
    )


def build_documents(
    state_update: dict,
    requirements: RequirementsOutput,
) -> dict[str, str]:
    steps = state_update.get("as_is_process", [])
    rules = state_update.get("candidate_business_rules", [])
    evidence_items = state_update.get("evidence_items", [])
    questions = _open_questions_markdown(requirements)
    criteria = _acceptance_criteria_markdown(requirements)
    actors = list(dict.fromkeys(step["actor"] for step in steps if step.get("actor") is not None))

    current_steps = "\n".join(
        f"{index}. {step['name']} — {step.get('actor') if step.get('actor') is not None else 'actor not stated'}"
        for index, step in enumerate(steps, start=1)
    ) or CLARIFICATION
    stakeholders = "\n".join(f"- {actor}" for actor in actors) or CLARIFICATION
    business_rules = "\n".join(
        f"- {rule['rule_id']}: {rule['statement']} "
        f"(Evidence: {', '.join(rule.get('evidence_ids', [])) or CLARIFICATION})"
        for rule in rules
    ) or CLARIFICATION
    business_needs = "\n".join(
        f"- {rule['statement']}" for rule in rules
    ) or CLARIFICATION

    requirements_by_type: dict[str, list] = {
        "functional": [
            item for item in requirements.requirements if item.req_type == "functional"
        ],
        "workflow": [
            item for item in requirements.requirements if item.req_type == "workflow"
        ],
    }

    functional_rows = "\n".join(
        f"| {_markdown_cell(item.id)} | {_markdown_cell(item.statement)} | "
        f"{_markdown_cell(item.status)} | "
        f"{_markdown_cell(', '.join(item.rule_ids) or '—')} | "
        f"{_markdown_cell(', '.join(item.evidence_ids) or '—')} |"
        for item in requirements_by_type["functional"]
    ) or f"| {CLARIFICATION} | {CLARIFICATION} | {CLARIFICATION} | {CLARIFICATION} | {CLARIFICATION} |"

    workflow_steps = "\n".join(
        f"{index}. {step['name']} — "
        f"{step.get('actor') if step.get('actor') is not None else 'actor not stated'}"
        for index, step in enumerate(steps, start=1)
    ) or CLARIFICATION
    features = "\n".join(
        f"- {item.statement}" for item in requirements_by_type["workflow"]
    ) or CLARIFICATION
    user_stories = "\n".join(
        f"- As a {step['actor']}, I need to {step['name']}"
        for step in steps
        if step.get("actor") is not None
    ) or CLARIFICATION
    priorities = "\n".join(
        f"- {priority}: {sum(item.priority == priority for item in requirements.requirements)}"
        for priority in ("Must", "Should", "Could")
    )

    goals = _section_text(state_update, "goal")
    if goals is None:
        goals = None

    brd = "\n\n".join(
        [
            _document_header("Business Requirements Document (BRD)", requirements),
            "## Purpose\n\n" + _heading_content(_section_text(state_update, "purpose")),
            "## Business problem\n\n" + CLARIFICATION,
            "## Goals\n\n" + _heading_content(goals),
            "## Scope\n\n" + _heading_content(_section_text(state_update, "procedure")),
            "## Stakeholders\n\n" + stakeholders,
            "## Current process\n\n" + current_steps,
            "## Business needs\n\n" + business_needs,
            "## Business rules\n\n" + business_rules,
            "## Constraints\n\n" + CLARIFICATION,
            "## Assumptions and open questions\n\n" + questions,
            "## Risks\n\n" + CLARIFICATION,
            "## Success measures\n\n" + CLARIFICATION,
            "## Approvals\n\nPending. No approvals recorded.",
        ]
    )

    frd = "\n\n".join(
        [
            _document_header("Functional Requirements Document (FRD)", requirements),
            "## System overview\n\n" + _heading_content(_section_text(state_update, "purpose")),
            "## Actors and roles\n\n" + stakeholders,
            "## Functional requirements\n\n"
            "| ID | Statement | Status | Rule IDs | Evidence IDs |\n"
            "|---|---|---|---|---|\n"
            + functional_rows,
            "## Workflow\n\n" + workflow_steps,
            "## Open questions\n\n" + questions,
            "## Permissions\n\n" + CLARIFICATION,
            "## Acceptance criteria\n\n" + criteria,
        ]
    )

    prd = "\n\n".join(
        [
            _document_header("Product Requirements Document (PRD)", requirements),
            "## Product goal\n\n" + _heading_content(_section_text(state_update, "purpose")),
            "## Users\n\n" + stakeholders,
            "## User problems\n\n" + CLARIFICATION,
            "## Features\n\n" + features,
            "## User stories\n\n" + user_stories,
            "## Priorities\n\n" + priorities,
            "## Acceptance criteria\n\n" + criteria,
            "## Dependencies\n\n" + CLARIFICATION,
            "## Open questions\n\n" + questions,
        ]
    )

    evidence_by_id = {item["id"]: item.get("quote", "") for item in evidence_items}
    traceability_rows: list[str] = []
    for item in requirements.requirements:
        first_quote = (
            evidence_by_id.get(item.evidence_ids[0], CLARIFICATION)
            if item.evidence_ids
            else CLARIFICATION
        )
        traceability_rows.append(
            f"| {_markdown_cell(item.id)} | {_markdown_cell(item.req_type)} | "
            f"{_markdown_cell(item.status)} | "
            f"{_markdown_cell(', '.join(item.rule_ids) or '—')} | "
            f"{_markdown_cell(', '.join(item.step_ids) or '—')} | "
            f"{_markdown_cell(', '.join(item.evidence_ids) or '—')} | "
            f"{_markdown_cell(first_quote)} |"
        )

    used_evidence_ids = {
        evidence_id
        for item in requirements.requirements
        for evidence_id in item.evidence_ids
    }
    used_step_ids = {
        step_id for item in requirements.requirements for step_id in item.step_ids
    }
    used_rule_ids = {
        rule_id for item in requirements.requirements for rule_id in item.rule_ids
    }
    no_evidence = [
        item.id for item in requirements.requirements if not item.evidence_ids
    ]
    unused_evidence = [
        item["id"] for item in evidence_items if item["id"] not in used_evidence_ids
    ]
    steps_without_requirements = [
        step["step_id"] for step in steps if step["step_id"] not in used_step_ids
    ]
    rules_without_requirements = [
        rule["rule_id"] for rule in rules if rule["rule_id"] not in used_rule_ids
    ]

    def coverage_line(label: str, values: list[str]) -> str:
        return f"- {label}: {', '.join(values) if values else 'None'}"

    traceability = "\n\n".join(
        [
            _document_header("Traceability", requirements),
            "| Requirement ID | Type | Status | Rule IDs | Step IDs | Evidence IDs | First evidence quote |\n"
            "|---|---|---|---|---|---|---|\n"
            + ("\n".join(traceability_rows) or f"| {CLARIFICATION} | — | — | — | — | — | — |"),
            "## Coverage\n\n"
            + "\n".join(
                [
                    coverage_line("Requirements with no evidence", no_evidence),
                    coverage_line("Evidence items not used by any requirement", unused_evidence),
                    coverage_line("Steps without a requirement", steps_without_requirements),
                    coverage_line("Rules without a requirement", rules_without_requirements),
                ]
            ),
        ]
    )

    return {
        "BRD": brd,
        "FRD": frd,
        "PRD": prd,
        "TRACEABILITY": traceability,
    }
