# SPEC-001: Project Schema

## 1. Goal

Define the information required to create and store a ProcessFoundry project.

## 2. Required Fields

* Project ID
* Project name
* Project description
* Project status
* Creation timestamp
* Last updated timestamp

## 3. Validation Rules

* Project name must not be empty.
* Project ID must uniquely identify each project.
* Project status must use values agreed upon by the team.
* Timestamps must use a consistent format.

## 4. Acceptance Criteria

* A valid project can be represented by the schema.
* A missing or blank project name is rejected.
* Each project has a unique ID.
* The schema is consistent with the database and API contracts.

## 5. Dependencies

* Company implementation design
* Database specification
* Project API specification

## 6. Status

Draft — pending team review.
