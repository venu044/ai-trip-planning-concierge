"""
Phase 1 (skeleton) + Phase 7 (integration).

Wires Stages A, C, and B into one compiled LangGraph:

    START
      -> classify
      -> (conditional: flights_desk | accommodation_desk | itinerary_desk)
      -> extract_trip_request
      -> budget_screening
      -> supervisor
      -> (conditional: cost_optimization | premium_planning | recommendation)
      -> recommendation   (cost_optimization and premium_planning also flow here)
      -> END

The follow-up agent (Stage D) is intentionally NOT part of this graph --
it's an interactive, open-ended loop with its own checkpointer, run
separately by the driver script after this graph finishes. That mirrors
how the Agent Lab kept the ReAct agent as its own loop rather than a
single-shot graph node.
"""

from langgraph.graph import StateGraph, START, END

from state import TripState
from classification import (
    classify_node,
    route_after_classification,
    DESK_NODES,
)
from extraction import extract_trip_request_node
from feasibility import (
    budget_screening_node,
    supervisor_node,
    supervisor_router,
    cost_optimization_node,
    premium_planning_node,
    recommendation_node,
)


def build_main_graph():
    graph = StateGraph(TripState)

    # Stage A -- classification & routing
    graph.add_node("classify", classify_node)
    for name, node_fn in DESK_NODES.items():
        graph.add_node(f"{name}_desk", node_fn)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classification,
        {name: f"{name}_desk" for name in DESK_NODES},
    )

    # Stage C -- structured extraction (right after intake/routing)
    graph.add_node("extract_trip_request", extract_trip_request_node)
    for name in DESK_NODES:
        graph.add_edge(f"{name}_desk", "extract_trip_request")

    # Stage B -- feasibility multi-agent pipeline
    graph.add_node("budget_screening", budget_screening_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("cost_optimization", cost_optimization_node)
    graph.add_node("premium_planning", premium_planning_node)
    graph.add_node("recommendation", recommendation_node)

    graph.add_edge("extract_trip_request", "budget_screening")
    graph.add_edge("budget_screening", "supervisor")

    # Supervisor's router returns a next-node name directly -- no mapping dict needed.
    graph.add_conditional_edges("supervisor", supervisor_router)

    graph.add_edge("cost_optimization", "recommendation")
    graph.add_edge("premium_planning", "recommendation")
    graph.add_edge("recommendation", END)

    return graph.compile()


if __name__ == "__main__":
    # Quick structural sanity check: compiles without needing a live LLM.
    app = build_main_graph()
    print("Graph compiled OK. Nodes:", list(app.get_graph().nodes))
