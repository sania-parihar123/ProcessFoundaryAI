# clarification_hitl — Human-in-the-loop (HITL) module

Plain Python. No LLM calls. Imports nothing from `member2/`, `requirements_artifacts/` or `sania-contribution/`.

## What it does
1. `question_builder.build_questions(state_update)` reads `project_id`, `as_is_process`, `candidate_business_rules` and creates questions: missing actor, conflicting dates/rules (both kept as options), vague terms, other unknowns.
2. `ClarificationStore` records answers and human decisions and enforces the rules:
   - same problem never asked twice; same answer sent twice is stored once
   - every answer has a name, role and time; re-answering keeps the old answer (marked superseded)
   - stale questions can be re-opened (`mark_stale`) and cancel an earlier approval
   - only roles `approver`, `process_owner`, `admin` may decide; approve is refused while questions are open; reject needs a reason
   - **nothing is ever approved automatically**
3. `store.to_state_update()` returns keys named like `ProcessFoundryState`: `clarification_questions`, `human_answers`, `decisions`, `pending_question_ids`, `approval_status` (pending/approved/rejected), `lifecycle_status` (paused_for_human / running).

## Resume contract (for the LangGraph part)
- After the AI layer runs: `store.load_from_state(state)`; if `not store.is_ready_to_resume()` → pause the graph (`paused_for_human`).
- The UI/API calls `record_answer(question_id, text, answered_by, role)`.
- When `is_ready_to_resume()` is True → resume. Approval still needs a human `record_decision(...)`.
- Save/restore between pauses: `store.save(path)` / `ClarificationStore.load(path)`.

## Run
    python -m pytest clarification_hitl/tests -q
    python -m clarification_hitl.run_clarification_demo
