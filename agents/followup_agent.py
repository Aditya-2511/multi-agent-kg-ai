"""
agents/followup_agent.py
────────────────────────
Handles follow-up questions about previously fetched train results.

State contract
──────────────
Reads:
    question             (str)        Follow-up question
    conversation_history (list[dict]) Previous Q&A turns
    train_result         (list[dict]) Trains from previous turn (if any)

Writes:
    final_answer  (str)   Direct answer to follow-up
    is_followup   (bool)  Flag so reasoning_agent skips re-processing
"""

from llm.groq_client import chat


def is_followup_question(question: str, conversation_history: list[dict]) -> bool:
    if not conversation_history:
        return False

    history_text = "\n".join([
        f"User: {turn['question']}\nAssistant: {turn['answer']}"
        for turn in conversation_history[-3:]
    ])

    prompt = f"""You are a conversation analyzer.

            Previous conversation:
            {history_text}

            New question: "{question}"

            Does the new question reference or ask about the previous results without mentioning a new city or route?

            Examples that ARE follow-ups:
            - "which one is cheapest?"
            - "which of these has AC coaches?"
            - "which runs on Sunday?"
            - "does any have sleeper class?"
            - "what about the fastest one?"

            Examples that are NOT follow-ups:
            - "flights from delhi to mumbai"
            - "trains from mumbai to pune"
            - "what is the weather today"

            Reply with only: YES or NO
            """
    try:
        response = chat(prompt, max_tokens=5).strip().upper()
        # extract YES or NO cleanly in case Groq adds extra text
        result = "YES" if "YES" in response else "NO"
        print(f"[followup_agent] Is follow-up: {result}")
        return result == "YES"
    except Exception as e:
        print(f"[followup_agent] Detection failed: {e}")
        return False


def answer_followup(
    question: str,
    train_result: list[dict],
    conversation_history: list[dict],
) -> str:
    # ── Try flight result if no train result ──────────────────────────────
    flight_result = _extract_flights_from_history(conversation_history)
    result_data   = train_result or flight_result

    if not result_data:
        return "I don't have any previous results to answer that. Please ask a new search question first."

    data_summary = ""
    for i, item in enumerate(result_data[:10], 1):
        # train fields
        if "train_number" in item:
            classes  = ", ".join(item.get("class_types", []))
            run_days = ", ".join(item.get("run_days", []))
            data_summary += (
                f"{i}. [{item['train_number']}] {item['train_name']} ({item['train_type']})\n"
                f"   Departure: {item['departure']} → Arrival: {item['arrival']} | Duration: {item['duration']}\n"
                f"   Classes: {classes} | Runs on: {run_days}\n\n"
            )
        # flight fields
        elif "flight_number" in item:
            data_summary += (
                f"{i}. [{item['flight_number']}] {item['airline']}\n"
                f"   {item['from_airport']} → {item['to_airport']}\n"
                f"   Departure: {item['departure']} | Duration: {item['duration']} | {item['stops']} | Price: {item['price']}\n\n"
            )

    history_text = "\n".join([
        f"User: {turn['question']}\nAssistant: {turn['answer']}"
        for turn in conversation_history[-3:]
    ])

    prompt = f"""You are a helpful travel assistant.

            Previous conversation:
            {history_text}

            Data already fetched:
            {data_summary}

            User follow-up question: "{question}"

            Instructions:
            - Answer ONLY using the data provided above
            - Be conversational and concise (2-3 sentences max)
            - Mention flight/train name and number when referring to specific options
            - If the question cannot be answered from the data, say so politely
            """

    try:
        answer = chat(prompt, max_tokens=250)
        return answer
    except Exception as e:
        print(f"[followup_agent] Answer failed: {e}")
        return "Sorry, I couldn't process your follow-up question."


def followup_agent(state: dict) -> dict:
    question             = state.get("question", "")
    conversation_history = state.get("conversation_history", [])
    train_result         = state.get("train_result") or \
                           _extract_trains_from_history(conversation_history)

    # ── No need to re-detect — planner already confirmed it's a follow-up ────
    state["is_followup"]  = True
    state["final_answer"] = answer_followup(question, train_result, conversation_history)
    print(f"[followup_agent] Follow-up answer generated.")
    print(f"[followup_agent] Handled as follow-up.")
    return state


def _extract_trains_from_history(conversation_history: list[dict]) -> list[dict]:
    """Extract train_result stored from a previous turn if available."""
    for turn in reversed(conversation_history):
        if turn.get("train_result"):
            return turn["train_result"]
    return []

def _extract_flights_from_history(conversation_history: list[dict]) -> list[dict]:
    """Extract flight_result stored from a previous turn if available."""
    for turn in reversed(conversation_history):
        if turn.get("flight_result"):
            return turn["flight_result"]
    return []
