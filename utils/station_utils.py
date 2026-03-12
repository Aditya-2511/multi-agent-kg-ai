from config import STATION_CODES
from llm.groq_client import chat
import json
import re


def resolve_station_code(city_name: str) -> str | None:
    return STATION_CODES.get(city_name.strip().lower())


def extract_stations_from_question(question: str) -> tuple[str | None, str | None]:
    """
    Uses Groq LLM to extract origin and destination city names from a natural
    language question, then resolves them to IRCTC station codes.

    Falls back to keyword scan if LLM fails.
    """
    # ── 1. Ask Groq to extract city names ────────────────────────────────────
    known_cities = ", ".join(sorted(STATION_CODES.keys()))

    prompt = f"""You are a railway assistant. Extract the origin and destination city names from the user's question.

Known cities: {known_cities}

Rules:
- Return ONLY a JSON object with keys "origin" and "destination"
- Values must exactly match one of the known cities above (lowercase)
- If a city is not mentioned or not in the known list, use null
- No explanation, no markdown, just raw JSON

Examples:
  Question: "trains from ajmer to jaipur" → {{"origin": "ajmer", "destination": "jaipur"}}
  Question: "I want to travel from mumbai to delhi tomorrow" → {{"origin": "mumbai", "destination": "delhi"}}
  Question: "is there a train from pune to anywhere" → {{"origin": "pune", "destination": null}}

Question: "{question}"
"""

    try:
        response = chat(prompt, max_tokens=100)

        # Strip markdown fences if present
        clean = re.sub(r"```(?:json)?|```", "", response).strip()
        data  = json.loads(clean)

        origin_name = data.get("origin")
        dest_name   = data.get("destination")

        print(f"[station_utils] Groq extracted → origin: {origin_name}, destination: {dest_name}")

        origin_code = STATION_CODES.get(origin_name.lower()) if origin_name else None
        dest_code   = STATION_CODES.get(dest_name.lower())   if dest_name   else None

        # ── 2. If Groq resolved both — return immediately ─────────────────────
        if origin_code or dest_code:
            return origin_code, dest_code

    except Exception as e:
        print(f"[station_utils] Groq extraction failed: {e} — falling back to keyword scan")

    # ── 3. Fallback: original keyword scan ───────────────────────────────────
    return _keyword_scan(question)


def _keyword_scan(question: str) -> tuple[str | None, str | None]:
    """Original position-based keyword scan as a reliable fallback."""
    q = question.lower()
    found: list[tuple[int, str]] = []
    seen_codes: set[str] = set()

    for name in sorted(STATION_CODES, key=len, reverse=True):
        code = STATION_CODES[name]
        if code in seen_codes:
            continue
        pos = q.find(name)
        if pos != -1:
            found.append((pos, code))
            seen_codes.add(code)

    found.sort(key=lambda x: x[0])

    source_code = found[0][1] if len(found) > 0 else None
    dest_code   = found[1][1] if len(found) > 1 else None

    print(f"[station_utils] Keyword scan → source: {source_code}, dest: {dest_code}")
    return source_code, dest_code


def format_train_list(trains: list[dict]) -> str:
    if not trains:
        return "No trains found for this route and date."

    lines: list[str] = []
    for i, t in enumerate(trains, 1):
        run_days = ", ".join(t["run_days"])    if t.get("run_days")    else "N/A"
        classes  = ", ".join(t["class_types"]) if t.get("class_types") else "N/A"
        lines.append(
            f"{i}. [{t['train_number']}] {t['train_name']}\n"
            f"   From     : {t['from_station']}  →  {t['to_station']}\n"
            f"   Departure: {t['departure']}   Arrival: {t['arrival']}   "
            f"Duration: {t['duration']}\n"
            f"   Type     : {t['train_type']}   Classes: {classes}\n"
            f"   Runs on  : {run_days}\n"
        )
    return "\n".join(lines)