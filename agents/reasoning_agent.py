"""
agents/reasoning_agent.py
─────────────────────────
Converts raw agent output (KG result, finance data, train list, etc.)
into a single natural-language sentence / paragraph.
"""

from llm.groq_client import chat


def generate_explanation(state: dict) -> dict:
    """
    Reasoning node. Inspects state for known result keys and
    generates a human-readable final_answer.
    """

    question = state.get("question", "")

    # ── Knowledge Graph result ────────────────────────────────────────────────
    if "kg_result" in state:
        prompt = f"""
User question: {question}

GraphDB result: {state["kg_result"]}

Write ONE short, natural sentence that answers the question using the result above.
Return only the sentence — no preamble, no quotes.
        """.strip()
        state["final_answer"] = chat(prompt)

    # ── Finance result ────────────────────────────────────────────────────────
    elif "finance_result" in state:
        data = state["finance_result"]
        state["final_answer"] = (
            f"The stock price of {data.get('ticker', 'N/A')} is "
            f"${data.get('price', 'N/A')} "
            f"with a market cap of {data.get('market_cap', 'N/A')}."
        )

    # ── Train result ──────────────────────────────────────────────────────────
    elif "train_result" in state:
        trains = state["train_result"]
        if not trains:
            state["final_answer"] = "No trains were found for that route and date."
        else:
            lines = [
                f"  • [{t['train_number']}] {t['train_name']} — "
                f"Departs {t['departure']}, Arrives {t['arrival']} "
                f"(Duration: {t['duration']})"
                for t in trains[:10]   # cap at 10 to avoid token overflow
            ]
            header = (
                f"Found {len(trains)} train(s) for your route:\n"
                if len(trains) <= 10
                else f"Showing 10 of {len(trains)} trains found:\n"
            )
            state["final_answer"] = header + "\n".join(lines)

    # ── Flight result ─────────────────────────────────────────────────────────
    elif "flight_result" in state:
        flights = state["flight_result"]
        if not flights:
            state["final_answer"] = "No flights found for that route and date."
        else:
            lines = [
                f"  • {f.get('airline', 'N/A')} {f.get('flight_number', '')} — "
                f"Departs {f.get('departure', 'N/A')}, Arrives {f.get('arrival', 'N/A')}"
                for f in flights[:10]
            ]
            state["final_answer"] = "Available flights:\n" + "\n".join(lines)

    # ── Weather result ────────────────────────────────────────────────────────
    elif "weather_result" in state:
        w = state["weather_result"]
        state["final_answer"] = (
            f"Current weather in {w.get('city', 'N/A')}: "
            f"{w.get('description', 'N/A')}, "
            f"{w.get('temperature', 'N/A')}°C, "
            f"humidity {w.get('humidity', 'N/A')}%."
        )

    else:
        state["final_answer"] = "No data was available to generate an answer."

    print(f"[reasoning_agent] final_answer set.")
    return state