"""Construction of the deterministic analysis LangGraph workflow."""

from langgraph.graph import END, START, StateGraph

from .nodes import (
    analyze_conflicts_node,
    analyze_gaps_node,
    blocked_node,
    finish_node,
    initialize_node,
    pause_for_human_node,
    route_after_conflicts,
)
from .state import ProcessFoundryState


def build_graph():
    """Build and compile the analysis workflow with a routing boundary."""

    graph = StateGraph(ProcessFoundryState)
    graph.add_node("initialize", initialize_node)
    graph.add_node("analyze_gaps", analyze_gaps_node)
    graph.add_node("analyze_conflicts", analyze_conflicts_node)
    graph.add_node("finish", finish_node)
    graph.add_node("pause_for_human", pause_for_human_node)
    graph.add_node("blocked", blocked_node)
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "analyze_gaps")
    graph.add_edge("analyze_gaps", "analyze_conflicts")
    graph.add_conditional_edges(
        "analyze_conflicts",
        route_after_conflicts,
        {
            "finish": "finish",
            "pause_for_human": "pause_for_human",
            "blocked": "blocked",
        },
    )
    graph.add_edge("finish", END)
    graph.add_edge("pause_for_human", END)
    graph.add_edge("blocked", END)
    return graph.compile()
