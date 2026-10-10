# SPEC-001: Project Schema

## 1. Goal

Define the information required to create and store a ProcessFoundry project.

## 2. Required Fields

* Project ID (`id`)
* Project name (`name`)
* Process type (`process_type`)
* Project description (`description`)
* Project status (`status`)
* Creation timestamp (`created_at`)
* Last updated timestamp (`updated_at`)

## 3. Validation Rules

* Project ID must uniquely identify each project.
* Project name must not be empty.
* Project status must use values agreed upon by the team.
* Timestamps must use a consistent format.
* Field definitions must remain consistent with the company implementation design and database specification.

## 4. Acceptance Criteria

* A valid project can be represented by the schema.
* A missing or blank project name is rejected.
* Each project has a unique ID.
* Project details can be stored and retrieved.
* The schema is consistent with the database and API contracts.

## 5. Dependencies

* Company implementation design
* SPEC-002: Database Design
* Project API specification

## 6. Status

Draft - pending team review.
