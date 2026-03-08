# agents/response_agent.py

def format_response(state):
    """
    Formats the final response depending on which outputs are available.
    Works even if only sparql_query or kg_result exists.
    """
    response = {
        "question": state.get("question", ""),
        "sparql_query": state.get("sparql_query", None),
        "kg_result": state.get("kg_result", None),
        "final_answer": state.get("final_answer", None)
    }

    # Save in state for consistency
    state["formatted_response"] = response
    return state