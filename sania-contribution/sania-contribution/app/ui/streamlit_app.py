"""Streamlit presentation for ProcessFoundry workflow discovery."""

from __future__ import annotations

from typing import Any

from app.agents.ingestion_service import ingest_documents
from app.ui.mock_adapter import get_all_demo_runs
from app.ui.view_models import ingestion_view_model, workflow_view_model


def main() -> None:
    """Render the local ProcessFoundry discovery workspace."""

    import streamlit as st

    st.set_page_config(
        page_title="ProcessFoundry AI",
        page_icon=":material/account_tree:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_theme(st)
    navigation = _render_sidebar(st)

    if navigation == "Projects":
        _render_projects_page(st)
        return

    st.markdown(
        '<div class="eyebrow">PROCESS DISCOVERY WORKSPACE</div>',
        unsafe_allow_html=True,
    )
    st.title("Turn process documents into a reviewable workflow")
    st.caption(
        "Extract evidence, surface gaps and conflicts, and assemble a "
        "provenance-backed proposal without silently resolving policy."
    )

    mode = st.radio(
        "Workspace mode",
        ["Analyze uploaded documents", "Synthetic demo"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if mode == "Analyze uploaded documents":
        _render_upload_analysis(st)
    else:
        _render_demo_workspace(st)


def _apply_theme(st: Any) -> None:
    st.markdown(
        """
        <style>
        :root {
            --pf-navy: #0b1f3a;
            --pf-navy-soft: #15345d;
            --pf-blue: #2f6fed;
            --pf-ink: #172033;
            --pf-muted: #667085;
            --pf-line: #e4e7ec;
            --pf-panel: #ffffff;
            --pf-canvas: #f6f8fb;
        }
        .stApp {
            background: var(--pf-canvas);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1f3a 0%, #102b4f 100%);
            border-right: 1px solid #17365f;
        }
        [data-testid="stSidebar"] * {
            color: #e8eff8;
        }
        [data-testid="stSidebar"] .stRadio label {
            color: #d7e3f3;
        }
        .pf-brand {
            padding: 0.35rem 0.2rem 1.5rem;
        }
        .pf-brand-mark {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.2rem;
            height: 2.2rem;
            margin-right: 0.55rem;
            border-radius: 0.7rem;
            background: #2f6fed;
            color: white;
            font-size: 1.15rem;
            font-weight: 700;
            vertical-align: middle;
        }
        .pf-brand-name {
            color: white;
            font-size: 1.08rem;
            font-weight: 700;
            vertical-align: middle;
        }
        .pf-brand-subtitle {
            margin: 0.65rem 0 0;
            color: #9db4d0;
            font-size: 0.78rem;
            line-height: 1.45;
        }
        .eyebrow {
            color: #2f6fed;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            margin-bottom: 0.35rem;
        }
        .section-kicker {
            color: #667085;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .status-pill {
            display: inline-block;
            padding: 0.2rem 0.58rem;
            border-radius: 999px;
            background: #eef4ff;
            color: #2458bd;
            font-size: 0.78rem;
            font-weight: 650;
        }
        .demo-pill {
            background: #fff4e5;
            color: #9a5b00;
        }
        .warning-card {
            padding: 0.85rem 1rem;
            border: 1px solid #f2c46d;
            border-radius: 0.7rem;
            background: #fffaf0;
            color: #7a4b00;
        }
        .step-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.75rem;
            height: 1.75rem;
            margin-right: 0.55rem;
            border-radius: 50%;
            background: #eaf1ff;
            color: #2458bd;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar(st: Any) -> str:
    with st.sidebar:
        st.markdown(
            """
            <div class="pf-brand">
              <span class="pf-brand-mark">P</span>
              <span class="pf-brand-name">ProcessFoundry AI</span>
              <p class="pf-brand-subtitle">
                Evidence-led process discovery for complex organizations.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("WORKSPACE")
        navigation = st.radio(
            "Workspace navigation",
            ["Discovery", "Projects", "Sources", "Workflow"],
            index=0,
            label_visibility="collapsed",
        )
        st.markdown("")
        st.caption("ABOUT THIS BUILD")
        st.caption(
            "Local, in-memory analysis. No persistence, authentication, "
            "live backend, or automatic approval is connected."
        )
    return navigation


def _render_projects_page(st: Any) -> None:
    st.markdown('<div class="eyebrow">PROJECTS</div>', unsafe_allow_html=True)
    st.title("Projects")
    st.caption(
        "Create lightweight project records for this session. Temporary "
        "storage only — projects are not saved to a database."
    )

    if "projects" not in st.session_state:
        st.session_state.projects = []

    with st.form("project_form", clear_on_submit=True):
        project_name = st.text_input("Project Name")
        process_type = st.text_input("Process Type")
        description = st.text_area("Description")
        submitted = st.form_submit_button(
            "Save project",
            type="primary",
            icon=":material/add:",
        )

    if submitted:
        missing_fields = []
        if not project_name.strip():
            missing_fields.append("Project Name")
        if not process_type.strip():
            missing_fields.append("Process Type")

        if missing_fields:
            st.error(
                "Please provide: " + ", ".join(missing_fields) + ".",
                icon=":material/error:",
            )
        else:
            st.session_state.projects.append(
                {
                    "Project Name": project_name.strip(),
                    "Process Type": process_type.strip(),
                    "Description": description.strip(),
                }
            )
            st.success("Project saved for this session.", icon=":material/check:")

    st.markdown("### Saved projects")
    if st.session_state.projects:
        st.dataframe(
            st.session_state.projects,
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No projects saved in this session yet.")


def _render_demo_workspace(st: Any) -> None:
    st.markdown(
        '<div class="warning-card">Synthetic demo data — examples are '
        "not connected to a live backend.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("### Explore a sample process")
    demos = get_all_demo_runs()
    selected_demo = st.selectbox(
        "Synthetic process",
        demos,
        format_func=lambda run: run.config.get("demo_label", run.process_type),
        label_visibility="collapsed",
    )
    _render_workflow_workspace(st, workflow_view_model(selected_demo))


def _render_upload_analysis(st: Any) -> None:
    st.markdown(
        '<div class="status-pill">LOCAL ANALYSIS</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Analyze uploaded documents")
    st.caption(
        "Upload policy and process documents to create a traceable draft "
        "workflow. Files are processed in memory for this session."
    )

    with st.container(border=True):
        input_columns = st.columns([1, 1, 1.6], vertical_alignment="bottom")
        with input_columns[0]:
            process_type = st.text_input(
                "Process identity",
                value="general-process",
            )
        with input_columns[1]:
            process_description = st.text_input(
                "Process description",
                value="",
                help="Optional context retained with this analysis run.",
            )
        with input_columns[2]:
            uploads = st.file_uploader(
                "Upload process documents",
                type=["pdf", "docx", "xlsx", "txt"],
                accept_multiple_files=True,
                help="Supported formats: PDF, DOCX, XLSX, and TXT.",
            )

        if not uploads:
            st.info(
                "Add one or more PDF, DOCX, XLSX, or TXT files to begin.",
                icon=":material/upload_file:",
            )
            return
        if not st.button(
            "Extract text and analyze",
            type="primary",
            icon=":material/auto_awesome:",
        ):
            return

    result = ingest_documents(
        uploads,
        process_type=process_type.strip() or "general-process",
        config={"process_description": process_description.strip()},
    )
    ingestion = ingestion_view_model(result)
    _render_ingestion_results(st, result, ingestion)


def _render_ingestion_results(
    st: Any,
    result: Any,
    ingestion: dict[str, Any],
) -> None:
    document_count = len(ingestion["documents"])
    evidence_count = len(ingestion["evidence_items"])
    gap_count = len(result.state.gap_issues) if result.state is not None else 0
    conflict_count = (
        len(result.state.conflict_issues) if result.state is not None else 0
    )
    _render_metrics(
        st,
        [
            ("Documents", document_count, ":material/description:"),
            ("Evidence", evidence_count, ":material/verified:"),
            ("Gaps", gap_count, ":material/pending_actions:"),
            ("Conflicts", conflict_count, ":material/warning:"),
        ],
    )

    if ingestion["errors"]:
        st.warning(
            f"{len(ingestion['errors'])} file issue(s) need attention.",
            icon=":material/warning:",
        )
        st.dataframe(ingestion["errors"], hide_index=True)

    if result.state is None:
        st.info(ingestion["message"])
        return

    st.success(ingestion["message"], icon=":material/check_circle:")
    _render_workflow_workspace(st, workflow_view_model(result.state))


def _render_metrics(st: Any, metrics: list[tuple[str, int, str]]) -> None:
    columns = st.columns(len(metrics), gap="medium")
    for column, (label, value, icon) in zip(columns, metrics):
        with column:
            st.metric(label, value, border=True, help=f"{icon} {label}")


def _render_workflow_workspace(st: Any, view: dict[str, Any]) -> None:
    if view.get("is_demo"):
        st.warning(
            str(view.get("demo_label") or "Synthetic demo data"),
            icon=":material/science:",
        )

    header_columns = st.columns([2.5, 1, 1], vertical_alignment="center")
    with header_columns[0]:
        st.markdown(
            f'<div class="section-kicker">PROCESS</div>'
            f"<h2>{view.get('process_label', view['process_type'])}</h2>",
            unsafe_allow_html=True,
        )
        if view.get("process_description"):
            st.caption(view["process_description"])
    with header_columns[1]:
        st.metric("Lifecycle", _humanize(view["lifecycle_status"]), border=True)
    with header_columns[2]:
        st.metric(
            "Review state",
            "Needs review" if view["human_review_required"] else "Ready",
            border=True,
        )

    st.caption(
        f"Project `{view['project_id']}` · Run `{view['run_id']}` · "
        f"Next action: `{view['next_action']}`"
    )
    tabs = st.tabs(
        [
            "Overview",
            "Sources",
            "Evidence",
            "Findings",
            "Workflow proposal",
            "Trace",
        ]
    )
    with tabs[0]:
        _render_overview(st, view)
    with tabs[1]:
        _render_sources(st, view)
    with tabs[2]:
        _render_evidence(st, view)
    with tabs[3]:
        _render_findings(st, view)
    with tabs[4]:
        _render_proposal(st, view)
    with tabs[5]:
        _render_trace(st, view)


def _render_overview(st: Any, view: dict[str, Any]) -> None:
    st.markdown("### Run overview")
    if view["human_review_required"] and view["issues_unresolved"]:
        st.warning(
            "Human review is required. Outstanding findings remain unresolved; "
            "no winning policy or claim has been selected.",
            icon=":material/rate_review:",
        )
    elif view["issues_unresolved"]:
        st.info(
            "Findings are attached to this run and remain visible in the "
            "Findings and Workflow proposal tabs."
        )
    else:
        st.success("No unresolved gaps or conflicts were detected.")

    summary = [
        {"Field": "Current node", "Value": view["current_node"] or "Not started"},
        {"Field": "Next action", "Value": view["next_action"]},
        {"Field": "Retry count", "Value": view["retry_count"]},
        {"Field": "Proposal status", "Value": view["proposal_label"]},
    ]
    st.dataframe(summary, hide_index=True)
    if view["last_error"]:
        st.error(view["last_error"], icon=":material/error:")


def _render_sources(st: Any, view: dict[str, Any]) -> None:
    st.markdown("### Source documents")
    source_index = view.get("source_index", {})
    if source_index:
        rows = [
            {
                "Document ID": document_id,
                "Filename": metadata.get("filename", ""),
                "Type": metadata.get("file_type", ""),
                "Size": metadata.get("file_size", ""),
                "SHA-256": metadata.get("sha256", ""),
            }
            for document_id, metadata in source_index.items()
        ]
        st.dataframe(rows, hide_index=True)
    else:
        st.caption("No source document metadata is available.")


def _render_evidence(st: Any, view: dict[str, Any]) -> None:
    st.markdown("### Extracted evidence")
    evidence_items = view.get("evidence_items", [])
    if not evidence_items:
        st.info("No evidence items were extracted.")
        return
    rows = [
        {
            "Evidence ID": item.get("evidence_id", ""),
            "Document": item.get("filename", item.get("source_id", "")),
            "Kind": item.get("kind", "unknown"),
            "Quote": item.get("quote", ""),
            "Source references": ", ".join(item.get("source_refs", [])),
        }
        for item in evidence_items
    ]
    st.dataframe(rows, hide_index=True)
    st.caption("Expand an item to inspect its assertion and exact source location.")
    for item in evidence_items:
        with st.expander(
            f"{item.get('evidence_id', 'Evidence')} · "
            f"{item.get('kind', 'statement')}",
            icon=":material/format_quote:",
        ):
            st.write(item.get("quote", ""))
            if item.get("assertion"):
                st.json(item["assertion"])
            _render_provenance(st, item)


def _render_findings(st: Any, view: dict[str, Any]) -> None:
    st.markdown("### Findings")
    gaps = view.get("gap_issues", [])
    conflicts = view.get("conflict_issues", [])
    if not gaps and not conflicts:
        st.success("No gaps or conflicts detected.")
        return

    if gaps:
        st.markdown("#### Gaps")
        for issue in gaps:
            with st.expander(
                f"{issue['issue_id']} · {_humanize(issue['status'])}",
                icon=":material/pending_actions:",
            ):
                st.write(issue["description"])
                _render_issue_references(st, issue)
    else:
        st.caption("No gaps detected.")

    if conflicts:
        st.markdown("#### Conflicts")
        st.warning(
            "These competing claims remain unresolved. ProcessFoundry has not "
            "selected an authoritative claim.",
            icon=":material/warning:",
        )
        for issue in conflicts:
            with st.expander(
                f"{issue['issue_id']} · {_humanize(issue['status'])}",
                icon=":material/compare_arrows:",
            ):
                st.write(issue["description"])
                if issue["claims"]:
                    st.dataframe(
                        [
                            {
                                "Claim": claim.get("value", ""),
                                "Subject": claim.get("subject", ""),
                                "Predicate": claim.get("predicate", ""),
                                "Evidence": claim.get("evidence_id", ""),
                                "Source": claim.get("source_id", ""),
                            }
                            for claim in issue["claims"]
                        ],
                        hide_index=True,
                    )
                _render_issue_references(st, issue)
    else:
        st.caption("No conflicts detected.")


def _render_issue_references(st: Any, issue: dict[str, Any]) -> None:
    st.caption(f"Status: {issue['status']}")
    st.caption(
        "Evidence references: "
        + (", ".join(issue["evidence_refs"]) or "None")
    )
    st.caption(
        "Source references: " + (", ".join(issue["source_refs"]) or "None")
    )
    if issue.get("rule_refs"):
        st.caption("Rule references: " + ", ".join(issue["rule_refs"]))


def _render_proposal(st: Any, view: dict[str, Any]) -> None:
    st.markdown("### Workflow proposal")
    proposal = view.get("workflow_proposal", {})
    if not proposal:
        st.info("No workflow proposal supplied.")
        return

    proposal_status = proposal.get("status", "not supplied")
    if proposal_status != "approved":
        st.warning(
            f"This is an {view['proposal_label'].lower()}. It requires human "
            "review before it can be treated as authoritative.",
            icon=":material/edit_note:",
        )
    else:
        st.success("This proposal has an explicit approved status.")
    st.caption(
        f"Proposal ID: `{proposal.get('proposal_id', 'Not supplied')}` · "
        f"Status: `{proposal_status}`"
    )
    if proposal.get("explanation"):
        st.info(proposal["explanation"])

    steps = proposal.get("steps", [])
    st.markdown("#### Proposed steps")
    if not steps:
        st.caption("No supported process steps were extracted.")
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            st.markdown(f"{index}. {step}")
            continue
        title = step.get("title", step.get("step", "Proposed step"))
        with st.container(border=True):
            st.markdown(
                f'<span class="step-number">{index}</span>'
                f"<strong>{title}</strong>",
                unsafe_allow_html=True,
            )
            if step.get("description"):
                st.write(step["description"])
            if step.get("requirement"):
                st.caption(f"Supported requirement: {step['requirement']}")
            if step.get("responsible_role"):
                st.caption(f"Responsible role: {step['responsible_role']}")
            if step.get("actors"):
                st.caption(
                    "Actors: "
                    + ", ".join(
                        str(actor.get("label", actor))
                        for actor in step["actors"]
                    )
                )
            _render_reference_lines(
                st,
                step.get("evidence_refs", step.get("supported_by", [])),
                step.get("source_locations", []),
            )

    proposal_sections = (
        ("requirements", "Requirements"),
        ("required_inputs", "Required inputs"),
        ("conditions", "Conditions"),
        ("decisions", "Decisions"),
        ("responsibilities", "Responsibilities"),
        ("deadlines", "Deadlines"),
        ("produced_outputs", "Produced outputs"),
        ("related_evidence", "Related evidence"),
        ("data_evidence", "Data evidence"),
        ("exceptions", "Exception paths"),
        ("unresolved_questions", "Unresolved questions"),
        ("conflicts", "Unresolved conflicts"),
    )
    for field, label in proposal_sections:
        values = proposal.get(field)
        if not values:
            continue
        with st.expander(label, expanded=field in {"unresolved_questions", "conflicts"}):
            if field in {"unresolved_questions", "conflicts"}:
                st.warning(
                    "These items remain unresolved and require review.",
                    icon=":material/warning:",
                )
            st.dataframe(_compact_records(values), hide_index=True)

    if proposal.get("source_refs"):
        st.caption("Source references: " + ", ".join(proposal["source_refs"]))


def _render_trace(st: Any, view: dict[str, Any]) -> None:
    st.markdown("### Workflow execution trace")
    trace_events = view.get("trace_events", [])
    if trace_events:
        st.dataframe(trace_events, hide_index=True)
    else:
        st.caption("No trace events recorded.")


def _render_reference_lines(
    st: Any,
    evidence_refs: object,
    source_locations: object,
) -> None:
    if isinstance(evidence_refs, list):
        st.caption("Supporting evidence: " + (", ".join(evidence_refs) or "None"))
    if source_locations:
        st.caption("Source locations: " + _format_locations(source_locations))


def _render_provenance(st: Any, item: dict[str, Any]) -> None:
    st.caption("Source references: " + ", ".join(item.get("source_refs", [])))
    locations = item.get("source_locations", [])
    if locations:
        st.caption("Source locations: " + _format_locations(locations))


def _compact_records(values: object) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return [{"Value": values}]
    rows: list[dict[str, Any]] = []
    for value in values:
        if isinstance(value, dict):
            rows.append(
                {
                    key.replace("_", " ").title(): _display_value(item)
                    for key, item in value.items()
                    if key not in {"source_locations"}
                }
            )
        else:
            rows.append({"Value": value})
    return rows


def _display_value(value: Any) -> Any:
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return str(value)
    return value


def _humanize(value: object) -> str:
    return str(value).replace("_", " ").strip().title()


def _format_locations(locations: object) -> str:
    """Format only structured locations supplied by extraction or fixtures."""

    if not isinstance(locations, list):
        return ""
    formatted: list[str] = []
    for location in locations:
        if not isinstance(location, dict):
            continue
        parts = []
        for field in (
            "filename",
            "page",
            "paragraph",
            "section",
            "line_start",
            "line_end",
            "worksheet_name",
            "row_number",
            "table_id",
        ):
            if location.get(field) is not None:
                parts.append(f"{field}={location[field]}")
        if location.get("cell_coordinates"):
            parts.append(
                "cells=" + ",".join(map(str, location["cell_coordinates"]))
            )
        if parts:
            formatted.append("; ".join(parts))
    return " | ".join(formatted)


if __name__ == "__main__":
    main()
