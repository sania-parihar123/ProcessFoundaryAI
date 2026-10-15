# Sania's Specification: Orchestration, Analysis, Integration, and Streamlit

**Status:** Draft for review  
**Owner:** Sania Parihar
**Date:** 2026-10-09  
**Scope:** Platform orchestration, analysis, integration, and application-shell experience

## 1. Purpose

Sania owns the workflow coordination layer for ProcessFoundry AI. This layer consumes structured discovery and extraction results supplied by Member 2, identifies gaps and contradictions without making unsupported policy choices, integrates teammate-owned clarification, artifact, and audit interfaces, and exposes core project workflow status through Streamlit.

Scholarship processing is the demonstration process. All contracts in this specification must remain process-neutral: a future process may provide different source types, rule categories, actors, or workflow steps without changing the orchestration principles.

## 2. Scope

### In scope

- A Pydantic-defined `ProcessFoundryState` contract for one analysis run.
- LangGraph graph construction, node and edge definitions, workflow execution, explicit Python routing, graph-level error handling, and controlled retries.
- Consumption and validation of structured Member 2 outputs through agreed interfaces.
- Gap analysis for missing, ambiguous, incomplete, or unsequenced information.
- Conflict detection between evidence and business rules, and between mutually incompatible extracted assertions.
- Stable, traceable issue records with status and evidence references.
- Integration of the teammate-owned HITL clarification/approval module at graph pause and resume boundaries.
- Integration of teammate-owned requirements/artifact and traceability/audit interfaces without implementing those modules.
- A Streamlit application shell with Projects, Sources, Discovery, and overall Workflow status pages, plus integration points for teammate-owned interface components.
- Mock/sample adapters and deterministic fixtures until Member 1 and Member 2 integrations exist.
- Unit, contract, graph-path, and Streamlit behavior tests using Pytest.

### Exclusions

- Document ingestion, OCR, embeddings, LLM calls, evidence extraction, As-Is discovery, and business-rule extraction owned by Member 2.
- Authentication, authorization, persistence APIs, PostgreSQL schemas, migrations, and backend endpoints owned by Member 1.
- Clarification question handling, human answer/decision/approval recording, HITL interface components, and HITL resume notification owned by the teammate.
- BRD, FRD, PRD, and SRS generation, templates, formatting, exports, validation, and related tests owned by the teammate.
- Traceability matrices, workflow audit records, traceability validation/reports, traceability interface components, and related tests owned by the teammate.
- Final policy adjudication, automatic approval of applicants or process changes, or legal/compliance certification.
- Production deployment, multi-tenant isolation, distributed workers, queues, Redis, microservices, or external orchestration services.
- React, Node.js, n8n, LiteLLM, CopilotKit, AG-UI, or any other excluded technology.
- Implementing a completed integration before the other members provide a reviewed contract.

## 3. Assumptions and open contracts

1. The repository does not yet contain completed application modules or backend endpoints.
2. Member 2 will provide versioned, structured, Pydantic-compatible outputs for source metadata, evidence references, discovered process steps, and extracted business rules. Exact field names are provisional.
3. Member 1 will provide persistence and project/source/decision interfaces. The graph must not import database models directly; an adapter boundary will be used.
4. A process run has a stable `run_id`; a source item and an evidence item have stable IDs supplied by the producing component.
5. A local in-memory checkpoint and mock repository are acceptable for the demonstration until a persistence adapter is agreed.
6. The teammate-owned HITL module provides clarification/approval operations and notifies the graph when a response is available; Sania owns only graph integration and routing around that module.
7. “Unknown” or “unresolved” is a valid human outcome and must not be converted into approval or a guessed value.
8. Only an explicitly authorized human actor can approve a decision. The AI can recommend, ask, summarize, and route, but cannot approve itself.
9. The teammate-owned artifact and traceability modules expose reviewed interfaces; their internal schemas and implementations are not assumed to exist.
10. Thresholds for materiality, retry counts, and authorized roles remain configuration decisions until the team confirms them.
11. Sania's application code will be organized under `app/graph/`, `app/agents/`, and `app/ui/`; Sania's tests will be organized under `tests/`.

## 4. Functional requirements

### FR-001 — Represent a process run

The system shall represent a run with a stable identifier, process/project context, lifecycle status, current graph node, timestamps, input references, outputs, errors, and an append-only trace of significant actions.

### FR-002 — Validate structured inputs

The system shall validate Member 2 outputs at the orchestration boundary. Invalid, missing, or incompatible records shall produce an explicit validation error and a visible failed/blocked run state; they shall not be silently discarded.

### FR-003 — Build a reusable LangGraph workflow

The graph shall orchestrate analysis in process-neutral stages: initialize, load/validate inputs, normalize references, analyze gaps, detect conflicts, prepare questions, pause for human input when required, apply human responses, produce a reviewable result, and finish or fail.

### FR-004 — Route using explicit Python logic

Routing decisions shall be made by named Python functions using state values and documented rules. The system shall not rely on an LLM to decide whether a gap is resolved, a conflict is safe, a retry is allowed, or a run may finish.

