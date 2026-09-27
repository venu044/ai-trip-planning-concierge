# AI Trip Planning Concierge

A LangChain + LangGraph multi-agent app: classifies a travel request, extracts
it into structured data, runs it through a supervisor-led feasibility
pipeline, answers tool-using follow-up questions with memory, and saves a
JSON session report.

## Setup

```bash
pip install langchain langchain-core langchain-ollama langgraph pydantic
ollama pull qwen2.5:3b
ollama serve   # if not already running
```

## Run

```bash
python main.py                 # runs 3 built-in sample trips end-to-end
python main.py --interactive   # ...then lets you type your own trip + follow-ups
```

Each run prints, per trip: the classification + desk response, the
extracted structured trip request, the feasibility pipeline's path and
final tier, and the follow-up Q&A. It also writes one JSON report per trip
(`session_report_1_borderline.json`, etc.).

## Files

| File | Phase | What it does |
|---|---|---|
| `state.py` | 1 | Shared `TripState` TypedDict threaded through the whole graph. |
| `llm_config.py` | 1 | Connects to the local Ollama model. |
| `classification.py` | 2 | Classifier node (flights/accommodation/itinerary) + the three specialist desk nodes + the conditional-edge router. |
| `extraction.py` | 3 | `TripRequest` Pydantic schema + `JsonOutputParser` LCEL chain that turns free text into structured data. |
| `feasibility.py` | 4 | The multi-agent pipeline: Budget Screening Agent -> Supervisor Agent -> (Cost Optimization / Premium Planning) -> Recommendation Agent. |
| `tools.py` | 5 | Three `@tool` functions: `convert_currency`, `apply_discount`, `destination_info` (static reference data, no live network calls). |
| `followup_agent.py` | 5 | Builds the ReAct agent (`create_react_agent`) with a `MemorySaver` checkpointer, and helpers to prime it with trip context, ask a question, and read back history. |
| `report.py` | 6 | Builds the combined session dict and writes it to JSON. |
| `graph.py` | 1 + 7 | Compiles Stages A/C/B into one `StateGraph`. |
| `main.py` | 7 | Driver script: runs the graph, then the follow-up loop, then saves the report, for each sample trip (and optionally an interactive one). |
| `session_report_sample.json` | -- | Example output matching the spec's Section 6 walkthrough (Bali, needs-review -> Budget tier). |

## Design notes

- **Feasibility thresholds** live at the top of `feasibility.py` as
  `OVER_BUDGET_CEILING` / `NEEDS_REVIEW_CEILING` (USD per person per day).
  Defaults: below $40 = over-budget, $40-$100 = needs-review, above
  $100 = feasible (split into Standard/Premium at $120).
- **The follow-up agent runs outside the main graph.** It's an open-ended,
  multi-turn loop with its own checkpointer/thread id, started after the
  main graph finishes for that trip -- mirroring how the labs kept the
  ReAct agent as its own driver loop rather than a single graph node.
- **Guardrails**: the classifier falls back to `itinerary` on an
  unrecognized label; the extractor falls back to a zeroed-out
  `TripRequest` if the LLM's JSON fails schema validation.
- **Tools use static lookup tables** (FX rates, destination facts) instead
  of live APIs, so the whole thing runs offline once Ollama is up. Swap in
  a real FX/weather API in `tools.py` if you want live data.

## Sample run (from `session_report_sample.json`)

Request: *"We're 2 people looking at 6 days in Bali, budget around $900
total, mostly want a relaxed itinerary."*

1. Classified as **itinerary** -> routed to the Itinerary desk.
2. Extracted: `destination=Bali, travelers=2, duration_days=6, budget=900`.
3. Budget Screening: $75/person/day -> **needs-review**.
4. Supervisor routes to **Cost Optimization** (borderline case).
5. Recommendation: **Budget tier** -- guesthouses, local transport, lean itinerary.
6. Follow-up: "What's that per person per day?" -> $75.00. "15% off that
   total?" -> $765.00 (saves $135). "Weather there that month?" -> pulled
   from `destination_info`.
7. Full session saved to JSON.
