Status: DRAFT. AI-generated, not approved.
Project ID: demo-project
Schema version: 0.1

# Functional Requirements Document (FRD)

## System overview

The Merit Excellence Scholarship supports students of Riverdale Institute of Technology who show strong academic results and need financial help. This document describes how a student applies, how the application is checked, and how the scholarship is awarded.

## Actors and roles

- student
- scholarship clerk
- Head of Department (HOD)
- Scholarship Committee
- Accounts Office
- Each selected student

## Functional requirements

| ID | Statement | Status | Rule IDs | Evidence IDs |
|---|---|---|---|---|
| demo-project-REQ-001 | The system shall enforce: Only eligible students may apply for the scholarship. | draft | demo-project-BR-001 | demo-project-EVD-002 |
| demo-project-REQ-002 | The system shall enforce: A student must be enrolled in a full-time undergraduate programme at the institute. | draft | demo-project-BR-002 | demo-project-EVD-003 |
| demo-project-REQ-003 | The system shall enforce: The student must have a cumulative grade point average (CGPA) of at least 8.0 in the previous academic year. | draft | demo-project-BR-003 | demo-project-EVD-004 |
| demo-project-REQ-004 | The system shall enforce: The annual family income of the student must not exceed 5,00,000 rupees. | draft | demo-project-BR-004 | demo-project-EVD-005 |
| demo-project-REQ-005 | The system shall enforce: Students who have already received another scholarship from the institute in the same academic year cannot apply. | draft | demo-project-BR-005 | demo-project-EVD-006 |
| demo-project-REQ-006 | The system shall enforce: Applications must be submitted before 31 March of each year. | draft | demo-project-BR-006 | demo-project-EVD-007 |
| demo-project-REQ-007 | The system shall enforce: Applications received after this date will not be accepted. | draft | demo-project-BR-007 | demo-project-EVD-008 |
| demo-project-REQ-008 | The system shall enforce: The online application portal opens on 1 February. | draft | demo-project-BR-008 | demo-project-EVD-020 |
| demo-project-REQ-009 | The system shall enforce: The last date to submit the scholarship application is 15 April. | draft | demo-project-BR-009 | demo-project-EVD-021 |
| demo-project-REQ-010 | The system shall enforce: Students are informed about the result through the portal. | draft | demo-project-BR-010 | demo-project-EVD-024 |
| demo-project-REQ-011 | The system shall enforce: Students who are not selected are not sent any separate message. | draft | demo-project-BR-011 | demo-project-EVD-025 |
| demo-project-REQ-012 | The system shall enforce: Questions about the scholarship should be sent to the Scholarship Office of the institute. | draft | demo-project-BR-012 | demo-project-EVD-026 |

## Workflow

1. Fill online application form — student
2. Upload required documents — student
3. Check form and documents — scholarship clerk
4. Return incomplete applications — actor not stated
5. Verify form — actor not stated
6. Check documents for genuineness — scholarship clerk
7. Review application and recommend — Head of Department (HOD)
8. Review applications and select awardees — Scholarship Committee
9. Transfer scholarship amount — Accounts Office
10. Receive scholarship amount — Each selected student
11. Pay amount in single instalment — actor not stated
12. Meet and display awardees list — Scholarship Committee

## Open questions

- Who performs this step: Return incomplete applications? Reason: actor not stated in source (Related: demo-project-STEP-004)
- Who performs this step: Verify form? Reason: actor not stated in source (Related: demo-project-STEP-005)
- Who performs this step: Pay amount in single instalment? Reason: actor not stated in source (Related: demo-project-STEP-011)

## Permissions

Not stated in the source documents. Needs clarification.

## Acceptance criteria

Not stated in the source documents. Needs clarification.