### FR-005 — Identify gaps

The system shall identify missing or unclear information, missing process steps, missing rule attributes, unsupported assumptions, and ordering/dependency gaps. Each gap shall include a stable ID, type, severity, description, status, source/evidence references where available, and a resolution note when resolved.

### FR-006 — Detect conflicts

The system shall detect contradictions between extracted business rules and source evidence, and between extracted assertions that cannot simultaneously be true. Each conflict shall include a stable ID, conflict type, description, all relevant evidence/rule references, severity, status, and decision history.

### FR-007 — Preserve disagreement

The system shall never silently select one conflicting policy or evidence statement. An unresolved conflict must remain visible and must block completion when configured as material.

### FR-008 — Prepare clarification requests for the HITL module

For material gaps and conflicts, the graph shall prepare a versioned clarification request containing a human-readable question, context, supporting references, expected answer shape, affected issue IDs, and status for the teammate-owned HITL module. Sania shall not implement the module's question presentation or answer-recording internals.

### FR-009 — Pause safely at the HITL boundary

When clarification is required, the graph shall persist/checkpoint a resumable state and invoke the agreed HITL interface. The pause request shall identify the run, question IDs, outstanding issues, evidence references, permitted response actions, and graph resume information.

### FR-010 — Consume HITL responses

The graph shall consume an answer, explicit unknown/unresolved response, or request-for-more-information notification through the teammate-owned HITL interface. It shall validate run/question/version correlation and use the returned decision and approval status for routing; the teammate module owns durable response and approval records.

### FR-011 — Enforce approval safety at graph integration

The graph shall reject or block any response indicating non-human/system approval of a material issue. Only an authorized human approval supplied by the teammate-owned HITL module can permit a material issue to be treated as approved/resolved. Sania shall not reimplement approval storage or UI.

### FR-012 — Resume deterministically after HITL notification

After a valid HITL notification, the graph shall load the checkpoint, validate run/question/version and idempotency data, update shared state references, and continue from the correct graph boundary without reapplying the same response.

### FR-013 — Handle errors and retries

Transient, retryable node failures shall use a bounded retry policy with observable attempt counts and backoff configuration. Validation errors, permission errors, malformed human responses, and unresolved policy conflicts shall not be retried as if they were transient failures.

### FR-014 — Integrate artifact-generation interfaces

The graph/application shell shall submit structured requirements and approved inputs to the teammate-owned artifact-generation interface and display returned artifact metadata, validation status, and export references. Sania shall not implement BRD, FRD, PRD, SRS templates, generation, formatting, or exports.

### FR-015 — Integrate traceability and audit interfaces

The graph/application shell shall emit agreed run, node, route, issue, and integration events and consume traceability/audit summaries from the teammate-owned module. Sania shall not implement traceability matrices, audit persistence, validation reports, or duplicate traceability UI.

### FR-016 — Provide the Sania Streamlit application shell

The prototype shall expose Projects, Sources, Discovery, and overall Workflow status pages. It shall mount or link teammate-owned clarification/approval, artifact-generation, and traceability interface components through agreed integration points, without reimplementing their internal functionality.

### FR-017 — Support mock operation

The system shall run end-to-end with deterministic sample data and in-memory checkpoint/repository adapters. Mock mode shall be clearly labeled and shall not be represented as production data.

## 5. Non-functional requirements

- **NFR-001 Reusability:** Domain records and routing rules shall not hard-code scholarship-only names or fields.
- **NFR-002 Traceability:** IDs and references shall be stable within a run and preserved across pause/resume.
- **NFR-003 Determinism:** Given identical validated inputs and human responses, routing and issue IDs shall be reproducible.
- **NFR-004 Safety:** No unresolved material contradiction may be hidden or auto-approved.
- **NFR-005 Type safety:** Boundary objects shall use Pydantic models and explicit types; malformed data shall fail explicitly.
- **NFR-006 Observability:** Node start/end, route, retry, pause, resume, and failure events shall be available in the run trace without exposing secrets.
- **NFR-007 Testability:** Nodes, routers, adapters, issue detectors, integration contracts, and page view-model logic shall be testable without a live LLM, database, or network. Teammate-owned module behavior is covered by that module's tests.
- **NFR-008 Performance:** The prototype shall keep normal sample-run interaction responsive; exact production latency and scale targets are deferred.
- **NFR-009 Accessibility and clarity:** Questions shall present plain-language descriptions, supporting references, and explicit unresolved choices.
- **NFR-010 Privacy:** Sample data shall contain no real student PII; logs and traces shall avoid credentials and unnecessary sensitive content.

## 6. Inputs and expected outputs

### Inputs

- Project/process context and run ID.
- Source metadata and source content references from the Member 1 boundary.
- Member 2 structured discovery output: candidate steps, actors, states, and relationships.
- Member 2 structured evidence output: claims, quotations/locations, confidence, and source references.
- Member 2 structured business-rule output: rule IDs, conditions, actions, scope, effective context, and evidence references.
- Optional prior checkpoint and a validated HITL response notification.
- Configuration: materiality rules, retry limits, and adapter mode.

