"""
Phase 1 -- Shared state schema.

One TypedDict is threaded through every node in the graph (classification,
extraction, feasibility pipeline) so all stages read/write the same
shared memory instead of passing data around by hand.
"""

from typing import Any, Dict, List, Optional, TypedDict


class TripState(TypedDict, total=False):
    # --- Stage A: intake & routing -----------------------------------
    raw_request: str            # the traveler's original free-text message
    category: str                # "flights" | "accommodation" | "itinerary"
    desk_response: str           # first-line response from the specialist desk

    # --- Stage C: structured extraction --------------------------------
    trip_request: Dict[str, Any]  # {destination, travelers, duration_days, budget}

    # --- Stage B: feasibility multi-agent pipeline ----------------------
    budget_status: str           # "feasible" | "needs-review" | "over-budget"
    per_person_per_day: float    # derived budget metric used for screening
    next_agent: str              # supervisor's routing decision
    pipeline_path: List[str]     # trace of which agents actually ran
    trip_tier: str               # "Budget" | "Standard" | "Premium" | "Not Feasible"
    tier_explanation: str        # human-readable justification for the tier

    # --- Stage D: follow-up Q&A -----------------------------------------
    conversation_history: List[Dict[str, str]]  # [{"role": ..., "content": ...}]
    session_id: str              # thread id used by the checkpointer

    # --- Stage E: report --------------------------------------------------
    report: Dict[str, Any]
