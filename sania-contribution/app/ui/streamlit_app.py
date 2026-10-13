"""Minimal Streamlit workflow-status shell."""

from app.agents.ingestion_service import ingest_documents
from app.ui.mock_adapter import get_all_demo_runs
from app.ui.view_models import ingestion_view_model, workflow_view_model


def main() -> None:
    """Render the disconnected demo workflow view."""

    import streamlit as st

    st.set_page_config(page_title="ProcessFoundry Workflow", layout="wide")
    st.title("ProcessFoundry AI")
    mode = st.radio(
        "View",
        ["Synthetic demo", "Analyze uploaded documents"],
        horizontal=True,
    )
    if mode == "Analyze uploaded documents":
        _render_upload_analysis(st)
        return

    st.warning("SYNTHETIC DEMO DATA — NOT CONNECTED TO A LIVE BACKEND")
    st.subheader("Workflow status")
    demos = get_all_demo_runs()
    selected_demo = st.selectbox(
        "Synthetic process demo",
        demos,
        format_func=lambda run: run.config.get(
            "demo_label", run.process_type
        ),
    )
    view = workflow_view_model(selected_demo)
    _render_workflow(st, view)


def _render_upload_analysis(st: object) -> None:
    """Render local, in-memory analysis for uploaded documents."""

    st.info("Upload analysis is local and in-memory; it is not connected to a live backend and is not persisted.")
    st.subheader("Analyze uploaded documents")
    process_type = st.text_input("Process identity", value="general-process")
    process_description = st.text_input(
        "Process description (optional)",
        value="",
    )
    uploads = st.file_uploader(
        "Upload PDF, DOCX, XLSX, or TXT files",
        type=["pdf", "docx", "xlsx", "txt"],
        accept_multiple_files=True,
    )
    if not uploads:
        st.info("No files uploaded. Upload at least one document to begin analysis.")
        return
    if not st.button("Extract text and analyze"):
        return

    result = ingest_documents(
        uploads,
        process_type=process_type.strip() or "general-process",
        config={
            "process_description": process_description.strip(),
        },
    )
    ingestion = ingestion_view_model(result)
    st.write(f"**Result:** {ingestion['message']}")
    if ingestion["documents"]:
        st.markdown("### Uploaded documents")
        st.table(ingestion["documents"])
    if ingestion["errors"]:
        st.markdown("### File issues")
        st.table(ingestion["errors"])
    if ingestion["sections"]:
        st.markdown("### Extracted text")
        for section in ingestion["sections"]:
            if section.get("worksheet_name"):
                location = (
                    f"{section['worksheet_name']} / row "
                    f"{section.get('row_number') or 'empty'}"
                )
            else:
                location = section.get("page", section.get("section"))
            label = f"{section['filename']} — {location}" if location else section["filename"]
            with st.expander(label):
                if section.get("worksheet_empty"):
                    st.write("Worksheet is empty.")
                elif section.get("cells"):
                    st.table(section["cells"])
                else:
                    st.write(section["text"])
    if ingestion["evidence_items"]:
        st.markdown("### Recognized evidence")
        st.table(
            [
                {
                    "Evidence ID": item["evidence_id"],
                    "Document": item["filename"],
                    "Location": (
                        f"{item['worksheet_name']} / "
                        f"{', '.join(item.get('cell_references', []))}"
                        if item.get("worksheet_name")
                        else item.get("page", item.get("section"))
                    ),
                    "Quote": item["quote"],
                    "Kind": item.get("kind", "unknown"),
                    "Value": item.get("assertion", {}).get("value", ""),
                    "Source ID": item["source_id"],
                    "Source references": ", ".join(item.get("source_refs", [])),
                    "Source locations": _format_locations(item.get("source_locations", [])),
                }
                for item in ingestion["evidence_items"]
            ]
        )
    if result.state is not None:
        st.markdown("### Analysis findings")
        _render_workflow(st, workflow_view_model(result.state))


