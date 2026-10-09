"""Construction of the initial minimal ProcessFoundry LangGraph workflow."""

from langgraph.graph import END, START, StateGraph

from .nodes import finish_node, initialize_node
from .state import ProcessFoundryState


def build_graph():
    """Build and compile ``START -> initialize -> finish -> END``."""

    graph = StateGraph(ProcessFoundryState)
    graph.add_node("initialize", initialize_node)
    graph.add_node("finish", finish_node)
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "finish")
    graph.add_edge("finish", END)
    return graph.compile()
