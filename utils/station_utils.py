from config import STATION_CODES


def resolve_station_code(city_name: str) -> str | None:
    """
    Resolve a city / station name string to its IRCTC station code.
    Returns None if not found.
    """
    return STATION_CODES.get(city_name.strip().lower())


def extract_stations_from_question(question: str) -> tuple[str | None, str | None]:
    """
    Parse source and destination station codes from a natural language question.

    Strategy:
      - Scan for every known city/station name in the question text.
      - Sort matches by their position in the string (left → right = source → destination).
      - Return (source_code, destination_code). Either may be None if not found.

    Examples:
      "trains from ajmer to jaipur"   → ("AII", "JP")
      "mumbai to delhi trains"        → ("MMCT", "NDLS")
      "is there a train from pune"    → ("PUNE", None)
    """
    q = question.lower()
    found: list[tuple[int, str]] = []   # (position, station_code)
    seen_codes: set[str] = set()

    # Sort names by length descending so "mumbai central" matches before "mumbai"
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

    return source_code, dest_code


def format_train_list(trains: list[dict]) -> str:
    """Return a human-readable multi-line string of train results."""
    if not trains:
        return "No trains found for this route and date."

    lines: list[str] = []
    for i, t in enumerate(trains, 1):
        run_days = ", ".join(t["run_days"])  if t.get("run_days")   else "N/A"
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