# SPEC-002: Database design

## 1. Goal

Define the PostgreSQL schema and rules required to store ProcessFoundry AI projects, uploaded documents, extracted evidence, workflow versions, rules, requirements, artifacts, tests, approvals, and run history. This specification complements `SPEC-001` and matches the implementation design as the canonical source of truth.

## 2. Database characteristics

- Database platform: PostgreSQL
- Initial schema: complete model for all entities in the design document
- Fresh setup: create all tables in one initial migration or equivalent schema file
- Upgrade path: safe additive migration for existing databases that are missing tables or columns
- Constraint behavior: enforce foreign keys, uniqueness, and non-empty required values

## 3. Canonical table list

The complete database schema must include these 16 tables:

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

## 4. Table definitions

### 4.1 `projects`

Purpose: Store one redesign project for a general college process.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique project identifier |
| `name` | `TEXT` | NOT NULL | Must not be empty or whitespace only |
| `process_type` | `TEXT` | NOT NULL | e.g. admissions, exam, scholarship |
| `description` | `TEXT` | NOT NULL | Detailed project description |
| `status` | `TEXT` | NOT NULL | Lifecycle status |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | Creation time |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | Last modification time |

Constraints:
- `CHECK (btrim(name) <> '')`

### 4.2 `documents`

Purpose: Storage metadata for uploaded source files.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique document identifier |
| `project_id` | `TEXT` | FK -> `projects.id`, NOT NULL | Parent project |
| `filename` | `TEXT` | NOT NULL | Original filename |
| `mime_type` | `TEXT` | NOT NULL | File type |
| `checksum` | `TEXT` | NOT NULL | Integrity hash |
| `version` | `TEXT` | NOT NULL | Document version |
| `storage_path` | `TEXT` | NOT NULL | Stored file location |

### 4.3 `document_sections`

Purpose: Extracted text sections from source files.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique section identifier |
| `document_id` | `TEXT` | FK -> `documents.id`, NOT NULL | Parent document |
| `page_number` | `INTEGER` | NULL allowed | Page number if available |
| `section_title` | `TEXT` | NULL allowed | Heading if available |
| `text` | `TEXT` | NOT NULL | Extracted content |

### 4.4 `evidence_items`

Purpose: Candidate facts and statements derived from document sections.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique evidence identifier |
| `project_id` | `TEXT` | FK -> `projects.id`, NOT NULL | Parent project |
| `document_section_id` | `TEXT` | FK -> `document_sections.id`, NOT NULL | Source section |
| `quote` | `TEXT` | NOT NULL | Citational sample text |
| `claim_type` | `TEXT` | NOT NULL | Claim category |
| `confidence` | `NUMERIC` | NOT NULL | Confidence value |

### 4.5 `process_versions`

Purpose: Versioned As-Is and To-Be process definitions.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique process version identifier |
| `project_id` | `TEXT` | FK -> `projects.id`, NOT NULL | Parent project |
| `version` | `TEXT` | NOT NULL | Version number or label |
| `as_is_json` | `JSON` | NULL allowed | As-Is process payload |
| `to_be_json` | `JSON` | NULL allowed | To-Be process payload |
| `status` | `TEXT` | NOT NULL | Version lifecycle status |

### 4.6 `process_steps`

Purpose: Ordered workflow steps within a process version.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique step identifier |
| `process_version_id` | `TEXT` | FK -> `process_versions.id`, NOT NULL | Parent version |
| `step_key` | `TEXT` | NOT NULL | Stable, unique step key |
| `name` | `TEXT` | NOT NULL | Human-readable step name |
| `actor` | `TEXT` | NOT NULL | Participant or role |
| `step_type` | `TEXT` | NOT NULL | Step kind |
| `sequence` | `INTEGER` | NOT NULL | Step ordering |

### 4.7 `business_rules`

Purpose: Candidate business rules and conditions grounded in evidence.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique rule identifier |
| `project_id` | `TEXT` | FK -> `projects.id`, NOT NULL | Parent project |
| `rule_key` | `TEXT` | NOT NULL | Stable rule key |
| `description` | `TEXT` | NOT NULL | Rule statement |
| `condition_json` | `JSON` | NULL allowed | Conditional logic or metadata |
| `status` | `TEXT` | NOT NULL | Lifecycle or approval status |

### 4.8 `rule_evidence`

Purpose: Link business rules to evidence records.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `rule_id` | `TEXT` | PK, FK -> `business_rules.id`, NOT NULL | Rule identifier |
| `evidence_id` | `TEXT` | PK, FK -> `evidence_items.id`, NOT NULL | Evidence identifier |

This is a composition table with a composite primary key.

### 4.9 `clarification_items`

Purpose: Requests for missing or conflicting facts during discovery.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique clarification record |
| `project_id` | `TEXT` | FK -> `projects.id`, NOT NULL | Parent project |
| `question` | `TEXT` | NOT NULL | Clarification question |
| `reason` | `TEXT` | NOT NULL | Why this matters |
| `status` | `TEXT` | NOT NULL | Current status |
| `answer` | `TEXT` | NULL allowed | Human answer |
| `answered_by` | `TEXT` | NULL allowed | Reviewer identity |

### 4.10 `requirements`

Purpose: Requirements generated from the approved process model.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique requirement identifier |
| `project_id` | `TEXT` | FK -> `projects.id`, NOT NULL | Parent project |
| `requirement_key` | `TEXT` | NOT NULL | Stable requirement key |
| `type` | `TEXT` | NOT NULL | Functional or other category |
| `statement` | `TEXT` | NOT NULL | Requirement text |
| `priority` | `TEXT` | NOT NULL | Priority |
| `status` | `TEXT` | NOT NULL | Lifecycle status |

