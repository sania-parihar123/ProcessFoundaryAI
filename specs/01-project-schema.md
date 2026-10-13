# SPEC-001: Canonical project schema

## 1. Purpose

This specification defines the canonical project data model for ProcessFoundry AI as described in `ProcessFoundry_AI_Detailed_Implementation_Design.md`. It is the authoritative schema for database, application models, and traceability logic.

The project is process-agnostic and supports any college process that must be analyzed, redesigned, documented, and validated.

## 2. Canonical entity set

The database must include all 16 entities defined in the detailed design:

1. `projects`
2. `documents`
3. `document_sections`
4. `evidence_items`
5. `process_versions`
6. `process_steps`
7. `business_rules`
8. `rule_evidence`
9. `clarification_items`
10. `requirements`
11. `requirement_links`
12. `artifacts`
13. `artifact_links`
14. `test_cases`
15. `approvals`
16. `agent_runs`

## 3. Project entity

### `projects`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique project identifier |
| `name` | `TEXT` | No |  | Must not be empty or whitespace only |
| `process_type` | `TEXT` | No |  | Type of college process |
| `description` | `TEXT` | No |  | High-level project description |
| `status` | `TEXT` | No |  | Current lifecycle status |
| `created_at` | `TIMESTAMPTZ` | No |  | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | No |  | Last update timestamp |

Relationships:
- One project has many documents.
- One project has many evidence items.
- One project has many process versions.
- One project has many business rules.
- One project has many clarification items.
- One project has many requirements.
- One project has many artifacts.
- One project has many test cases.
- One project has many approvals.
- One project has many agent runs.

## 4. Document and evidence entities

### `documents`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique document identifier |
| `project_id` | `TEXT` | No | FK -> `projects.id` | Source project |
| `filename` | `TEXT` | No |  | Original filename |
| `mime_type` | `TEXT` | No |  | File content type |
| `checksum` | `TEXT` | No |  | File integrity identifier |
| `version` | `TEXT` | No |  | Document version |
| `storage_path` | `TEXT` | No |  | Stored location |

### `document_sections`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique section identifier |
| `document_id` | `TEXT` | No | FK -> `documents.id` | Source document |
| `page_number` | `INTEGER` | Yes |  | Page number when available |
| `section_title` | `TEXT` | Yes |  | Section heading when available |
| `text` | `TEXT` | No |  | Extracted text |

### `evidence_items`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique evidence identifier |
| `project_id` | `TEXT` | No | FK -> `projects.id` | Project scope |
| `document_section_id` | `TEXT` | No | FK -> `document_sections.id` | Supporting source section |
| `quote` | `TEXT` | No |  | Supporting evidence text |
| `claim_type` | `TEXT` | No |  | Category of the claim |
| `confidence` | `NUMERIC` | No |  | Confidence score |

Traceability rule:
- Each evidence item must be linked to a real document section and project.
- Evidence is treated as source-grounded claims and not as direct instructions.

## 5. Process model entities

### `process_versions`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique process version identifier |
| `project_id` | `TEXT` | No | FK -> `projects.id` | Parent project |
| `version` | `TEXT` | No |  | Version identifier |
| `as_is_json` | `JSON` | Yes |  | Canonical As-Is process model |
| `to_be_json` | `JSON` | Yes |  | Canonical To-Be model |
| `status` | `TEXT` | No |  | Process version status |

### `process_steps`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique process step identifier |
| `process_version_id` | `TEXT` | No | FK -> `process_versions.id` | Parent process version |
| `step_key` | `TEXT` | No |  | Stable step identifier |
| `name` | `TEXT` | No |  | Step name |
| `actor` | `TEXT` | No |  | Responsible actor or role |
| `step_type` | `TEXT` | No |  | Step category or workflow type |
| `sequence` | `INTEGER` | No |  | Order within the process |

Process ordering rule:
- Each process version must maintain a valid ordered sequence of steps.

## 6. Rule and clarification entities

