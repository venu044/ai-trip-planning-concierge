"""
Phase 2 -- Classification & Routing (Stage A).

A classifier node labels the incoming request as one of three categories,
then a conditional edge sends execution to the matching specialist desk
node, which drafts a first-line response.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from state import TripState

VALID_CATEGORIES = {"flights", "accommodation", "itinerary"}
FALLBACK_CATEGORY = "itinerary"

CLASSIFIER_SYSTEM_PROMPT = """You are a travel-request classifier for a travel agency.
Read the traveler's message and label it with exactly one of these categories:

- flights        (booking or asking about flights/airfare)
- accommodation   (booking or asking about hotels/stays)
- itinerary       (planning activities, day-by-day plans, general trip requests)

Respond with ONLY the single category word, lowercase, nothing else."""


def classify_node(state: TripState) -> TripState:
    """LLM-based classification with a safe fallback for bad output."""
    from llm_config import get_llm

    llm = get_llm()
    messages = [
        SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
        HumanMessage(content=state["raw_request"]),
    ]
    raw_label = llm.invoke(messages).content.strip().lower()

    # Guardrail: only accept a label we actually recognize.
    category = raw_label if raw_label in VALID_CATEGORIES else FALLBACK_CATEGORY
    return {"category": category}


def route_after_classification(state: TripState) -> str:
    """Router function used by add_conditional_edges."""
    return state.get("category", FALLBACK_CATEGORY)


def flights_desk_node(state: TripState) -> TripState:
    response = (
        "Flights desk: I can help you find and compare flight options for "
        f"this trip. Let's start from your request: \"{state['raw_request']}\"."
    )
    return {"desk_response": response}


def accommodation_desk_node(state: TripState) -> TripState:
    response = (
        "Accommodation desk: I can help you find a place to stay that fits "
        f"your budget and dates. Starting point: \"{state['raw_request']}\"."
    )
    return {"desk_response": response}


def itinerary_desk_node(state: TripState) -> TripState:
    response = (
        "Itinerary desk: I can help you put together a day-by-day plan for "
        f"this trip. Starting point: \"{state['raw_request']}\"."
    )
    return {"desk_response": response}


DESK_NODES = {
    "flights": flights_desk_node,
    "accommodation": accommodation_desk_node,
    "itinerary": itinerary_desk_node,
}
