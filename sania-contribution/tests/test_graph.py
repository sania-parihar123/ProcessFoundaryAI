from datetime import datetime, timezone

from langgraph.graph.state import CompiledStateGraph

from app.graph.build_graph import build_graph
from app.graph.state import LifecycleStatus, ProcessFoundryState


def _new_state() -> ProcessFoundryState:
    return ProcessFoundryState(
        run_id="run-001",
        project_id="project-001",
        process_type="generic-process",
    )


def test_build_graph_returns_compiled_graph() -> None:
    graph = build_graph()

    assert isinstance(graph, CompiledStateGraph)


def test_graph_executes_initialize_then_finish() -> None:
    graph = build_graph()

    result = graph.invoke(_new_state())

    assert result["lifecycle_status"] is LifecycleStatus.COMPLETED
    assert result["current_node"] == "finish"
    assert result["next_action"] == "end"
    assert [event.node for event in result["trace_events"]] == [
        "initialize",
        "finish",
    ]
    assert all(
        event.timestamp.tzinfo is not None
        and event.timestamp.utcoffset() == timezone.utc.utcoffset(
            datetime.now(timezone.utc)
        )
        for event in result["trace_events"]
    )


def test_graph_preserves_existing_state_fields() -> None:
    state = _new_state()
    state.source_document_ids.append("source-001")

    result = build_graph().invoke(state)

    assert result["run_id"] == "run-001"
    assert result["project_id"] == "project-001"
    assert result["source_document_ids"] == ["source-001"]