### `business_rules`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique business rule identifier |
| `project_id` | `TEXT` | No | FK -> `projects.id` | Parent project |
| `rule_key` | `TEXT` | No |  | Stable rule identifier |
| `description` | `TEXT` | No |  | Rule text |
| `condition_json` | `JSON` | Yes |  | Condition metadata |
| `status` | `TEXT` | No |  | Rule approval or lifecycle status |

### `rule_evidence`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `rule_id` | `TEXT` | No | PK, FK -> `business_rules.id` | Supporting rule |
| `evidence_id` | `TEXT` | No | PK, FK -> `evidence_items.id` | Supporting evidence |

This is a link table. The composite primary key prevents duplicate same-rule/same-evidence links.

### `clarification_items`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique clarification identifier |
| `project_id` | `TEXT` | No | FK -> `projects.id` | Parent project |
| `question` | `TEXT` | No |  | Clarification question |
| `reason` | `TEXT` | No |  | Why the question is required |
| `status` | `TEXT` | No |  | Lifecycle status |
| `answer` | `TEXT` | Yes |  | Human response, if any |
| `answered_by` | `TEXT` | Yes |  | Reviewer or approver identity |

Traceability rule:
- Clarification questions are stored independently from rule generation and must be resolved before downstream artifacts are considered approved.

## 7. Requirement and artifact entities

### `requirements`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique requirement identifier |
| `project_id` | `TEXT` | No | FK -> `projects.id` | Parent project |
| `requirement_key` | `TEXT` | No |  | Stable requirement identifier |
| `type` | `TEXT` | No |  | Requirement category |
| `statement` | `TEXT` | No |  | Requirement statement |
| `priority` | `TEXT` | No |  | Priority |
| `status` | `TEXT` | No |  | Requirement lifecycle status |

### `requirement_links`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `source_requirement_id` | `TEXT` | No | PK, FK -> `requirements.id` | Source requirement |
| `target_id` | `TEXT` | No | PK | Target entity ID |
| `link_type` | `TEXT` | No | PK | Relationship type |

This table supports traceability from a requirement to related rules, steps, tests, or artifacts.

### `artifacts`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique artifact identifier |
| `project_id` | `TEXT` | No | FK -> `projects.id` | Parent project |
| `artifact_type` | `TEXT` | No |  | Artifact category |
| `version` | `TEXT` | No |  | Artifact version |
| `content_json` | `JSON` | Yes |  | Structured payload |
| `markdown` | `TEXT` | Yes |  | Markdown export |
| `status` | `TEXT` | No |  | Draft / Needs Review / Approved |

### `artifact_links`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `artifact_id` | `TEXT` | No | PK, FK -> `artifacts.id` | Source artifact |
| `target_type` | `TEXT` | No | PK | Entity type being linked |
| `target_id` | `TEXT` | No | PK | Target entity ID |
| `link_type` | `TEXT` | No | PK | Relationship type |

## 8. Test, approval, and agent run entities

### `test_cases`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique test case identifier |
| `project_id` | `TEXT` | No | FK -> `projects.id` | Parent project |
| `test_key` | `TEXT` | No |  | Stable test identifier |
| `requirement_id` | `TEXT` | No | FK -> `requirements.id` | Linked requirement |
| `scenario` | `TEXT` | No |  | Scenario description |
| `expected_result` | `TEXT` | No |  | Expected outcome |

### `approvals`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique approval identifier |
| `project_id` | `TEXT` | No | FK -> `projects.id` | Parent project |
| `target_type` | `TEXT` | No |  | Type of object being approved |
| `target_id` | `TEXT` | No |  | Object identifier |
| `decision` | `TEXT` | No |  | Approved, rejected, or requested changes |
| `reviewer` | `TEXT` | No |  | Reviewer identity |
| `timestamp` | `TIMESTAMPTZ` | No |  | Approval timestamp |
| `comment` | `TEXT` | Yes |  | Optional reviewer comment |

