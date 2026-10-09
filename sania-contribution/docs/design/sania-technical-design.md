# Sania's Technical Design: Orchestration, Analysis, Integration, and Streamlit

**Status:** Proposed design for review
**Owner:** Sania Parihar
**Date:** 2026-10-09

## 1. Design goals and assumptions

This design defines Sania's orchestration, analysis, integration, and application-shell layer without assuming that Member 1's backend, Member 2's extraction modules, or the teammate's transferred modules already exist. The implementation will use Pydantic contracts, LangGraph for execution/checkpoint boundaries, explicit Python routing, and Streamlit as the demonstration UI.

The workflow is process-neutral. Scholarship data is a fixture and a demonstration configuration, not a domain model requirement. Integration adapters will isolate provisional contracts from future teammate implementations.

### Explicit assumptions

- Member 2 supplies structured records, not raw LLM responses.
- Member 1 supplies project/source/decision persistence through a reviewed interface.
- Exact external field names, authentication, persistence, and authorization mechanisms are undecided.
- A single-process in-memory implementation is acceptable for the first demonstrator.
- LangGraph's checkpointer is the workflow pause/resume mechanism; its concrete production backend is not selected.

## 2. Component architecture

```text
Sania Streamlit shell
    |
Sania page view-models / application services
    |
Run service ---- Gap + conflict analysis
    |                         |
LangGraph graph -------------+---- Pydantic shared state/contracts
    |                         |
Member 1/2 adapters          |---- Teammate HITL adapter
    |                         |---- Artifact-generation adapter
    +---- Trace/audit event adapter

Teammate-owned modules:
HITL | Requirements/artifacts | Traceability/audit
```

### Responsibilities

- **Sania graph modules:** Own `ProcessFoundryState`, graph construction, nodes, edges, routing, graph-level errors/retries, and teammate-module integration.
- **Sania analysis modules:** Own deterministic gap and conflict detection and stable issue records.
- **Adapters:** Translate Member 1, Member 2, and teammate contracts into shared domain contracts; no direct database or extractor imports in graph nodes.
- **Run service:** Starts/resumes runs, supplies configuration, handles graph results, and invokes teammate interfaces at agreed boundaries.
- **Sania Streamlit shell:** Owns Projects, Sources, Discovery, and overall Workflow status; mounts or links teammate-owned interface components.
- **Teammate-owned modules:** Own HITL handling/approval, requirements and artifact generation, and traceability/workflow audit. Sania consumes their interfaces but does not implement their internals.
- **Graph event adapter:** Publishes observable run/node/route/issue/integration events for the teammate's audit and traceability module; it is not a second traceability implementation.

## 3. Approved folder structure

This is the approved repository layout. The files below are proposed implementation locations only; creating them is outside this specification task.

```text
docs/
  specs/sania-spec.md
  design/sania-technical-design.md
app/
  graph/
    state.py
    graph.py
    nodes.py
    routing.py
    retry.py
    service.py
    contracts.py
  agents/
    gap_analysis.py
    conflict_detection.py
    member1.py
    member2.py
    hitl.py
    artifacts.py
    trace_events.py
    mocks.py
  ui/
    app.py
    pages/
      projects.py
      sources.py
      discovery.py
      workflow.py
    view_models.py
tests/
  graph/
  agents/
  ui/
```

The exact filenames may be refined during implementation, but Sania's application code belongs under the approved `app/` areas and Sania's tests belong under `tests/`. The `member1.py` and `member2.py` entries represent boundary adapters only. The `hitl.py`, `artifacts.py`, and `trace_events.py` entries represent integration adapters/contracts, not implementations of the teammate-owned modules. The teammate owns any clarification, artifact, approval, traceability, audit, and related interface components.

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
| `questions` | Clarification requests and returned question status; produced/maintained through the teammate HITL interface. |
| `decisions` | References to teammate-owned human decisions and approval records; Sania does not own their durable persistence. |
| `workflow_proposal` | Reviewable proposed digital workflow, never an automatic approval; Sania owns graph status, not audit history. |
| `pending_question_ids` | Questions that must be answered before routing can continue. |
| `retry_counts` | Per-node attempts for bounded retry decisions. |
| `last_error` | Structured, user-safe error details and error category. |
| `trace_events` | Ordered graph execution/integration events emitted for the teammate's traceability/audit module. |
| `config` | Materiality, retry, and adapter-mode configuration snapshot. |
| `schema_version` | Contract/checkpoint compatibility marker. |

