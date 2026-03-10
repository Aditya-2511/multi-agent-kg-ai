"""
agents/response_agent.py
────────────────────────
Final agent in every pipeline. Packages everything into a clean
structured dict that the FastAPI /ask endpoint returns as JSON.
"""


def format_response(state: dict) -> dict:
    """
    Response node. Always runs last.
    Collects all relevant state keys into formatted_response.
    """
    response = {
        "question":     state.get("question", ""),
        "final_answer": state.get("final_answer", "No answer available."),
        # include raw results only when present
        **({"sparql_query":  state["sparql_query"]}  if "sparql_query"  in state else {}),
        **({"kg_result":     state["kg_result"]}     if "kg_result"     in state else {}),
        **({"train_result":  state["train_result"]}  if "train_result"  in state else {}),
        **({"finance_result":state["finance_result"]}if "finance_result"in state else {}),
        **({"flight_result": state["flight_result"]} if "flight_result" in state else {}),
        **({"weather_result":state["weather_result"]}if "weather_result"in state else {}),
        **({"error":         state["error"]}         if state.get("error") else {}),
    }

    state["formatted_response"] = response
    return state