### `agent_runs`

| Column | Type | Null | Key | Notes |
|---|---|---:|---|---|
| `id` | `TEXT` | No | PK | Unique run identifier |
| `project_id` | `TEXT` | No | FK -> `projects.id` | Parent project |
| `node_name` | `TEXT` | No |  | Agent / node name |
| `status` | `TEXT` | No |  | Execution state |
| `input_summary` | `TEXT` | Yes |  | Summary of inputs |
| `output_ref` | `TEXT` | Yes |  | Reference to output or artifact |
| `error` | `TEXT` | Yes |  | Error or failure details |
| `created_at` | `TIMESTAMPTZ` | No |  | Run creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | No |  | Last update timestamp |

## 9. Referential integrity and relationship rules

The implementation must maintain the following foreign-key rules:

- `documents.project_id` -> `projects.id`
- `document_sections.document_id` -> `documents.id`
- `evidence_items.project_id` -> `projects.id`
- `evidence_items.document_section_id` -> `document_sections.id`
- `process_versions.project_id` -> `projects.id`
- `process_steps.process_version_id` -> `process_versions.id`
- `business_rules.project_id` -> `projects.id`
- `rule_evidence.rule_id` -> `business_rules.id`
- `rule_evidence.evidence_id` -> `evidence_items.id`
- `clarification_items.project_id` -> `projects.id`
- `requirements.project_id` -> `projects.id`
- `requirement_links.source_requirement_id` -> `requirements.id`
- `artifacts.project_id` -> `projects.id`
- `artifact_links.artifact_id` -> `artifacts.id`
- `test_cases.project_id` -> `projects.id`
- `test_cases.requirement_id` -> `requirements.id`
- `approvals.project_id` -> `projects.id`
- `agent_runs.project_id` -> `projects.id`

## 10. Indexing and validation rules

- Primary keys are required for every table.
- Foreign keys must be enforced by the database.
- `projects.name` must be non-empty after trimming whitespace.
- `process_steps.sequence` must be a positive integer or a valid ordering value used by the graph logic.
- `rule_evidence` must reject duplicate `(rule_id, evidence_id)` pairs.
- `requirement_links` must reject duplicate `(source_requirement_id, target_id, link_type)` pairs.
- `artifact_links` must reject duplicate `(artifact_id, target_type, target_id, link_type)` pairs.
- `evidence_items.confidence` must be a valid numeric confidence score within the project’s agreed range.
- All generated traceability links must reference real source, rule, requirement, step, artifact, and test records.

## 11. Traceability requirements

The schema and application logic must support a full source-to-test lineage:

`source document section -> evidence -> business rule -> requirement -> process step -> artifact/test`

Stable IDs must be used for all generated records. Example patterns:
- Evidence: `EVD-001`
- Business rule: `BR-001`
- Requirement: `REQ-001`
- Workflow step: `STEP-001`
- Test: `TEST-001`
- UAT scenario: `UAT-001`

If a source cannot support a generated claim, the implementation must label the result as `Assumption` or `Needs Clarification` rather than inventing a citation.

## 12. Acceptance criteria

The schema is accepted when all of the following are true:

- A project can be created and stored.
- Source documents can be uploaded and linked to a project.
- Extracted sections can be associated with a source document.
- Evidence items can be linked to both a project and a document section.
- Process versions can hold both As-Is and To-Be payloads.
- Process steps can be sequenced and linked to a process version.
- Business rules can be represented with conditions and lifecycle status.
- Requirements can be linked to rule, step, artifact, and test traceability records.
- Clarification items can document unresolved questions and approved answers.
- Artifacts can be generated and linked to related entities.
- Test cases can be tied to specific requirements.
- Approvals can represent human review decisions.
- Agent runs can be logged with inputs, outputs, and failure details.
- The database schema remains consistent with the design document and is not a partial or process-specific variant.

## 13. Status

Canonical and approved as the implementation baseline for this project.
