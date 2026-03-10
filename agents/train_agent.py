"""
agents/train_agent.py
─────────────────────
Train Agent — fits into the multi-agent state-dict pipeline.

Responsibility:
  1. Extract source + destination station codes from the question
     (or accept them as explicit state overrides).
  2. Call train_service.get_trains() to fetch live schedules.
  3. Write results back into state so reasoning_agent / response_agent
     can consume them downstream.

State contract
──────────────
Reads from state:
    question      (str)           Natural language query          [required]
    journey_date  (str yyyy-mm-dd) Travel date                    [optional → today]
    source_code   (str)           Override source station code    [optional]
    dest_code     (str)           Override destination code       [optional]

Writes to state:
    train_result  (list[dict])    Parsed train objects
    train_answer  (str)           Human-readable schedule string
    error         (str | None)    Error message, or None on success
"""

from datetime import date

from services.train_service import get_trains
from utils.station_utils import (
    extract_stations_from_question,
    format_train_list,
)

# ── Fallback route when nothing can be parsed ─────────────────────────────────
_DEFAULT_SOURCE = "AII"   # Ajmer
_DEFAULT_DEST   = "JP"    # Jaipur


# ─────────────────────────────────────────────────────────────────────────────
# Agent node
# ─────────────────────────────────────────────────────────────────────────────

def train_agent(state: dict) -> dict:
    """
    Agent node. Receives and returns the shared state dict.
    Called by orchestrator/agent_controller.py via AGENT_REGISTRY.
    """
    question     = state.get("question", "")
    journey_date = state.get("journey_date") or date.today().strftime("%Y-%m-%d")

    # ── 1. Resolve station codes ──────────────────────────────────────────────
    source_code = state.get("source_code")
    dest_code   = state.get("dest_code")
    
    print(f"journey_date : {journey_date}\nsource_code : {source_code}\ndest_code : {dest_code}")
    
    if not source_code or not dest_code:
        parsed_src, parsed_dst = extract_stations_from_question(question)
        source_code = source_code or parsed_src or _DEFAULT_SOURCE
        dest_code   = dest_code   or parsed_dst or _DEFAULT_DEST

    print(
        f"[train_agent] Route: {source_code} → {dest_code}  "
        f"Date: {journey_date}"
    )

    # ── 2. Fetch from service layer ───────────────────────────────────────────
    result = get_trains(source_code, dest_code, journey_date)

    # ── 3. Handle service error ───────────────────────────────────────────────
    if "error" in result:
        state["train_result"] = []
        state["train_answer"] = (
            f"Sorry, I couldn't fetch train data: {result['error']}"
        )
        state["error"] = result["error"]
        print(f"[train_agent] ERROR: {result['error']}")
        return state

    # ── 4. Write success results into state ───────────────────────────────────
    trains = result["trains"]
    meta   = result["meta"]

    state["train_result"] = trains
    state["error"]        = None

    header = (
        f"Trains from {meta['source_code']} → {meta['destination_code']} "
        f"on {meta['journey_date']} "
        f"({meta['total_trains']} train(s) found):\n\n"
    )
    state["train_answer"] = header + format_train_list(trains)
    print(
        f"[train_agent] Found {meta['total_trains']} trains "
        f"for {meta['source_code']} → {meta['destination_code']}"
    )
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Convenience wrapper — useful for direct / CLI calls without the full pipeline
# ─────────────────────────────────────────────────────────────────────────────

def ask_train_agent(
    question: str,
    journey_date: str | None = None,
    source_code:  str | None = None,
    dest_code:    str | None = None,
) -> str:
    """
    Run the train agent standalone (no orchestrator needed).

    Args:
        question     : Natural language question, e.g. "trains from Ajmer to Jaipur"
        journey_date : yyyy-mm-dd travel date (optional, defaults to today)
        source_code  : Override source station code (optional)
        dest_code    : Override destination station code (optional)

    Returns:
        Human-readable answer string.

    Usage:
        from agents.train_agent import ask_train_agent
        print(ask_train_agent("trains from mumbai to delhi", "2025-06-01"))
    """
    state: dict = {"question": question}
    if journey_date:
        state["journey_date"] = journey_date
    if source_code:
        state["source_code"] = source_code
    if dest_code:
        state["dest_code"] = dest_code

    state = train_agent(state)
    return state.get("train_answer", "No answer generated.")