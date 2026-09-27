"""
Phase 3 -- Structured Trip Request Extraction (Stage C).

Turns the traveler's free-text message into a validated, typed object
(destination, travelers, duration_days, budget) using a Pydantic schema
and a JsonOutputParser-based LCEL chain, the same pattern as the
Parsers Lab's StudentProfile extractor.
"""

from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from state import TripState


class TripRequest(BaseModel):
    destination: str = Field(description="City, region, or country the traveler wants to visit")
    travelers: int = Field(description="Number of people traveling", ge=1)
    duration_days: int = Field(description="Length of the trip in days", ge=1)
    budget: float = Field(description="Total trip budget in USD", ge=0)


_parser = JsonOutputParser(pydantic_object=TripRequest)

_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Extract the trip details from the traveler's message into the "
            "requested JSON schema. If a field truly isn't mentioned, make a "
            "reasonable estimate rather than leaving it blank.\n"
            "{format_instructions}",
        ),
        ("human", "{raw_request}"),
    ]
).partial(format_instructions=_parser.get_format_instructions())


def _default_trip_request(raw_request: str) -> dict:
    """Safe fallback if the LLM output fails schema validation."""
    return {
        "destination": "unspecified",
        "travelers": 1,
        "duration_days": 1,
        "budget": 0.0,
    }


def extract_trip_request_node(state: TripState) -> TripState:
    from llm_config import get_llm

    chain = _prompt | get_llm() | _parser
    try:
        result = chain.invoke({"raw_request": state["raw_request"]})
        # Validate/coerce through the Pydantic model so types are guaranteed.
        validated = TripRequest(**result)
        trip_request = validated.model_dump()
    except Exception:
        trip_request = _default_trip_request(state["raw_request"])

    return {"trip_request": trip_request}
