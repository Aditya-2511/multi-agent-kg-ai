from config import AIRPORT_CODES
from llm.groq_client import chat
import json
import re


def extract_airports_from_question(question: str) -> tuple[str | None, str | None]:
    """
    Uses Groq LLM to extract origin and destination city names,
    then resolves them to IATA sky codes.
    Falls back to keyword scan if LLM fails.
    """
    known_cities = ", ".join(sorted(AIRPORT_CODES.keys()))

    prompt = f"""You are a flight booking assistant. Extract the origin and destination city names from the user's question.

Known cities: {known_cities}

Rules:
- Return ONLY a JSON object with keys "origin" and "destination"
- Values must exactly match one of the known cities above (lowercase)
- If a city is not mentioned or not in the known list, use null
- No explanation, no markdown, just raw JSON

Examples:
  Question: "flights from delhi to mumbai" → {{"origin": "delhi", "destination": "mumbai"}}
  Question: "I want to fly from london to new york tomorrow" → {{"origin": "london", "destination": "new york"}}
  Question: "any flight from bangalore?" → {{"origin": "bangalore", "destination": null}}

Question: "{question}"
"""

    try:
        response = chat(prompt, max_tokens=100)
        clean    = re.sub(r"```(?:json)?|```", "", response).strip()
        data     = json.loads(clean)

        origin_name = data.get("origin")
        dest_name   = data.get("destination")

        print(f"[flight_utils] Groq extracted → origin: {origin_name}, destination: {dest_name}")

        origin_code = AIRPORT_CODES.get(origin_name.lower())[0] if origin_name else None
        dest_code   = AIRPORT_CODES.get(dest_name.lower())[0]   if dest_name   else None

        if origin_code or dest_code:
            return origin_code, dest_code

    except Exception as e:
        print(f"[flight_utils] Groq extraction failed: {e} — falling back to keyword scan")

    return _keyword_scan(question)


def _keyword_scan(question: str) -> tuple[str | None, str | None]:
    """Original position-based keyword scan as fallback."""
    q = question.lower()
    found: list[tuple[int, str]] = []
    seen_codes: set[str] = set()

    for name in sorted(AIRPORT_CODES, key=len, reverse=True):
        sky_id = AIRPORT_CODES[name][0]
        if sky_id in seen_codes:
            continue
        pos = q.find(name)
        if pos != -1:
            found.append((pos, sky_id))
            seen_codes.add(sky_id)

    found.sort(key=lambda x: x[0])

    origin_code = found[0][1] if len(found) > 0 else None
    dest_code   = found[1][1] if len(found) > 1 else None

    print(f"[flight_utils] Keyword scan → origin: {origin_code}, dest: {dest_code}")
    return origin_code, dest_code


def format_flight_list(flights: list[dict]) -> str:
    """Return a human-readable string of flight results."""
    if not flights:
        return "No flights found for this route and date."

    lines = []
    for i, f in enumerate(flights, 1):
        lines.append(
            f"{i}. [{f['flight_number']}] {f['airline']}\n"
            f"   From     : {f['from_airport']}  →  {f['to_airport']}\n"
            f"   Departure: {f['departure']}   Arrival: {f['arrival']}\n"
            f"   Duration : {f['duration']}   {f['stops']}   Price: {f['price']}\n"
        )
    return "\n".join(lines)
