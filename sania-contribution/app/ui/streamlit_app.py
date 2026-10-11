"""Minimal Streamlit workflow-status shell."""

from app.agents.ingestion_service import ingest_documents
from app.ui.mock_adapter import get_demo_runs
from app.ui.view_models import ingestion_view_model, workflow_view_model


def main() -> None:
    """Render the disconnected demo workflow view."""

    import streamlit as st

    st.set_page_config(page_title="ProcessFoundry Workflow", layout="wide")
    st.title("ProcessFoundry AI")
    mode = st.radio(
        "View",
        ["Clean completed demo", "Unresolved issues demo", "Analyze uploaded documents"],
        horizontal=True,
    )
    if mode == "Analyze uploaded documents":
        _render_upload_analysis(st)
        return

    st.warning("DEMO DATA — NOT CONNECTED TO A LIVE BACKEND")
    st.subheader("Workflow status")
    run_id = (
        "demo-run-completed"
        if mode == "Clean completed demo"
        else "demo-run-review"
    )
    run = {item.run_id: item for item in get_demo_runs()}[run_id]
    view = workflow_view_model(run)
    _render_workflow(st, view)


def _render_upload_analysis(st: object) -> None:
    """Render local, in-memory analysis for uploaded documents."""

    st.info("Upload analysis is local and in-memory; it is not connected to a live backend and is not persisted.")
    st.subheader("Analyze uploaded documents")
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

    result = ingest_documents(uploads)
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
                    "Value": item["assertion"]["value"],
                    "Source ID": item["source_id"],
                    "Source references": ", ".join(item.get("source_refs", [])),
                }
                for item in ingestion["evidence_items"]
            ]
        )
    if result.state is not None:
        st.markdown("### Analysis findings")
        _render_workflow(st, workflow_view_model(result.state))


def _render_workflow(st: object, view: dict[str, object]) -> None:
    """Render a workflow view shared by demo and upload analysis."""

    st.caption(f"Project: {view['project_id']} | Run: {view['run_id']}")
    st.write(f"**Process type:** {view['process_type']}")
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
                st.write(f"- {step.get('step', 'Proposed step')}")
                if step.get("description"):
                    st.write(f"  - {step['description']}")
                if step.get("requirement"):
                    st.write(f"  - Supported requirement: {step['requirement']}")
                if step.get("responsible_role"):
                    st.write(f"  - Responsible role: {step['responsible_role']}")
                st.write(
                    "  - Evidence: "
                    + ", ".join(step.get("supported_by", []))
                )
            else:
                st.write(f"- {step}")
        if proposal.get("requirements"):
            st.write("**Extracted requirements:**")
            st.table(proposal["requirements"])
        if proposal.get("required_inputs"):
            st.write("**Required supporting documents:**")
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
        if proposal.get("decision_points"):
            st.write("**Eligibility checks and decision points:**")
            st.table(
                [
                    {
                        "Check": item.get("check", ""),
                        "Description": item.get("description", ""),
                        "Claim": item.get("claim", ""),
                        "Evidence": ", ".join(item.get("evidence_refs", [])),
                        "Sources": ", ".join(item.get("source_refs", [])),
                    }
                    for item in proposal["decision_points"]
                ]
            )
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
    else:
        st.write("No workflow proposal supplied.")

    st.markdown("### Trace")
    if view["trace_events"]:
        st.table(view["trace_events"])
    else:
        st.write("No trace events recorded.")


if __name__ == "__main__":
    main()
