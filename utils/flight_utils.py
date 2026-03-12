from config import AIRPORT_CODES


def extract_airports_from_question(question: str) -> tuple[str | None, str | None]:
    """
    Parse origin and destination IATA codes from a natural language question.
    """
    q = question.lower()
    found: list[tuple[int, str]] = []
    seen_codes: set[str] = set()

    for name in sorted(AIRPORT_CODES, key=len, reverse=True):
        sky_id = AIRPORT_CODES[name][0]   # first element of tuple is IATA code
        if sky_id in seen_codes:
            continue
        pos = q.find(name)
        if pos != -1:
            found.append((pos, sky_id))
            seen_codes.add(sky_id)

    found.sort(key=lambda x: x[0])

    origin_code = found[0][1] if len(found) > 0 else None
    dest_code   = found[1][1] if len(found) > 1 else None

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