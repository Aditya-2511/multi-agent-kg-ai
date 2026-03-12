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
from llm.groq_client import chat

# ── Fallback route when nothing can be parsed ─────────────────────────────────
_DEFAULT_SOURCE = "AII"   # Ajmer
_DEFAULT_DEST   = "JP"    # Jaipur

def recommend_train(question: str, trains: list[dict]) -> str:
    """
    Uses Groq to analyze train options and recommend the best one
    based on the user's question/intent.
    """
    if not trains:
        return "No trains available to recommend."

    # Format trains as a readable list for Groq
    train_summary = ""
    for i, t in enumerate(trains, 1):
        classes  = ", ".join(t.get("class_types", []))
        run_days = ", ".join(t.get("run_days", []))
        train_summary += (
            f"{i}. [{t['train_number']}] {t['train_name']} ({t['train_type']})\n"
            f"   Departure: {t['departure']} → Arrival: {t['arrival']} "
            f"| Duration: {t['duration']}\n"
            f"   Classes: {classes} | Runs on: {run_days}\n"
            f"   Special Train: {t['special_train']}\n\n"
        )

    prompt = f"""You are an expert Indian railway assistant.

            A user asked: "{question}"

            Here are the available trains:
            {train_summary}

            Instructions:
            - Carefully read the user's question to understand their intent (fastest, cheapest, AC, morning, etc.)
            - If the user asks for AC trains, list ALL trains that have AC classes (CC, EC, 2A, 3A, 1A) with their details
            - If the user asks for morning trains, list ALL trains departing before 10:00 AM
            - If the user asks for cheapest, list ALL trains with budget classes (SL, 2S) 
            - After listing relevant trains, clearly recommend the BEST one and explain why in 1-2 lines
            - Always mention train name and number for each option
            - Keep the full response concise and helpful
            - Use bullet points for listing multiple trains
            """

    try:
        recommendation = chat(prompt, max_tokens=300)
        print(f"[train_agent] Groq recommendation generated.")
        return recommendation
    except Exception as e:
        print(f"[train_agent] Recommendation failed: {e}")
        return "Could not generate a recommendation at this time."


def generate_nl_answer(question: str, trains: list[dict], recommendation: str) -> str:
    """
    Uses Groq to convert raw train results into a natural language
    conversational response combining the list + recommendation.
    """
    if not trains:
        return "I couldn't find any trains for that route and date."

    # Build compact train summary for Groq
    train_summary = ""
    for i, t in enumerate(trains, 1):
        classes  = ", ".join(t.get("class_types", []))
        run_days = ", ".join(t.get("run_days", []))
        train_summary += (
            f"{i}. [{t['train_number']}] {t['train_name']} ({t['train_type']})\n"
            f"   Departure: {t['departure']} → Arrival: {t['arrival']} "
            f"| Duration: {t['duration']}\n"
            f"   Classes: {classes} | Runs on: {run_days}\n\n"
        )

    prompt = f"""You are a helpful Indian railway assistant having a friendly conversation.

    User asked: "{question}"

    Available trains:
    {train_summary}

    AI Recommendation already generated:
    {recommendation}

    Your task:
    - Write a natural, conversational response (2-4 sentences) that directly answers the user's question
    - Mention the total number of trains found
    - Highlight the recommended train naturally in the sentence (name + number + key detail like duration or departure)
    - If multiple trains are relevant to the user's intent, briefly mention them too
    - End with a helpful tip if appropriate (e.g. booking advice, best class, runs daily or not)
    - Do NOT use bullet points or lists — write in flowing paragraph form only
    - Sound like a knowledgeable friend, not a database printout
    """

    try:
        nl_answer = chat(prompt, max_tokens=300)
        print(f"[train_agent] Natural language answer generated.")
        return nl_answer
    except Exception as e:
        print(f"[train_agent] NL answer generation failed: {e}")
        return None   # None signals reasoning_agent to fall back to raw list

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
    
    if not source_code or not dest_code:
        parsed_src, parsed_dst = extract_stations_from_question(question)
        source_code = source_code or parsed_src or _DEFAULT_SOURCE
        dest_code   = dest_code   or parsed_dst or _DEFAULT_DEST

    # ── Fail early if cities not recognised ──────────────────────────────────
    if not source_code or not dest_code:
        state["train_result"] = []
        state["error"]        = f"Could not identify origin or destination station from: '{question}'. Please mention valid city names."
        state["train_answer"] = state["error"]
        return state

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

    # ── 5. Groq Train Recommendation ─────────────────────────────────────────
    recommendation = recommend_train(question, trains)
    state["train_recommendation"] = recommendation
    print(f"[train_agent] Recommendation: {recommendation}")

    # ── 6. Groq Natural Language Answer ──────────────────────────────────────
    nl_answer = generate_nl_answer(question, trains, recommendation)
    state["train_nl_answer"] = nl_answer

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