### Expected outputs

- Validated normalized run state.
- Gap records and conflict records with stable IDs and statuses.
- HITL clarification requests and returned decision/approval references.
- Structured requirements/artifact requests and returned artifact metadata.
- A reviewable workflow proposal only when required material issues are resolved or explicitly accepted by an authorized human.
- Graph events and integration references consumable by the teammate-owned traceability/audit module.
- Explicit terminal status: completed, paused-for-human, blocked, or failed.

## 7. Acceptance criteria

1. A deterministic mock run with no material issues reaches `completed` and exposes its trace.
2. A run containing a material gap creates a HITL clarification request, checkpoint, and visible `paused-for-human` status without implementing the HITL UI or storage.
3. A valid HITL response notification updates shared state references and proceeds without duplicating the response.
4. An unknown/unresolved HITL response preserves the issue and either pauses again or ends blocked according to configured routing.
5. Contradictory rule/evidence records create one stable conflict record with both references; no side is silently selected.
6. A non-human approval response is rejected or blocked at the graph boundary and leaves the issue unapproved.
7. Invalid Member 2 data produces an explicit validation failure and no fabricated result.
8. A transient node error retries only up to the configured bound and records each attempt.
9. A non-retryable error becomes failed/blocked with a useful user-facing message and trace entry.
10. Projects, Sources, Discovery, and Workflow pages render from the agreed adapter/view-model boundary using mock data, without requiring FastAPI or PostgreSQL.
11. Artifact-generation and traceability interface calls use versioned correlation IDs and return explicit success/error states without Sania implementing their internals.
12. Replaying identical inputs produces identical issue IDs and routing outcomes.
13. Automated tests cover the Sania-owned scenarios in Section 9 and pass without external services.

## 8. Error and edge cases

| Case | Required behavior |
|---|---|
| Missing source/evidence reference | Create a validation issue; do not dereference or invent the source. |
| Duplicate input IDs | Reject at the boundary unless the contract explicitly declares them mergeable; report the offending IDs. |
| Empty discovery or rule output | Record a data-availability gap and ask for clarification or additional source material. |
| Same rule ID with changed content | Treat as a version conflict; preserve both versions and block silent overwrite. |
| Contradictory statements with weak evidence | Still record the conflict; confidence affects severity/prioritization, not disappearance. |
| Question answered for an obsolete issue version | Reject as stale and request refresh; do not apply it to the new issue. |
| HITL module returns “unknown” | Preserve unresolved status and route according to materiality; never coerce to false/approved. |
| HITL module returns malformed/stale response | Keep the checkpoint intact, record an integration error, and do not resume. |
| Checkpoint missing or corrupt | Fail/resume visibly with recovery guidance; do not start a new run under the same ID silently. |
| Retry limit exhausted | Mark failed with attempts and last error; require explicit restart/retry action. |
| Streamlit adapter unavailable | Show a clear unavailable state and preserve mock/demo option; do not fabricate live data. |
| Session refresh during pause | Re-read checkpoint and show outstanding questions; response submission must remain idempotent. |
| HITL module reports no authorized approver | Keep the run blocked and identify the required role; AI cannot substitute. |

## 9. Test scenarios

- Validate a complete mock input bundle and assert normalized IDs/references.
- Reject malformed evidence, rule, and discovery records with field-level errors.
- Detect a missing required process step and create the expected gap.
- Detect an ambiguous rule condition and create a clarification question.
- Detect direct contradiction between a rule and cited evidence.
- Detect contradiction between two rules while retaining both references.
- Confirm stable issue IDs across repeated runs.
- Confirm a no-issue graph path reaches completion.
- Confirm a material-issue path pauses at the human boundary.
- Send a valid HITL response notification and verify issue references, graph route, and checkpoint behavior.
- Send unknown/unresolved and verify no approval and correct blocked/paused route.
- Send a stale or duplicate HITL notification and verify idempotent rejection.
- Send an AI/system approval response and verify rejection.
- Inject a transient failure and assert bounded retries and trace entries.
- Inject a validation or permission failure and assert no retry.
- Resume from a persisted checkpoint and verify no duplicate side effects.
- Render Sania's Projects, Sources, Discovery, and Workflow pages with mock adapters and verify empty/loading/error states.
- Verify artifact-generation and traceability integration errors are visible and do not create fabricated outputs.
- Verify graph event payloads contain stable run/node/issue correlation IDs for the teammate-owned traceability module.

## 10. Repository alignment

The approved repository structure is:

```text
app/
  graph/
  agents/
  ui/
tests/
docs/
  specs/
  design/
```

This structure describes ownership and placement only. It does not imply that Member 1's backend or Member 2's extraction implementation already exists.

## 11. Definition of done for Sania

The design is implementation-ready when the team confirms the open contracts and thresholds, Member 1 and Member 2 review the boundary models, the teammate reviews the three transferred-module interfaces, and the acceptance scenarios can be mapped to tests. This document does not authorize implementing the teammate-owned HITL, artifact-generation, or traceability/audit modules.
