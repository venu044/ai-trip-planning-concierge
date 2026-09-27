"""
Phase 4 -- Trip Feasibility Assessment (Stage B), a small multi-agent
pipeline modeled on the supervisor pattern from the Multi-Agent Lab,
re-purposed for trip planning instead of hiring.

Flow:
    budget_screening_node -> supervisor_node -> (conditional)
        - cost_optimization_node   (borderline / needs-review)
        - premium_planning_node    (clearly comfortable budget)
        - recommendation_node      (clearly over-budget: straight to decision)
    cost_optimization_node -> recommendation_node
    premium_planning_node  -> recommendation_node
"""

from state import TripState

# Thresholds for per-person-per-day spend, in USD. Tune freely.
OVER_BUDGET_CEILING = 40.0     # below this, the trip is not feasible
NEEDS_REVIEW_CEILING = 100.0   # between the two ceilings -> borderline
# above NEEDS_REVIEW_CEILING -> comfortably feasible


def budget_screening_node(state: TripState) -> TripState:
    """Budget Screening Agent: reads budget + trip length, gives a preliminary status."""
    trip = state.get("trip_request", {})
    travelers = max(trip.get("travelers", 1), 1)
    duration_days = max(trip.get("duration_days", 1), 1)
    budget = trip.get("budget", 0.0)

    per_person_per_day = budget / (travelers * duration_days)

    if per_person_per_day < OVER_BUDGET_CEILING:
        status = "over-budget"
    elif per_person_per_day < NEEDS_REVIEW_CEILING:
        status = "needs-review"
    else:
        status = "feasible"

    return {
        "budget_status": status,
        "per_person_per_day": round(per_person_per_day, 2),
        "pipeline_path": ["budget_screening"],
    }


def supervisor_node(state: TripState) -> TripState:
    """Supervisor Agent: decides which agent runs next based on the screening status."""
    status = state.get("budget_status", "needs-review")

    if status == "over-budget":
        next_agent = "recommendation"       # straight to final decision
    elif status == "needs-review":
        next_agent = "cost_optimization"     # borderline case
    else:  # "feasible"
        next_agent = "premium_planning"      # clearly comfortable budget

    path = state.get("pipeline_path", []) + ["supervisor"]
    return {"next_agent": next_agent, "pipeline_path": path}


def supervisor_router(state: TripState) -> str:
    """Router function used by add_conditional_edges (no explicit mapping dict needed)."""
    return state.get("next_agent", "recommendation")


def cost_optimization_node(state: TripState) -> TripState:
    """Cost Optimization Agent: looks for ways to make a borderline trip work."""
    path = state.get("pipeline_path", []) + ["cost_optimization"]
    note = (
        "Cost optimization pass: shifted toward guesthouses/hostels, local "
        "transport, and off-peak dates to stretch a borderline budget."
    )
    return {"pipeline_path": path, "tier_explanation": note}


def premium_planning_node(state: TripState) -> TripState:
    """Premium Planning Agent: builds out a richer plan for comfortable budgets."""
    path = state.get("pipeline_path", []) + ["premium_planning"]
    note = (
        "Premium planning pass: budget comfortably covers upgraded stays, "
        "guided experiences, and more flexible dining/transport choices."
    )
    return {"pipeline_path": path, "tier_explanation": note}


def recommendation_node(state: TripState) -> TripState:
    """Recommendation Agent: converts the screening status into a final trip tier."""
    status = state.get("budget_status", "needs-review")
    per_day = state.get("per_person_per_day", 0.0)
    path = state.get("pipeline_path", []) + ["recommendation"]

    if status == "over-budget":
        tier = "Not Feasible"
        explanation = (
            f"At ~${per_day:.2f} per person/day, this budget is too tight for "
            "the requested trip. Recommend extending the budget or shortening "
            "the trip."
        )
    elif status == "needs-review":
        tier = "Budget"
        explanation = (
            f"At ~${per_day:.2f} per person/day, this trip is workable at the "
            "Budget tier: guesthouses, local transport, and a lean itinerary."
        )
    else:  # "feasible"
        # Split the comfortable range into Standard vs Premium.
        if per_day >= 120.0:
            tier = "Premium"
        else:
            tier = "Standard"
        explanation = (
            f"At ~${per_day:.2f} per person/day, this trip comfortably "
            f"supports the {tier} tier."
        )

    return {"trip_tier": tier, "tier_explanation": explanation, "pipeline_path": path}
