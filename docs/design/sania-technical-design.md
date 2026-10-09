# Sania's Technical Design

**Status:** Proposed design for review  
**Owner:** Sania Parihar
**Date:** 2026-10-09

## 1. Design goals and assumptions

This design defines the orchestration and review layer without assuming that Member 1's backend or Member 2's extraction modules already exist. The implementation will use Pydantic contracts, LangGraph for execution/checkpoint boundaries, explicit Python routing, and Streamlit as the demonstration UI.

The workflow is process-neutral. Scholarship data is a fixture and a demonstration configuration, not a domain model requirement. Integration adapters will isolate provisional contracts from future teammate implementations.

### Explicit assumptions

- Member 2 supplies structured records, not raw LLM responses.
- Member 1 supplies project/source/decision persistence through a reviewed interface.
- Exact external field names, authentication, persistence, and authorization mechanisms are undecided.
- A single-process in-memory implementation is acceptable for the first demonstrator.
- LangGraph's checkpointer is the workflow pause/resume mechanism; its concrete production backend is not selected.

## 2. Component architecture

```text
Streamlit pages
    |
Page view-models / application services
    |
Run service ---- Issue analysis (gap + conflict detectors)
    |                         |
LangGraph graph -------------+---- Pydantic domain contracts
    |                         |
Checkpoint adapter            |---- Member 2 input adapter
    |                         |---- Member 1 project/source/decision adapter
    +---- Mock adapters and deterministic fixtures
```

### Responsibilities

- **Domain contracts:** Pydantic models, enums, stable IDs, validation, status transitions.
- **Adapters:** Translate external teammate contracts into domain contracts; no direct database or extractor imports in graph nodes.
- **Analysis services:** Pure, deterministic gap/conflict detection over normalized records.
- **Graph factory:** Constructs the LangGraph nodes, edges, checkpointer configuration, and retry policy.
- **Run service:** Starts/resumes runs, supplies configuration, handles graph results, and exposes safe application-level operations.
- **Streamlit view-models:** Convert adapter/run-service results into page-oriented data and explicit loading/error states.
- **Trace service:** Appends structured events and correlates all outputs to input and decision IDs.

## 3. Approved folder structure

This is the approved repository layout. The files below are proposed implementation locations only; creating them is outside this specification task.

```text
docs/
  specs/member3-spec.md
  design/member3-technical-design.md
app/
  graph/
    state.py
    graph.py
    nodes.py
    routing.py
    retry.py
    service.py
  agents/
    gap_analysis.py
    conflict_detection.py
    member1.py
    member2.py
    checkpoints.py
    mocks.py
  ui/
    app.py
    pages/
      projects.py
      sources.py
      discovery.py
      questions_rules.py
      workflow.py
      traceability.py
    view_models.py
tests/
  graph/
  agents/
  ui/
```

The exact filenames may be refined during implementation, but all Sania's application code belongs under the approved `app/` areas and all tests belong under `tests/`. Member 1 and Member 2 implementations must not be added to these paths by Sania; the `member1.py`, `member2.py`, and `mocks.py` entries represent boundary adapters and test doubles only.

## 4. Graph state

`ProcessFoundryState` is the graph's single state contract. Fields below describe purpose and lifecycle; exact Python annotations and serialization details belong to implementation.

| Field | Purpose |
|---|---|
| `run_id` | Stable identifier for checkpoint lookup, idempotency, and trace correlation. |
| `project_id` | Process/project context; opaque to Sania. |
| `process_type` | Reusable process identifier, such as a scholarship demo configuration. |
| `status` | `created`, `running`, `paused_for_human`, `blocked`, `completed`, or `failed`. |
| `current_node` | Last entered/awaiting graph node for diagnostics and resume display. |
| `input_bundle` | Validated normalized inputs from Member 1/2 adapters. |
| `source_index` | Stable source metadata and evidence lookup index. |
| `discovery_records` | Normalized Member 2 discovery output. |
| `evidence_records` | Normalized Member 2 evidence output. |
| `rule_records` | Normalized Member 2 business-rule output. |
| `gaps` | Gap records, including status and references. |
| `conflicts` | Conflict records, including status and references. |
| `questions` | Outstanding and historical clarification questions. |
| `decisions` | Human responses and approval metadata; append-only by decision ID. |
| `workflow_proposal` | Reviewable proposed digital workflow, never an automatic approval. |
| `pending_question_ids` | Questions that must be answered before routing can continue. |
| `retry_counts` | Per-node attempts for bounded retry decisions. |
| `last_error` | Structured, user-safe error details and error category. |
| `trace_events` | Ordered execution and provenance events. |
| `config` | Materiality, retry, and adapter-mode configuration snapshot. |
| `schema_version` | Contract/checkpoint compatibility marker. |

State updates should be small and merge-safe. Decisions and trace events are append-only; issue records are updated through explicit transitions rather than replacement with an unreferenced object.

## 5. Graph nodes, edges, and routing

### Nodes

