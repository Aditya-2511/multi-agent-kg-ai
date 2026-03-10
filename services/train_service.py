import requests
from datetime import date

from config import RAPIDAPI_KEY, TRAIN_RAPIDAPI_HOST, TRAIN_BASE_URL

def get_trains(
    source_code: str,
    destination_code: str,
    journey_date: str | None = None,
) -> dict:
    """
    Fetch trains running between two IRCTC station codes on a given date.

    Args:
        source_code      : Origin station code  (e.g. "AII" for Ajmer)
        destination_code : Destination code     (e.g. "JP"  for Jaipur)
        journey_date     : Travel date in yyyy-mm-dd format.
                           Defaults to today if omitted.

    Returns:
        On success → {"trains": [...], "meta": {...}}
        On failure → {"error": "<reason>"}

    Each train dict contains:
        train_number, train_name, train_type,
        from_station, to_station,
        departure (HH:MM), arrival (HH:MM), duration,
        run_days (list[str]), class_types (list[str]),
        special_train (bool), train_date (str)
    """
    if not journey_date:
        journey_date = date.today().strftime("%Y-%m-%d")

    # ── MOCK DATA (remove when quota resets or plan upgraded) ────────────────
    # trains = [
    #     {
    #         "train_number":  "19707",
    #         "train_name":    "ARAVALI EXPRESS",
    #         "train_type":    "EXP",
    #         "from_station":  "AJMER JN",
    #         "to_station":    "JAIPUR JN",
    #         "departure":     "06:10",
    #         "arrival":       "09:45",
    #         "duration":      "3:35",
    #         "run_days":      ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    #         "class_types":   ["SL", "3A", "2A", "1A"],
    #         "special_train": False,
    #         "train_date":    journey_date,
    #     },
    #     {
    #         "train_number":  "12015",
    #         "train_name":    "AJMER SHATABDI",
    #         "train_type":    "SHATABDI",
    #         "from_station":  "AJMER JN",
    #         "to_station":    "JAIPUR JN",
    #         "departure":     "14:25",
    #         "arrival":       "17:10",
    #         "duration":      "2:45",
    #         "run_days":      ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    #         "class_types":   ["CC", "EC"],
    #         "special_train": False,
    #         "train_date":    journey_date,
    #     },
    # ]

    # return {
    #     "trains": trains,
    #     "meta": {
    #         "source_code":      source_code,
    #         "destination_code": destination_code,
    #         "journey_date":     journey_date,
    #         "total_trains":     len(trains),
    #     },
    # }

    # Implementation
    headers = {
        "X-RapidAPI-Key":  RAPIDAPI_KEY,
        "X-RapidAPI-Host": TRAIN_RAPIDAPI_HOST,
    }
    params = {
        "fromStationCode": source_code,
        "toStationCode":   destination_code,
        "dateOfJourney":   journey_date,
    }

    # ── HTTP call ────────────────────────────────────────────────────────────
    try:
        response = requests.get(
            TRAIN_BASE_URL, headers=headers, params=params, timeout=30
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Please try again."}
    except requests.exceptions.HTTPError as exc:
        return {"error": f"HTTP {exc.response.status_code}: {exc.response.text}"}
    except requests.exceptions.RequestException as exc:
        return {"error": f"Network error: {exc}"}
    except ValueError:
        return {"error": "Invalid JSON in API response."}

    # ── API-level failure ────────────────────────────────────────────────────
    if not data.get("status"):
        return {"error": data.get("message", "API returned an error.")}

    # ── Parse trains ─────────────────────────────────────────────────────────
    trains = [
        {
            "train_number": t.get("train_number", "N/A"),
            "train_name":   t.get("train_name",   "N/A"),
            "train_type":   t.get("train_type",   "N/A"),
            "from_station": t.get("from_station_name") or t.get("from", "N/A"),
            "to_station":   t.get("to_station_name")   or t.get("to",   "N/A"),
            "departure":    t.get("from_std", "N/A"),
            "arrival":      t.get("to_std",   "N/A"),
            "duration":     t.get("duration", "N/A"),
            "run_days":     t.get("run_days",    []),
            "class_types":  t.get("class_type",  []),
            "special_train":t.get("special_train", False),
            "train_date":   t.get("train_date",  journey_date),
        }
        for t in data.get("data", [])
    ]

    return {
        "trains": trains,
        "meta": {
            "source_code":      source_code,
            "destination_code": destination_code,
            "journey_date":     journey_date,
            "total_trains":     len(trains),
        },
    }