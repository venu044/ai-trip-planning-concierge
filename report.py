"""
Phase 6 -- Session Report (Stage E).

Collects the classification result, extracted trip request, multi-agent
recommendation, and the full follow-up conversation into one structure,
and writes it to a readable JSON file.
"""

import json
from datetime import datetime, timezone
from state import TripState


def build_report(state: TripState) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "session_id": state.get("session_id"),
        "raw_request": state.get("raw_request"),
        "classification": {
            "category": state.get("category"),
            "desk_response": state.get("desk_response"),
        },
        "trip_request": state.get("trip_request"),
        "feasibility": {
            "budget_status": state.get("budget_status"),
            "per_person_per_day_usd": state.get("per_person_per_day"),
            "pipeline_path": state.get("pipeline_path"),
            "trip_tier": state.get("trip_tier"),
            "tier_explanation": state.get("tier_explanation"),
        },
        "followup_conversation": state.get("conversation_history", []),
    }


def save_report(report: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