1. **Initialize run:** Establish IDs, configuration, status, and trace.
2. **Load inputs:** Read through adapters and capture the input contract version.
3. **Validate and normalize:** Validate Pydantic boundary objects, resolve references into indexes, and reject malformed bundles.
4. **Analyze gaps:** Run deterministic gap detectors over steps, rules, evidence, and required fields.
5. **Detect conflicts:** Compare rules/assertions with cited evidence and with each other; create or update stable conflict records.
6. **Prepare questions:** Convert material unresolved issues into clarification questions with evidence context.
7. **Human review boundary:** Persist/checkpoint and pause when pending questions require a human.
8. **Apply human response:** Validate and append a response, update issue/question status, and emit a trace event.
9. **Re-evaluate:** Re-run only affected analysis or the complete deterministic analysis, preserving stable IDs and decision history.
10. **Build reviewable workflow:** Create a proposal only from supported records and recorded decisions.
11. **Finalize:** Mark completed only when routing rules permit; otherwise mark blocked or paused.
12. **Failure handler:** Normalize terminal errors and expose recovery action.

### Edges and routing rules

```text
START
  -> initialize -> load_inputs -> validate_normalize
  -> [invalid] failure_handler
  -> [valid] analyze_gaps -> detect_conflicts -> prepare_questions
  -> [pending material questions] human_review_boundary
  -> [no pending material questions] build_reviewable_workflow
  -> [human answer applied] re_evaluate -> prepare_questions
  -> finalize -> END
```

Explicit router rules:

- `route_after_validation`: invalid input -> failure; valid input -> gap analysis.
- `route_after_questions`: any unresolved material issue requiring human -> pause; otherwise -> workflow proposal.
- `route_after_human_response`: accepted answer or explicit unknown -> re-evaluate; malformed/stale response -> remain paused with an error; unauthorized approval -> remain paused/blocked.
- `route_after_re_evaluation`: new material questions -> pause; unresolved material conflicts without an authorized decision -> blocked or pause according to configuration; clear -> proposal.
- `route_after_failure`: retry only if the error is categorized transient and the node count is below the configured maximum; otherwise terminal failure.

No router calls an LLM. No router infers approval from confidence alone.

## 6. Gap and conflict detection

### Gap model

Gap types should include missing information, ambiguous information, missing step, missing rule attribute, unsupported assumption, and ordering/dependency gap. A gap key is derived from process context, type, normalized subject, and relevant references so repeated deterministic runs update the same issue.

Detection inputs:

- Required process-step templates from a process configuration.
- Observed discovery steps and relationships.
- Rule required fields and conditions.
- Evidence coverage and reference validity.
- Cross-record ordering and actor dependencies.

Detection output:

- Stable `gap_id`.
- Type, severity, description, status, affected subject.
- Evidence/source/rule references.
- Suggested clarification question, if material.
- Detection version/configuration.

### Conflict model

Conflict types should include rule-versus-evidence, rule-versus-rule, evidence-versus-evidence, and incompatible workflow assertions. Conflict detection compares normalized predicates, scope, effective context, and source references; it does not decide which policy is authoritative.

Every conflict contains:

- Stable `conflict_id`.
- Type and severity.
- Human-readable description of the incompatible claims.
- All participating rule, evidence, discovery, and source references.
- Status such as open, under_review, resolved_by_human, accepted_with_risk, or blocked.
- Decision IDs and timestamps when a human changes its status.
- Detector/version metadata.

An equal or higher-confidence record must not erase a lower-confidence contradictory record. Confidence is displayed and may prioritize questions, but authority is a human/process governance decision.

## 7. HITL pause/resume design

### Pause

The graph creates a checkpoint immediately before the human boundary, with a state version and pending question IDs. The run service returns a pause response containing run ID, question summaries, issue IDs, evidence references, allowed response kinds, and the next action (`submit_answer` or `mark_unknown`).

The Streamlit UI is a client of this response. It must not mutate graph state directly.

### Response contract

A response includes run ID, question ID, question version, actor identity/role from the authorization boundary, response kind (`answer`, `unknown`, or `needs_more_information`), answer payload, optional evidence references, approval intent, and an idempotency key.

The orchestration service validates:

1. The run is paused and the question is outstanding.
2. The question version matches the checkpoint.
3. The actor is permitted to answer and, separately, to approve.
4. Required answer fields are present.
5. The idempotency key has not already been applied.

Unknown/unresolved records a valid human decision but does not resolve a material issue. Approval fields are accepted only from the authorization/persistence interface and only for a human actor meeting the agreed role requirement.

### Resume

The service applies the response once, records the decision, writes a trace event, and resumes the graph using the run's checkpoint/thread identity. Stale, duplicate, unauthorized, or malformed submissions return explicit errors and leave the checkpoint intact.

For the first demo, in-memory checkpoints are sufficient. A production adapter will be selected with Member 1; the graph should depend on a checkpointer interface rather than a specific database.

## 8. Streamlit page responsibilities

