import requests
from datetime import date
from config import RAPIDAPI_KEY, FLIGHT_RAPIDAPI_HOST, FLIGHT_BASE_URL, AIRPORT_CODES


def get_flights(
    origin_code: str,
    destination_code: str,
    journey_date: str | None = None,
) -> dict:
    if not journey_date:
        journey_date = date.today().strftime("%Y-%m-%d")

    # ── Look up entityIds ─────────────────────────────────────────────────────
    origin_entry = next(
        (v for v in AIRPORT_CODES.values() if v[0] == origin_code), None
    )
    dest_entry = next(
        (v for v in AIRPORT_CODES.values() if v[0] == destination_code), None
    )

    if not origin_entry or not dest_entry:
        return {"error": f"Entity ID not found for {origin_code} or {destination_code}. Add it to AIRPORT_CODES in config.py."}

    origin_sky_id,   origin_entity_id = origin_entry
    dest_sky_id,     dest_entity_id   = dest_entry

    headers = {
        "X-RapidAPI-Key":  RAPIDAPI_KEY,
        "X-RapidAPI-Host": FLIGHT_RAPIDAPI_HOST,
    }
    params = {
        "originSkyId":        origin_sky_id,
        "destinationSkyId":   dest_sky_id,
        "originEntityId":     origin_entity_id,
        "destinationEntityId":dest_entity_id,
        "date":               journey_date,
        "cabinClass":         "economy",
        "adults":             "1",
        "sortBy":             "best",
        "currency":           "INR",
        "market":             "en-IN",
        "countryCode":        "IN",
    }

    try:
        response = requests.get(
            FLIGHT_BASE_URL, headers=headers, params=params, timeout=60
        )
        # ── print rate limit headers ──────────────────────────────────────────────
        print(f"[flight_service] Rate Limit Headers:")
        print(f"   Total requests allowed : {response.headers.get('x-ratelimit-requests-limit', 'N/A')}")
        print(f"   Requests remaining     : {response.headers.get('x-ratelimit-requests-remaining', 'N/A')}")
        print(f"   Resets at              : {response.headers.get('x-ratelimit-requests-reset', 'N/A')}")
        # ─────────────────────────────────────────────────────────────────────────

        response.raise_for_status()
        data = response.json()
        
        # ── debug: print full response ────────────────────────────────────────────
        import json
        print(f"[flight_service] API response: {json.dumps(data, indent=2)}")
        # ─────────────────────────────────────────────────────────────────────────

    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Please try again."}
    except requests.exceptions.HTTPError as exc:
        return {"error": f"HTTP {exc.response.status_code}: {exc.response.text}"}
    except requests.exceptions.RequestException as exc:
        return {"error": f"Network error: {exc}"}
    except ValueError:
        return {"error": "Invalid JSON in API response."}

    if not data.get("status"):
        return {"error": data.get("message", "API returned an error.")}

    # ── Parse itineraries ─────────────────────────────────────────────────────
    # correct path: data["data"]["itineraries"]
    raw_itineraries = data.get("data", {}).get("itineraries", [])
    flights = []

    for item in raw_itineraries:
        try:
            leg     = item["legs"][0]           # outbound leg only
            segment = leg["segments"][0]        # first segment
            carrier = leg["carriers"]["marketing"][0]

            duration_min = leg["durationInMinutes"]
            duration_str = f"{duration_min // 60}h {duration_min % 60}m"
            stops        = "Non-stop" if leg["stopCount"] == 0 else f"{leg['stopCount']} stop(s)"

            flights.append({
                "flight_number": f"{segment['marketingCarrier']['alternateId']}{segment['flightNumber']}",
                "airline":       carrier["name"],
                "from_airport":  leg["origin"]["displayCode"],
                "to_airport":    leg["destination"]["displayCode"],
                "departure":     leg["departure"],
                "arrival":       leg["arrival"],
                "duration":      duration_str,
                "stops":         stops,
                "price":         item["price"]["formatted"],
                "tags":          item.get("tags", []),
                "journey_date":  journey_date,
            })
        except (KeyError, IndexError):
            continue

    return {
        "flights": flights,
        "meta": {
            "origin_code":      origin_code,
            "destination_code": destination_code,
            "journey_date":     journey_date,
            "total_flights":    len(flights),
        },
    }