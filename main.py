"""
Phase 7 -- Integration.

One driver script that, for each sample trip:
  1. Runs the main graph (classification -> extraction -> feasibility pipeline).
  2. Starts a follow-up Q&A session (tool-using ReAct agent + memory).
  3. Builds and saves a session report as JSON.

Usage:
    python main.py                 # runs 3 built-in demo trips, canned follow-ups
    python main.py --interactive   # after the demo trips, lets you type your own
                                    # trip request and ask live follow-up questions
"""

import argparse
import sys
import uuid

from graph import build_main_graph
from followup_agent import (
    build_followup_agent,
    prime_agent_with_trip_context,
    ask_followup,
    get_conversation_history,
)
from report import build_report, save_report

# Three sample trips covering feasible / over-budget / borderline, per the
# submission guidelines (Section 10).
SAMPLE_TRIPS = [
    {
        "label": "borderline",
        "request": (
            "We're 2 people looking at 6 days in Bali, budget around $900 "
            "total, mostly want a relaxed itinerary."
        ),
        "followups": [
            "What's that budget per person per day?",
            "What's 15% off that total for an early-bird discount?",
            "What's the weather like there in that month?",
        ],
    },
    {
        "label": "over-budget",
        "request": (
            "Just me, 6 days in Bali, I only have $150 total for the whole trip."
        ),
        "followups": [
            "How much is my budget in Indonesian Rupiah?",
        ],
    },
    {
        "label": "generous",
        "request": (
            "Planning a flight and hotel package for 2 people, 5 days in Paris, "
            "budget is about $4000."
        ),
        "followups": [
            "What's the weather like there in that month?",
            "What's 10% off $4000?",
        ],
    },
]


def run_one_trip(app, followup_agent, trip_label: str, raw_request: str, followups: list, report_path: str):
    print("\n" + "=" * 70)
    print(f"TRIP: {trip_label.upper()}  ->  \"{raw_request}\"")
    print("=" * 70)

    session_id = str(uuid.uuid4())
    result = app.invoke({"raw_request": raw_request, "session_id": session_id})

    print(f"[classification]  category={result['category']}")
    print(f"[desk]            {result['desk_response']}")
    print(f"[extraction]      {result['trip_request']}")
    print(
        f"[feasibility]     status={result['budget_status']} "
        f"(~${result['per_person_per_day']}/person/day), path={result['pipeline_path']}"
    )
    print(f"[recommendation]  tier={result['trip_tier']} -- {result['tier_explanation']}")

    # --- Stage D: follow-up Q&A, seeded with this trip's context -----------
    prime_agent_with_trip_context(
        followup_agent,
        session_id,
        result["trip_request"],
        result["trip_tier"],
        result["tier_explanation"],
    )
    print("\n[follow-up Q&A]")
    for question in followups:
        answer = ask_followup(followup_agent, session_id, question)
        print(f"  Q: {question}\n  A: {answer}")

    result["conversation_history"] = get_conversation_history(followup_agent, session_id)

    # --- Stage E: report -----------------------------------------------------
    report = build_report(result)
    save_report(report, report_path)
    print(f"\n[report]          saved to {report_path}")
    return result


def interactive_session(app, followup_agent):
    print("\n" + "=" * 70)
    print("INTERACTIVE MODE -- type your own trip request")
    print("=" * 70)
    raw_request = input("Describe your trip: ").strip()
    if not raw_request:
        return

    session_id = str(uuid.uuid4())
    result = app.invoke({"raw_request": raw_request, "session_id": session_id})
    print(f"\n[classification]  category={result['category']}")
    print(f"[desk]            {result['desk_response']}")
    print(f"[extraction]      {result['trip_request']}")
    print(f"[recommendation]  tier={result['trip_tier']} -- {result['tier_explanation']}")

    prime_agent_with_trip_context(
        followup_agent, session_id, result["trip_request"], result["trip_tier"], result["tier_explanation"]
    )

    print("\nAsk follow-up questions (blank line to stop):")
    while True:
        question = input("You: ").strip()
        if not question:
            break
        print("Agent:", ask_followup(followup_agent, session_id, question))

    result["conversation_history"] = get_conversation_history(followup_agent, session_id)
    report = build_report(result)
    save_report(report, "session_report_interactive.json")
    print("Saved session_report_interactive.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interactive", action="store_true", help="also run a live interactive session")
    args = parser.parse_args()

    app = build_main_graph()
    followup_agent = build_followup_agent()

    for i, trip in enumerate(SAMPLE_TRIPS, start=1):
        run_one_trip(
            app,
            followup_agent,
            trip["label"],
            trip["request"],
            trip["followups"],
            report_path=f"session_report_{i}_{trip['label']}.json",
        )

    if args.interactive:
        interactive_session(app, followup_agent)


if __name__ == "__main__":
    sys.exit(main() or 0)
