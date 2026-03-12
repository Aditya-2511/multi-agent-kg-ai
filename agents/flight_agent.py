"""
agents/flight_agent.py
"""

from datetime import date

from services.flight_service import get_flights
from utils.flight_utils import extract_airports_from_question, format_flight_list
from llm.groq_client import chat


def recommend_flight(question: str, flights: list[dict]) -> str:
    """Uses Groq to recommend the best flight based on user intent."""
    if not flights:
        return "No flights available to recommend."

    # cap at 10 to avoid token overflow
    flight_summary = ""
    for i, f in enumerate(flights[:10], 1):
        flight_summary += (
            f"{i}. [{f['flight_number']}] {f['airline']}\n"
            f"   From: {f['from_airport']} → {f['to_airport']}\n"
            f"   Departure: {f['departure']} | Arrival: {f['arrival']}\n"
            f"   Duration: {f['duration']} | {f['stops']} | Price: {f['price']}\n"
            f"   Tags: {', '.join(f['tags']) if f['tags'] else 'none'}\n\n"
        )

    prompt = f"""You are an expert flight booking assistant.

A user asked: "{question}"

Here are the available flights (top 10):
{flight_summary}

Instructions:
- Carefully read the user's intent (cheapest, fastest, non-stop, morning, etc.)
- If the user asks for cheapest, list ALL flights with lowest prices
- If the user asks for fastest, list ALL non-stop or shortest duration flights
- If the user asks for morning flights, list ALL flights departing before 12:00
- After listing relevant flights, recommend the BEST one and explain why in 1-2 lines
- Always mention flight number and airline
- Keep response concise and use bullet points for multiple options
"""

    try:
        recommendation = chat(prompt, max_tokens=300)
        print(f"[flight_agent] Groq recommendation generated.")
        return recommendation
    except Exception as e:
        print(f"[flight_agent] Recommendation failed: {e}")
        return "Could not generate a recommendation at this time."


def generate_flight_nl_answer(question: str, flights: list[dict], recommendation: str) -> str:
    """Uses Groq to convert raw flight results into a conversational response."""
    if not flights:
        return (
            "No flights found. This may be because the date is outside the "
            "available booking window. Try a date within the next 2-3 days."
        )

    flight_summary = ""
    for i, f in enumerate(flights[:10], 1):
        flight_summary += (
            f"{i}. [{f['flight_number']}] {f['airline']} | "
            f"{f['from_airport']} → {f['to_airport']} | "
            f"Departs: {f['departure']} | Duration: {f['duration']} | "
            f"{f['stops']} | Price: {f['price']}\n"
        )

    prompt = f"""You are a helpful flight booking assistant having a friendly conversation.

User asked: "{question}"

Available flights (top 10 of {len(flights)} total):
{flight_summary}

AI Recommendation already generated:
{recommendation}

Your task:
- Write a natural conversational response (2-4 sentences)
- Mention total number of flights found
- Highlight the recommended flight naturally (airline + flight number + key detail)
- Mention price range if helpful
- End with a useful tip (book early, non-stop available, etc.)
- Do NOT use bullet points — flowing paragraph only
- Sound like a knowledgeable friend, not a database
"""

    try:
        nl_answer = chat(prompt, max_tokens=300)
        print(f"[flight_agent] Natural language answer generated.")
        return nl_answer
    except Exception as e:
        print(f"[flight_agent] NL answer generation failed: {e}")
        return None


def flight_agent(state: dict) -> dict:
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
        state["error"]         = f"Could not identify origin or destination airport from: '{question}'. Please mention valid city names."
        state["flight_result"] = []
        state["flight_answer"] = state["error"]
        return state

    print(f"[flight_agent] Route: {origin_code} → {dest_code}  Date: {journey_date}")

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
    state["flight_answer"] = header + format_flight_list(flights[:10])

    print(f"[flight_agent] Found {meta['total_flights']} flights for {meta['origin_code']} → {meta['destination_code']}")

    # ── 5. Groq Flight Recommendation ────────────────────────────────────────
    recommendation = recommend_flight(question, flights)
    state["flight_recommendation"] = recommendation

    # ── 6. Groq Natural Language Answer ──────────────────────────────────────
    nl_answer = generate_flight_nl_answer(question, flights, recommendation)
    state["flight_nl_answer"] = nl_answer

    return state