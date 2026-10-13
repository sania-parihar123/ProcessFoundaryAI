BEGIN;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL CONSTRAINT projects_name_check CHECK (btrim(name) <> ''),
    process_type TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    checksum TEXT NOT NULL,
    version TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    CONSTRAINT fk_documents_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS document_sections (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page_number INTEGER,
    section_title TEXT,
    text TEXT NOT NULL,
    CONSTRAINT fk_document_sections_document
        FOREIGN KEY (document_id)
        REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    document_section_id TEXT NOT NULL,
    quote TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    confidence NUMERIC NOT NULL,
    CONSTRAINT fk_evidence_items_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id),
    CONSTRAINT fk_evidence_items_document_section
        FOREIGN KEY (document_section_id)
        REFERENCES document_sections(id)
);

CREATE TABLE IF NOT EXISTS process_versions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    version TEXT NOT NULL,
    as_is_json JSON,
    to_be_json JSON,
    status TEXT NOT NULL,
    CONSTRAINT fk_process_versions_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS process_steps (
    id TEXT PRIMARY KEY,
    process_version_id TEXT NOT NULL,
    step_key TEXT NOT NULL,
    name TEXT NOT NULL,
    actor TEXT NOT NULL,
    step_type TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    CONSTRAINT fk_process_steps_process_version
        FOREIGN KEY (process_version_id)
        REFERENCES process_versions(id)
);

CREATE TABLE IF NOT EXISTS business_rules (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    rule_key TEXT NOT NULL,
    description TEXT NOT NULL,
    condition_json JSON,
    status TEXT NOT NULL,
    CONSTRAINT fk_business_rules_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS rule_evidence (
    rule_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    PRIMARY KEY (rule_id, evidence_id),
    CONSTRAINT fk_rule_evidence_business_rule
        FOREIGN KEY (rule_id)
        REFERENCES business_rules(id),
    CONSTRAINT fk_rule_evidence_evidence_item
        FOREIGN KEY (evidence_id)
        REFERENCES evidence_items(id)
);

CREATE TABLE IF NOT EXISTS clarification_items (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    question TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    answer TEXT,
    answered_by TEXT,
    CONSTRAINT fk_clarification_items_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS requirements (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    requirement_key TEXT NOT NULL,
    type TEXT NOT NULL,
    statement TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    CONSTRAINT fk_requirements_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS requirement_links (
    source_requirement_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    link_type TEXT NOT NULL,
    PRIMARY KEY (source_requirement_id, target_id, link_type),
    CONSTRAINT fk_requirement_links_source_requirement
        FOREIGN KEY (source_requirement_id)
        REFERENCES requirements(id)
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    version TEXT NOT NULL,
    content_json JSON,
    markdown TEXT,
    status TEXT NOT NULL,
    CONSTRAINT fk_artifacts_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS artifact_links (
    artifact_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    link_type TEXT NOT NULL,
    PRIMARY KEY (artifact_id, target_type, target_id, link_type),
    CONSTRAINT fk_artifact_links_source_artifact
        FOREIGN KEY (artifact_id)
        REFERENCES artifacts(id)
);

CREATE TABLE IF NOT EXISTS test_cases (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    test_key TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    scenario TEXT NOT NULL,
    expected_result TEXT NOT NULL,
    CONSTRAINT fk_test_cases_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id),
    CONSTRAINT fk_test_cases_requirement
        FOREIGN KEY (requirement_id)
        REFERENCES requirements(id)
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    comment TEXT,
    CONSTRAINT fk_approvals_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    node_name TEXT NOT NULL,
    status TEXT NOT NULL,
    input_summary TEXT,
    output_ref TEXT,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_agent_runs_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_document_sections_document_id ON document_sections(document_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_project_id ON evidence_items(project_id, document_section_id);
CREATE INDEX IF NOT EXISTS idx_process_versions_project_id ON process_versions(project_id);
CREATE INDEX IF NOT EXISTS idx_process_steps_process_version_id ON process_steps(process_version_id, sequence);
CREATE INDEX IF NOT EXISTS idx_business_rules_project_id ON business_rules(project_id);
CREATE INDEX IF NOT EXISTS idx_rule_evidence_rule_id ON rule_evidence(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_evidence_evidence_id ON rule_evidence(evidence_id);
CREATE INDEX IF NOT EXISTS idx_clarification_items_project_id ON clarification_items(project_id, status);
CREATE INDEX IF NOT EXISTS idx_requirements_project_id ON requirements(project_id);
CREATE INDEX IF NOT EXISTS idx_requirement_links_source_requirement_id ON requirement_links(source_requirement_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_project_id ON artifacts(project_id, artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifact_links_artifact_id ON artifact_links(artifact_id);
CREATE INDEX IF NOT EXISTS idx_test_cases_project_id ON test_cases(project_id, requirement_id);
CREATE INDEX IF NOT EXISTS idx_approvals_project_id ON approvals(project_id, target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_project_id ON agent_runs(project_id, created_at);

COMMIT;
