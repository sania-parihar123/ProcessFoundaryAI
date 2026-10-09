# Sania Contribution

This directory contains Sania's ProcessFoundry AI work. It is organized as an
isolated contribution area inside the repository while using the existing
virtual environment at the repository root.

## Ownership

Sania owns:

- LangGraph state and orchestration under `app/graph/`
- Gap analysis, conflict detection, and integration adapters under `app/agents/`
- The Streamlit application shell and core Projects, Sources, Discovery, and
  Workflow pages under `app/ui/`
- Tests for Sania-owned functionality and integration contracts under `tests/`

HITL clarification and approval, requirements and artifact generation, and
traceability/workflow audit remain teammate-owned modules. This contribution
directory contains no implementation of those modules.

Member 1's backend and Member 2's document processing, evidence extraction,
As-Is discovery, and business-rule extraction remain outside this directory.

## Current scope

The current implementation contains the process-neutral `ProcessFoundryState`
model in `app/graph/state.py` and focused tests in `tests/test_state.py`.
Graph construction, nodes, routing, retries, analysis services, UI pages, and
external integration adapters will be added only as their specifications are
approved.

## Repository layout

```text
sania-contribution/
  app/
    graph/
    agents/
    ui/
  tests/
  docs/
    specs/sania-spec.md
    design/sania-technical-design.md
  README.md
```

## Python environment

Use the existing root virtual environment. No new environment or dependency
installation is required:

```powershell
cd sania-contribution
..\venv\Scripts\python.exe --version
```

Run commands from `sania-contribution/` so the existing `from app.graph.state
import ...` package imports resolve without path modifications.

## Testing

Run the focused state-model tests:

```powershell
cd sania-contribution
..\venv\Scripts\python.exe -m pytest tests\test_state.py
```

Run all tests currently present:

```powershell
cd sania-contribution
..\venv\Scripts\python.exe -m pytest
```

The tests are local and deterministic. They do not require FastAPI,
PostgreSQL, an LLM, a document parser, or teammate-owned modules.