State updates should be small and merge-safe. Sania owns issue transitions and graph events; teammate-owned decisions, approvals, artifact records, and audit records are represented by references and interface results. No state update may silently overwrite a conflict or human decision.

## 5. Graph nodes, edges, and routing

### Nodes

1. **Initialize run:** Establish IDs, configuration, status, and trace.
2. **Load inputs:** Read through adapters and capture the input contract version.
3. **Validate and normalize:** Validate Pydantic boundary objects, resolve references into indexes, and reject malformed bundles.
4. **Analyze gaps:** Run deterministic gap detectors over steps, rules, evidence, and required fields.
5. **Detect conflicts:** Compare rules/assertions with cited evidence and with each other; create or update stable conflict records.
6. **Prepare HITL request:** Convert material unresolved issues into versioned clarification requests with evidence context for the teammate-owned HITL module.
7. **HITL boundary:** Persist/checkpoint, invoke the HITL interface, and pause when pending questions require a human.
8. **Consume HITL notification:** Validate the returned response/decision reference and approval status; do not record the teammate module's internal decision data.
9. **Re-evaluate:** Re-run only affected analysis or the complete deterministic analysis, preserving stable IDs and decision references.
10. **Prepare artifact request:** Submit structured requirements and approved inputs to the teammate-owned artifact-generation interface.
11. **Publish graph events:** Emit run/node/route/issue/integration events for the teammate-owned traceability/audit interface.
12. **Build reviewable workflow:** Create a proposal only from supported records and returned approval/artifact references.
13. **Finalize:** Mark completed only when routing rules permit; otherwise mark blocked or paused.
14. **Failure handler:** Normalize terminal errors and expose recovery action.

### Edges and routing rules

```text
START
  -> initialize -> load_inputs -> validate_normalize
  -> [invalid] failure_handler
  -> [valid] analyze_gaps -> detect_conflicts -> prepare_questions
  -> [pending material questions] hitl_boundary
  -> [no pending material questions] build_reviewable_workflow
  -> [HITL response notification] re_evaluate -> prepare_hitl_request
  -> finalize -> END
```

Explicit router rules:

- `route_after_validation`: invalid input -> failure; valid input -> gap analysis.
- `route_after_questions`: any unresolved material issue requiring human -> pause; otherwise -> workflow proposal.
- `route_after_hitl_response`: accepted answer or explicit unknown notification -> re-evaluate; malformed/stale response -> remain paused with an error; unauthorized approval -> remain paused/blocked.
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

## 7. HITL integration boundary

The teammate owns clarification handling, human answer recording, unknown/unresolved responses, human decision and approval records, and clarification/approval interface components. Sania owns only the graph boundary, checkpointing, validation of interface results, and routing.

### Graph-to-HITL request

The graph sends a versioned request containing:

- `run_id`, `project_id`, and graph/checkpoint correlation ID.
- Question IDs and question versions.
- Affected gap/conflict issue IDs and current statuses.
- Human-readable question text, expected answer shape, and permitted response kinds.
- Supporting source/evidence/rule references.
- A resume token or thread/checkpoint reference opaque to the UI.

### HITL-to-graph response notification

The teammate module returns or notifies with:

- Request/run/question IDs and versions.
- Response kind: `answer`, `unknown`, or `needs_more_information`.
- Decision/approval record IDs and statuses, not necessarily internal record contents.
- Human actor/authorization result and response timestamp.
- Idempotency key and interface contract version.
- Explicit error/stale/unauthorized status where applicable.