| Page | Responsibility |
|---|---|
| **Projects** | List/select projects, create a demo project through an adapter, show run status, and distinguish mock from connected mode. |
| **Sources** | Show source metadata and available evidence references; never implement ingestion or extraction. |
| **Discovery** | Present Member 2 discovery output, step/actor relationships, coverage, and detected discovery gaps. |
| **Questions & Rules** | Show rules, evidence references, conflicts, open questions, answer controls, unknown/unresolved action, and approval state. |
| **Workflow** | Show graph/run status, proposed steps, blockers, retry/failure state, and resume actions. It must label proposals as unapproved. |
| **Traceability** | Traverse source -> evidence -> rule/discovery claim -> gap/conflict -> question -> human decision -> workflow proposal and display execution events. |

All pages use view-models and adapter interfaces. They must support loading, empty, mock, unavailable, validation-error, and permission-error states.

## 9. Interfaces with Member 1 and Member 2

### Member 1 boundary

Sania needs abstract operations for project context, source metadata, checkpoint persistence, human decision persistence, and authorization/actor information. The initial adapter may use in-memory dictionaries and Pydantic fixtures. The design deliberately does not define PostgreSQL tables, FastAPI paths, authentication claims, or endpoint payloads.

The team must agree on:

- Project/run/source identifier semantics.
- Checkpoint ownership and retention.
- Decision idempotency and versioning.
- Human actor and approver authorization contract.
- Error categories and safe user-facing messages.

### Member 2 boundary

Sania needs a versioned read contract for normalized discovery steps, evidence claims/references, and business rules. The graph consumes these outputs and does not call the LLM or extraction pipeline.

The team must agree on:

- Required fields and enum values.
- Stable IDs and source/evidence reference format.
- Confidence representation and meaning.
- Rule scope/effective-date representation.
- Contract version compatibility and invalid-record behavior.

Adapters must translate these contracts into Sania's domain models so changes remain localized.

## 10. Mock-data strategy

- Keep fixtures under a clearly named mock/demo adapter, separate from production adapters.
- Provide at least: clean scholarship example, missing-step example, rule/evidence contradiction example, unresolved-human example, invalid-input example, and transient-failure example.
- Use fictional source text and no real student data.
- Make IDs deterministic and human-readable in fixtures while preserving the same domain shape as future integrations.
- Add a visible “Mock data” indicator to Streamlit.
- Make the mock repository/checkpointer implement the same interfaces expected by future adapters.

## 11. Testing strategy

- **Contract tests:** Pydantic validation, version compatibility, stable IDs, status transitions, and reference integrity.
- **Analysis unit tests:** Pure gap and conflict detector cases, including contradictory and incomplete inputs.
- **Graph tests:** Compile the graph with an in-memory checkpointer; assert every route, pause, resume, retry, blocked, failed, and completed path.
- **HITL tests:** Authorized answer, unknown, stale response, duplicate response, unauthorized approval, and idempotent resume.
- **Adapter contract tests:** Mock adapters satisfy the same protocol as provisional external adapters without calling a network/database.
- **UI tests:** Streamlit page/view-model tests for normal, empty, loading, unavailable, validation, and permission states. Use the project's chosen Streamlit testing mechanism when implementation begins.
- **Regression tests:** Re-run fixed fixtures to ensure issue IDs, references, and routing remain stable.
- **Coverage focus:** Every router branch and every terminal status matters more than a blanket percentage target; the team should set the numerical threshold before implementation.

## 12. Implementation order and dependencies

1. Confirm this specification, issue/status vocabulary, materiality rules, retry policy, and open teammate contracts.
2. Define Pydantic domain contracts and deterministic ID/reference rules. Dependency: decisions from Step 1.
3. Build mock Member 1/Member 2 adapters, fixtures, and in-memory checkpoint/decision stores. Dependency: Step 2.
4. Implement pure gap and conflict detectors. Dependency: normalized contracts and process configuration.
5. Implement graph nodes, explicit routers, failure classification, and bounded retries. Dependency: Steps 3–4.
6. Add checkpoint pause/resume and decision idempotency. Dependency: graph and checkpoint interface.
7. Add run service and traceability projections. Dependency: graph and adapters.
8. Add Streamlit pages in the requested order, starting with Projects and Workflow, then issue review and traceability pages. Dependency: run service/view-models.
9. Add contract, graph-path, HITL, and UI tests; run the smallest relevant test selectors after each stage. Dependency: each implemented surface.
10. Replace mock adapters only after Member 1/Member 2 contracts are reviewed; retain mocks for deterministic regression tests.

No step in this order authorizes implementing Member 1 persistence/API or Member 2 extraction/LLM behavior.

## 13. Decisions requiring confirmation

- Exact Pydantic field names and versioning format for Member 2 outputs.
- Required process-step/rule templates and whether they are supplied per process configuration or by another component.
- Definition of a material issue and which statuses block completion.
- Retry maximum, backoff strategy, and which error categories are retryable.
- Human roles allowed to answer versus approve.
- Checkpoint persistence/retention mechanism for the first demonstrator.
- Stable ID algorithm and whether IDs must remain stable across source revisions.
- Final Streamlit entrypoint and exact module filenames once implementation begins; the application root is already approved as `app/`.
- Minimum test coverage/quality gate and preferred Streamlit test tooling.