def _render_workflow(st: object, view: dict[str, object]) -> None:
    """Render a workflow view shared by demo and upload analysis."""

    if view.get("demo_label"):
        st.warning(str(view["demo_label"]))
    st.caption(f"Project: {view['project_id']} | Run: {view['run_id']}")
    st.write(f"**Process:** {view.get('process_label', view['process_type'])}")
    if view.get("process_description"):
        st.write(f"**Description:** {view['process_description']}")
    st.write(f"**Lifecycle:** {view['lifecycle_status']}")
    st.write(f"**Current node:** {view['current_node'] or 'Not started'}")
    st.write(f"**Next action:** {view['next_action']}")
    st.write(f"**Retry count:** {view['retry_count']}")
    if view["human_review_required"] and view["issues_unresolved"]:
        st.warning("Human review needed. Issues remain unresolved.")

    st.markdown("### Gaps")
    if not view["gap_issues"]:
        st.write("No gaps detected.")
    for issue in view["gap_issues"]:
        with st.expander(f"{issue['issue_id']} — {issue['status']}"):
            st.write(issue["description"])
            st.write(f"**Status:** {issue['status']}")
            st.write(f"**Evidence references:** {', '.join(issue['evidence_refs']) or 'None'}")
            st.write(f"**Source references:** {', '.join(issue['source_refs']) or 'None'}")
            st.write(f"**Rule references:** {', '.join(issue['rule_refs']) or 'None'}")

    st.markdown("### Conflicts")
    if not view["conflict_issues"]:
        st.write("No conflicts detected.")
    for issue in view["conflict_issues"]:
        with st.expander(f"{issue['issue_id']} — {issue['status']}"):
            st.write(issue["description"])
            st.write(f"**Status:** {issue['status']}")
            if issue["claims"]:
                st.write("**Competing claims (no winning claim selected):**")
                st.table(
                    [
                        {
                            "Claim": claim.get("value", ""),
                            "Evidence": claim.get("evidence_id", ""),
                            "Source": claim.get("source_id", ""),
                        }
                        for claim in issue["claims"]
                    ]
                )
            st.write(f"**Evidence references:** {', '.join(issue['evidence_refs']) or 'None'}")
            st.write(f"**Source references:** {', '.join(issue['source_refs']) or 'None'}")

    st.markdown("### Workflow proposal")
    st.caption(f"**{view['proposal_label']}**")
    proposal = view["workflow_proposal"]
    if proposal:
        st.write(f"**Proposal ID:** {proposal.get('proposal_id', 'Not supplied')}")
        st.write(f"**Status:** {proposal.get('status', 'Not supplied')}")
        if proposal.get("explanation"):
            st.info(proposal["explanation"])
        st.write("**Steps:**")
        for step in proposal.get("steps", []):
            if isinstance(step, dict):
                st.write(f"- {step.get('title', step.get('step', 'Proposed step'))}")
                if step.get("description"):
                    st.write(f"  - {step['description']}")
                if step.get("requirement"):
                    st.write(f"  - Supported requirement: {step['requirement']}")
                if step.get("responsible_role"):
                    st.write(f"  - Responsible role: {step['responsible_role']}")
                st.write(
                    "  - Evidence: "
                    + ", ".join(
                        step.get("evidence_refs", step.get("supported_by", []))
                    )
                )
                if step.get("actors"):
                    st.write(
                        "  - Actors: "
                        + ", ".join(
                            str(actor.get("label", actor))
                            for actor in step["actors"]
                        )
                    )
                if step.get("source_locations"):
                    st.write(
                        "  - Locations: "
                        + _format_locations(step["source_locations"])
                    )
            else:
                st.write(f"- {step}")
        if proposal.get("requirements"):
            st.write("**Requirements:**")
            st.table(proposal["requirements"])
        if proposal.get("required_inputs"):
            st.write("**Required inputs:**")
            st.table(
                [
                    {
                        "Requirement": item.get("description", item.get("document", "")),
                        "Evidence": ", ".join(item.get("evidence_refs", [])),
                        "Sources": ", ".join(item.get("source_refs", [])),
                    }
                    for item in proposal["required_inputs"]
                ]
            )
        if proposal.get("conditions"):
            st.write("**Conditions:**")
            st.table(proposal["conditions"])
        if proposal.get("decisions", proposal.get("decision_points")):
            st.write("**Decisions:**")
            st.table(
                [
                    {
                        "Check": item.get("check", item.get("assertion", {}).get("predicate", "")),
                        "Description": item.get("description", ""),
                        "Claim": item.get("claim", ""),
                        "Evidence": ", ".join(item.get("evidence_refs", [])),
                        "Sources": ", ".join(item.get("source_refs", [])),
                    }
                    for item in proposal.get("decisions", proposal.get("decision_points", []))
                ]
            )
        for field, label in (
            ("responsibilities", "Responsibilities"),
            ("deadlines", "Deadlines"),
            ("produced_outputs", "Produced outputs"),
            ("related_evidence", "Related evidence"),
            ("data_evidence", "Data evidence"),
        ):
            if proposal.get(field):
                st.write(f"**{label}:**")
                st.table(proposal[field])
        if proposal.get("exceptions"):
            st.write("**Exception paths:**")
            st.table(proposal["exceptions"])
        if proposal.get("conflicts"):
            st.warning("Unresolved conflicts affect this proposal.")
            st.table(proposal["conflicts"])
        if proposal.get("unresolved_questions"):
            st.warning("Review questions remain unresolved.")
            st.table(proposal["unresolved_questions"])
        st.write(
            "**Source references:** "
            + ", ".join(proposal.get("source_refs", []))
        )
        if view.get("evidence_items"):
            st.write("**Evidence provenance:**")
            st.table(
                [
                    {
                        "Evidence ID": item.get("evidence_id"),
                        "Kind": item.get("kind"),
                        "Quote": item.get("quote"),
                        "Sources": ", ".join(item.get("source_refs", [])),
                        "Locations": _format_locations(
                            item.get("source_locations", [])
                        ),
                    }
                    for item in view["evidence_items"]
                ]
            )
    else:
        st.write("No workflow proposal supplied.")

    st.markdown("### Trace")
    if view["trace_events"]:
        st.table(view["trace_events"])
    else:
        st.write("No trace events recorded.")


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