The graph validates that the run is paused, the question is outstanding, versions match, and the notification has not already been applied. Unknown/unresolved never permits automatic approval. A malformed, stale, duplicate, or unauthorized notification leaves the checkpoint intact and routes to an explicit integration error. Sania does not duplicate the teammate's decision store or approval UI.

For the first demo, in-memory checkpoints are sufficient. A production adapter will be selected with Member 1; the graph should depend on a checkpointer interface rather than a specific database.

## 8. Requirements and artifact-generation integration

The teammate owns requirements derivation, BRD/FRD/PRD/SRS generation, templates, formatting, exports, artifact validation, and artifact tests. Sania provides only the graph-owned input projection and consumes results.

### Graph-to-artifact request

The request should contain a contract version, `run_id`, correlation ID, process type, verified fact references, approved decision references, To-Be workflow/process records, and structured requirements candidates. It must identify whether the request is a draft or an authorized generation request.

### Artifact response

The response should contain request/correlation IDs, artifact IDs and types, generation status, validation status/errors, content/export references, source requirement references, and producer/version metadata. A failed or unavailable artifact response must be visible to the user and must not create a fabricated artifact or mark the run completed.

Sania must not create document templates, render documents, export Markdown/PDF/etc., or reproduce artifact validation logic.

## 9. Traceability and workflow-audit integration

The teammate owns traceability links, matrix generation, audit history, decision records, reports, validation, interface components, and related tests. Sania emits graph events and consumes summaries; it does not implement a second traceability system.

### Event contract

Each emitted event should contain:

- Stable `event_id`, `run_id`, and event schema version.
- UTC timestamp, event type, graph node, and lifecycle status.
- Correlation IDs for source, evidence, rule, gap/conflict issue, HITL request/decision, artifact request/artifact, and workflow proposal where applicable.
- Actor category (`system`, `member2`, `human`, or `teammate_module`) without exposing secrets.
- Safe event metadata and explicit error status when relevant.

The event stream is append-only from the graph perspective. The teammate module owns durable audit storage, traceability matrix construction, reports, and validation. Missing or rejected event acknowledgements are explicit integration errors and never silently replaced with local audit logic.

## 10. Streamlit page responsibilities

| Page | Responsibility |
|---|---|
| **Projects** | List/select projects, create a demo project through an adapter, show run status, and distinguish mock from connected mode. |
| **Sources** | Show source metadata and available evidence references; never implement ingestion or extraction. |
| **Discovery** | Present Member 2 discovery output, step/actor relationships, coverage, and detected discovery gaps. |
| **Workflow** | Show graph/run status, proposed steps, blockers, retry/failure state, integration status, and resume actions. It must label proposals as unapproved. |
| **Teammate components** | Mount or link teammate-owned clarification/approval, artifact-generation, and traceability/audit components through agreed interface contracts; Sania owns the shell integration only. |

Sania's pages use view-models and adapter interfaces. They must support loading, empty, mock, unavailable, validation-error, and permission-error states. The teammate owns the internal UI components listed above.

## 11. Interfaces with Member 1 and Member 2

### Member 1 boundary

Sania needs abstract operations for project context, source metadata, checkpoint persistence, human decision persistence, and authorization/actor information. The initial adapter may use in-memory dictionaries and Pydantic fixtures. The design deliberately does not define PostgreSQL tables, FastAPI paths, authentication claims, or endpoint payloads.

The team must agree on:

- Project/run/source identifier semantics.
- Checkpoint ownership and retention.
- Human actor and approver authorization contract at the HITL interface.
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

## 12. Mock-data and integration-fixture strategy

- Keep fixtures under a clearly named mock/demo adapter, separate from production adapters.
- Provide at least: clean scholarship example, missing-step example, rule/evidence contradiction example, HITL unresolved-response example, invalid-input example, transient-failure example, artifact failure example, and trace-event rejection example.
- Use fictional source text and no real student data.
- Make IDs deterministic and human-readable in fixtures while preserving the same domain shape as future integrations.
- Add a visible â€œMock dataâ€ indicator to Streamlit.
- Make mock HITL, artifact, and trace-event adapters implement only the reviewed integration interfaces; they must not be treated as the teammate's completed modules.

