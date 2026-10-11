# traceability_audit — Traceability & Workflow Audit

Plain Python. No LLM. Imports nothing from `member2/`, `requirements_artifacts/`, `clarification_hitl/` or `sania-contribution/`. It only reads dicts and never changes them.

## What it does
- `build_graph(state_update, requirements, tests)` links: evidence <- steps / rules <- requirements <- tests, plus issues, questions, answers, decisions.
  - `graph.evidence_for(id)`: the full chain back to the source quote.
  - `graph.downstream(id)`: impact analysis (what to re-check if a piece of evidence changes).
- `validate(graph, state_update)` reports problems: dangling IDs, steps/rules/requirements with no evidence, requirements with no source step/rule, unused evidence, unanswered questions, "approved" without a human decision or with open questions.
- `AuditLog` is an append-only event log with a hash chain. Editing or deleting an old event is detected by `verify()`. `import_hitl(state)` adds question/answer/decision events from the clarification module (safe to call repeatedly).
- `views`: Markdown traceability matrix, impact report, workflow history, validation report (all marked DRAFT).
- `run_traceability(state, requirements, tests, audit)` does all of it in one call.

## Inputs (read tolerantly, several field spellings accepted)
`evidence_items`, `as_is_process.steps`, `candidate_business_rules`, `gap_issues`, `conflict_issues`, `clarification_questions`, `human_answers`, `decisions`, `approval_status`, `pending_question_ids`; requirements list (id, evidence_ids, related step/rule ids); optional tests list `{test_id, requirement_ids}`.

## Workflow events
Sania's graph can call `audit.record(event_type, actor, subject, details)` at each node (e.g. `node_started`, `gap_found`, `paused_for_human`) so the history shows the whole run.

## Run
    python -m pytest traceability_audit/tests -q
    python -m traceability_audit.run_traceability_demo
    python -m traceability_audit.run_traceability_demo <state_update.json> <requirements.json>
