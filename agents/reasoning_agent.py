"""
agents/reasoning_agent.py
─────────────────────────
Converts raw agent output (KG result, train list, etc.)
into a single natural-language sentence / paragraph.
"""

from llm.groq_client import chat


def generate_explanation(state: dict) -> dict:
    """
    Reasoning node. Inspects state for known result keys and
    generates a human-readable final_answer.
    """

    # ── Skip if follow-up already handled ────────────────────────────────────
    if state.get("is_followup"):
        print("[reasoning_agent] Skipping — follow-up already answered.")
        return state

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

    # ── Train result ──────────────────────────────────────────────────────────
    elif "train_result" in state:
        trains = state["train_result"]
        if not trains:
            state["final_answer"] = "No trains were found for that route and date."
        else:
            # ── Try Groq natural language answer first ────────────────────
            nl_answer = state.get("train_nl_answer")
            if nl_answer:
                state["final_answer"] = nl_answer

            # ── Fallback to raw list + recommendation ─────────────────────
            else:
                lines = [
                    f"  • [{t['train_number']}] {t['train_name']} — "
                    f"Departs {t['departure']}, Arrives {t['arrival']} "
                    f"(Duration: {t['duration']})"
                    for t in trains[:10]
                ]
                header = (
                    f"Found {len(trains)} train(s) for your route:\n"
                    if len(trains) <= 10
                    else f"Showing 10 of {len(trains)} trains found:\n"
                )
                train_list = header + "\n".join(lines)

                recommendation = state.get("train_recommendation", "")
                if recommendation:
                    state["final_answer"] = (
                        train_list
                        + "\n\n💡 AI Recommendation:\n"
                        + recommendation
                    )
                else:
                    state["final_answer"] = train_list

    # ── Flight result ─────────────────────────────────────────────────────────
    elif "flight_result" in state:
        flights = state["flight_result"]
        if not flights:
            state["final_answer"] = (
                "No flights found. This may be because the requested date is outside "
                "the available booking window. Try a date within the next 2–3 days."
            )
        else:
            lines = [
                f"  • {f.get('airline', 'N/A')} {f.get('flight_number', '')} — "
                f"Departs {f.get('departure', 'N/A')}, Arrives {f.get('arrival', 'N/A')}"
                for f in flights[:10]
            ]
            state["final_answer"] = "Available flights:\n" + "\n".join(lines)

    else:
        state["final_answer"] = "No data was available to generate an answer."

    print(f"[reasoning_agent] final_answer set.")
    return state