## 13. Testing strategy

- **Contract tests:** Pydantic validation, version compatibility, stable IDs, status transitions, and reference integrity.
- **Analysis unit tests:** Pure gap and conflict detector cases, including contradictory and incomplete inputs.
- **Graph tests:** Compile the graph with an in-memory checkpointer; assert every route, pause, resume, retry, blocked, failed, and completed path.
- **HITL integration tests:** Valid response notification, unknown, stale response, duplicate response, unauthorized approval, and idempotent graph resume. Internal HITL behavior is tested by the teammate.
- **Artifact integration tests:** Structured request/response, validation failure, unavailable interface, correlation IDs, and no fabricated output. Generation internals are tested by the teammate.
- **Trace/audit integration tests:** Event schema, stable IDs, append-only emission, rejection/error handling, and summary consumption. Matrix/audit internals are tested by the teammate.
- **Adapter contract tests:** Mock Member 1/Member 2 and teammate adapters satisfy the agreed protocols without calling a network/database.
- **UI tests:** Sania's Projects, Sources, Discovery, and Workflow page/view-model tests for normal, empty, loading, unavailable, validation, and permission states. Teammate-owned interface components are tested by the teammate.
- **Regression tests:** Re-run fixed fixtures to ensure issue IDs, references, and routing remain stable.
- **Coverage focus:** Every router branch and every terminal status matters more than a blanket percentage target; the team should set the numerical threshold before implementation.

## 14. Implementation order and dependencies

1. Confirm this specification, issue/status vocabulary, materiality rules, retry policy, and open teammate contracts.
2. Define Pydantic domain contracts and deterministic ID/reference rules. Dependency: decisions from Step 1.
3. Build mock Member 1/Member 2 adapters, fixtures, and in-memory checkpoint/decision stores. Dependency: Step 2.
4. Implement pure gap and conflict detectors. Dependency: normalized contracts and process configuration.
5. Implement graph nodes, explicit routers, failure classification, and bounded retries. Dependency: Steps 3â€“4.
6. Add checkpoint pause/resume and HITL interface notification handling. Dependency: graph and reviewed HITL contract.
7. Add artifact-generation and trace/audit event adapters. Dependency: reviewed teammate contracts.
8. Add run service and graph-status projections. Dependency: graph and adapters.
9. Add Sania's Streamlit pages and mount/link teammate-owned components. Dependency: run service, view-models, and interface contracts.
10. Add contract, graph-path, integration, and UI tests; run the smallest relevant test selectors after each stage. Dependency: each implemented surface.
11. Replace mock adapters only after Member 1/Member 2 and teammate contracts are reviewed; retain mocks for deterministic regression tests.

No step in this order authorizes implementing Member 1 persistence/API, Member 2 extraction/LLM behavior, or the teammate-owned HITL, artifact-generation, or traceability/audit modules.

## 15. Decisions requiring confirmation

- Exact Pydantic field names and versioning format for Member 2 outputs.
- Required process-step/rule templates and whether they are supplied per process configuration or by another component.
- Definition of a material issue and which statuses block completion.
- Retry maximum, backoff strategy, and which error categories are retryable.
- Human roles allowed to answer versus approve.
- Checkpoint persistence/retention mechanism for the first demonstrator.
- Stable ID algorithm and whether IDs must remain stable across source revisions.
- Final Streamlit entrypoint and exact module filenames once implementation begins; the application root is already approved as `app/`.
- Minimum test coverage/quality gate and preferred Streamlit test tooling.
- HITL request/notification schema, versioning, idempotency, and resume-token ownership.
- Artifact request/response schema, supported artifact types, export references, and validation/error semantics.
- Graph event schema, acknowledgement behavior, retention, and which component owns audit persistence.
- Streamlit mounting/linking mechanism for teammate-owned interface components.
