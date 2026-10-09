# SPEC-002: Database Design

## 1. Goal

Define how ProcessFoundry AI stores projects, uploaded documents, and extracted document content in PostgreSQL.

## 2. Database

* Database name: processfoundry
* Database system: PostgreSQL

## 3. Tables

### 3.1 projects

Purpose: Store information about each process-improvement project.

Fields:

* id — unique project identifier
* name — project name
* process_type — type of college process
* description — project description
* status — current project status
* created_at — creation timestamp
* updated_at — last updated timestamp

### 3.2 documents

Purpose: Store metadata about uploaded source files.

Fields:

* id — unique document identifier
* project_id — project to which the document belongs
* filename — original filename
* mime_type — file content type
* checksum — file integrity identifier
* version — document version
* storage_path — location of the stored file

### 3.3 document_sections

Purpose: Store text extracted from uploaded documents.

Fields:

* id — unique section identifier
* document_id — document from which the section was extracted
* page_number — source page number, when available
* section_title — section heading, when available
* text — extracted text content

## 4. Database Rules

* Each table must have a primary key.
* A document must reference an existing project.
* A document section must reference an existing document.
* Required fields must not accept missing values.
* Foreign keys must maintain relationships between records.
* Project and document timestamps should use a consistent format.

## 5. Acceptance Criteria

* Projects can be stored and retrieved.
* Documents can be associated with the correct project.
* Extracted sections can be associated with their source document.
* Invalid relationships are rejected by the database.
* The schema is consistent with the company design and shared team contracts.

## 6. Dependencies

* SPEC-001: Project Schema
* Company implementation design
* Team-agreed API and data contracts

## 7. Status

Draft — pending team review.
