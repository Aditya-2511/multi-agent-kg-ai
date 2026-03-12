"""
agents/flight_agent.py
──────────────────────
Flight Agent — fits into the multi-agent state-dict pipeline.

State contract
──────────────
Reads from state:
    question      (str)            Natural language query         [required]
    journey_date  (str yyyy-mm-dd) Travel date                   [optional → today]
    origin_code   (str)            Override origin IATA code     [optional]
    dest_code     (str)            Override destination IATA code [optional]

Writes to state:
    flight_result (list[dict])     Parsed flight objects
    flight_answer (str)            Human-readable flight string
    error         (str | None)     Error message, or None on success
"""

from datetime import date

from services.flight_service import get_flights
from utils.flight_utils import extract_airports_from_question, format_flight_list

_DEFAULT_ORIGIN = "DEL"   # Delhi
_DEFAULT_DEST   = "BOM"   # Mumbai


def flight_agent(state: dict) -> dict:
    """
    Flight Agent node. Receives and returns the shared state dict.
    Called by orchestrator via AGENT_REGISTRY.
    """
    question     = state.get("question", "")
    journey_date = state.get("journey_date") or date.today().strftime("%Y-%m-%d")

    # ── 1. Resolve airport codes ──────────────────────────────────────────────
    origin_code = state.get("origin_code")
    dest_code   = state.get("dest_code")

    if not origin_code or not dest_code:
        parsed_origin, parsed_dest = extract_airports_from_question(question)
        origin_code = origin_code or parsed_origin
        dest_code   = dest_code   or parsed_dest

    if not origin_code or not dest_code:
        state["error"] = f"Could not identify origin or destination airport from: '{question}'. Please mention valid city names."
        state["flight_result"] = []
        state["flight_answer"] = state["error"]
        return state

    print(
        f"[flight_agent] Route: {origin_code} → {dest_code}  "
        f"Date: {journey_date}"
    )

    # ── 2. Fetch from service layer ───────────────────────────────────────────
    result = get_flights(origin_code, dest_code, journey_date)

    # ── 3. Handle service error ───────────────────────────────────────────────
    if "error" in result:
        state["flight_result"] = []
        state["flight_answer"] = f"Sorry, I couldn't fetch flight data: {result['error']}"
        state["error"]         = result["error"]
        print(f"[flight_agent] ERROR: {result['error']}")
        return state

    # ── 4. Write success results into state ───────────────────────────────────
    flights = result["flights"]
    meta    = result["meta"]

    state["flight_result"] = flights
    state["error"]         = None

    header = (
        f"Flights from {meta['origin_code']} → {meta['destination_code']} "
        f"on {meta['journey_date']} "
        f"({meta['total_flights']} flight(s) found):\n\n"
    )
    state["flight_answer"] = header + format_flight_list(flights)

    print(
        f"[flight_agent] Found {meta['total_flights']} flights "
        f"for {meta['origin_code']} → {meta['destination_code']}"
    )
    return state
