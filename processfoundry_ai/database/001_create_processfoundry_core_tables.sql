BEGIN;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
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

COMMIT;