### 4.11 `requirement_links`

Purpose: Traceability links between requirements and related entities.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `source_requirement_id` | `TEXT` | PK, FK -> `requirements.id`, NOT NULL | Source requirement |
| `target_id` | `TEXT` | PK, NOT NULL | Target entity identifier |
| `link_type` | `TEXT` | PK, NOT NULL | Relationship type |

This is a composite primary key table. It supports links to rules, steps, artifacts, or tests without requiring a separate target table.

### 4.12 `artifacts`

Purpose: Generated documents and structured outputs.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique artifact identifier |
| `project_id` | `TEXT` | FK -> `projects.id`, NOT NULL | Parent project |
| `artifact_type` | `TEXT` | NOT NULL | Artifact category |
| `version` | `TEXT` | NOT NULL | Artifact version |
| `content_json` | `JSON` | NULL allowed | Structured JSON payload |
| `markdown` | `TEXT` | NULL allowed | Human-readable export |
| `status` | `TEXT` | NOT NULL | Draft or approval state |

### 4.13 `artifact_links`

Purpose: Link artifacts to related project entities.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `artifact_id` | `TEXT` | PK, FK -> `artifacts.id`, NOT NULL | Source artifact |
| `target_type` | `TEXT` | PK, NOT NULL | Target entity type |
| `target_id` | `TEXT` | PK, NOT NULL | Target entity ID |
| `link_type` | `TEXT` | PK, NOT NULL | Relationship type |

### 4.14 `test_cases`

Purpose: Test scenarios linked to requirements.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique test identifier |
| `project_id` | `TEXT` | FK -> `projects.id`, NOT NULL | Parent project |
| `test_key` | `TEXT` | NOT NULL | Stable test identifier |
| `requirement_id` | `TEXT` | FK -> `requirements.id`, NOT NULL | Linked requirement |
| `scenario` | `TEXT` | NOT NULL | Scenario description |
| `expected_result` | `TEXT` | NOT NULL | Expected result |

### 4.15 `approvals`

Purpose: Human decisions and sign-off records.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique approval record |
| `project_id` | `TEXT` | FK -> `projects.id`, NOT NULL | Parent project |
| `target_type` | `TEXT` | NOT NULL | Object type being approved |
| `target_id` | `TEXT` | NOT NULL | Object identifier |
| `decision` | `TEXT` | NOT NULL | Approved/rejected/request changes |
| `reviewer` | `TEXT` | NOT NULL | Identity of reviewer |
| `timestamp` | `TIMESTAMPTZ` | NOT NULL | Decision time |
| `comment` | `TEXT` | NULL allowed | Reviewer notes |

### 4.16 `agent_runs`

Purpose: Audit trail of orchestration and agent steps.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `TEXT` | PK, NOT NULL | Unique run identifier |
| `project_id` | `TEXT` | FK -> `projects.id`, NOT NULL | Parent project |
| `node_name` | `TEXT` | NOT NULL | Agent or graph node |
| `status` | `TEXT` | NOT NULL | Current state |
| `input_summary` | `TEXT` | NULL allowed | Input description |
| `output_ref` | `TEXT` | NULL allowed | Output or artifact reference |
| `error` | `TEXT` | NULL allowed | Error text |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | Run creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | Last update timestamp |

## 5. Foreign key graph

The schema must support the following relationships:

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

## 6. Index strategy

Recommended indexes for common query access patterns:

- `documents(project_id)`
- `document_sections(document_id)`
- `evidence_items(project_id, document_section_id)`
- `process_versions(project_id)`
- `process_steps(process_version_id, sequence)`
- `business_rules(project_id)`
- `rule_evidence(rule_id)`
- `rule_evidence(evidence_id)`
- `clarification_items(project_id, status)`
- `requirements(project_id)`
- `requirement_links(source_requirement_id)`
- `artifacts(project_id, artifact_type)`
- `artifact_links(artifact_id)`
- `test_cases(project_id, requirement_id)`
- `approvals(project_id, target_type, target_id)`
- `agent_runs(project_id, created_at)`

## 7. Data integrity and validation constraints

- `projects.name` must be trimmed and non-empty.
- All primary keys are required and unique.
- Composite keys must prevent duplicate links.
- `process_steps.sequence` must be stored in deterministic ordering.
- `evidence_items.confidence` must be numeric and within a project-defined confidence range.
- JSON columns must store valid structured data for the As-Is and To-Be models, business-rule conditions, and artifact content.
- A generated claim must not be accepted without a valid evidence link or explicit `Assumption` / `Needs Clarification` label.

## 8. Traceability model

The database must support these link chains without ambiguity:

- source document -> evidence item
- evidence item -> business rule
- business rule -> requirement
- requirement -> process step or artifact
- process step -> workflow artifact
- requirement -> test case
- artifact -> related requirement or process model

This is the canonical traceability rule for the project.

## 9. Migration policy

- Fresh database creation should include every table in the initial schema.
- Existing databases should receive additive changes only when required.
- Do not drop existing tables or data during a normal upgrade.
- If a database already contains the prior partial schema, use a safe migration strategy that adds missing columns and tables without wiping user data.
- Alembic revisions must be applied in order and must not conflict with existing history.

## 10. Acceptance criteria

The database design is complete when:

- All 16 entities are present in the initial schema.
- Every entity has the required key fields and relationships described in the design.
- Primary and foreign keys enforce the intended integrity.
- Traceability chains can be queried via standard relational joins.
- Existing partial database implementations are aligned with the design, not a stale or narrower schema.

## 11. Status

The canonical database specification for ProcessFoundry AI is approved and aligned with the detailed design document.
