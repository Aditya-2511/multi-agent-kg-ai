"""
agents/planner_agent.py
───────────────────────
Planner Agent — uses the LLM to decide which agents should run for a question.
Falls back to keyword-based routing if the LLM returns an unparseable response.
"""

import ast
from llm.groq_client import chat
from agents.followup_agent import is_followup_question


_PROMPT_TEMPLATE = """
You are an AI Planner Agent. Your job is to decide which agents to run
to answer the user's question.

Available agents:
  - sparql_agent    : Generates a SPARQL query from natural language
  - kg_agent        : Executes the SPARQL query on GraphDB
  - train_agent     : Gets train schedules between two cities
  - flight_agent    : Gets flight information between two cities
  - reasoning_agent : Converts raw data into a natural-language answer
  - response_agent  : Formats the final structured response

Routing rules:
  - Train schedule question    → train_agent   → reasoning_agent → response_agent
  - Flight question            → flight_agent  → reasoning_agent → response_agent
  - Knowledge graph / company  → sparql_agent  → kg_agent → reasoning_agent → response_agent

Output ONLY a valid Python list of agent name strings. No explanation.

Question: {question}
Answer:
""".strip()

def _is_ambiguous(question: str) -> bool:
    """
    Detect vague questions with no domain or city context.
    """
    q = question.lower()
    # Only REAL domain keywords — not generic question words
    domain_keywords = (
        "train", "rail", "railway", "irctc",
        "flight", "airline", "fly", "airport",
        "weather", "stock", "price", "share",
        "company", "founder", "employee",
        "from", "to",   # ← city route indicator
    )
    return not any(w in q for w in domain_keywords)

def plan_agents(state: dict) -> dict:
    """
    Planner node. Calls the LLM to select the agent sequence,
    then validates / repairs the list before writing it to state.
    """
    question = state.get("question", "")
    conversation_history = state.get("conversation_history", [])

    # ── Check for follow-up first ─────────────────────────────────────────
    if is_followup_question(question, conversation_history):
        print(f"[planner] Follow-up detected → followup_agent pipeline")
        state["planned_agents"] = [
            "followup_agent",
            "response_agent",   # skip reasoning_agent — answer already in final_answer
        ]
        return state
    
    # ── Check for ambiguous question with no context ──────────────────────
    if _is_ambiguous(question) and not conversation_history:
        print(f"[planner] Ambiguous question with no context")
        state["planned_agents"] = ["response_agent"]
        state["final_answer"]   = (
            "I'm not sure what you're looking for. Could you please provide "
            "more details? For example: 'trains from Ajmer to Jaipur' or "
            "'flights from London to New York'."
        )
        return state

    # ── 1. Ask the LLM ───────────────────────────────────────────────────────
    try:
        llm_output = chat(_PROMPT_TEMPLATE.format(question=question), max_tokens=128)
        planned_agents: list[str] = ast.literal_eval(llm_output)
        if not isinstance(planned_agents, list):
            raise ValueError("LLM output is not a list")
    except Exception:
        # ── 2. Keyword fallback ───────────────────────────────────────────────
        planned_agents = _keyword_fallback(question)

    # ── 3. Guarantee reasoning_agent precedes response_agent ─────────────────
    if "reasoning_agent" not in planned_agents:
        planned_agents.append("reasoning_agent")

    # response_agent must always be last
    if "response_agent" in planned_agents:
        planned_agents.remove("response_agent")
    planned_agents.append("response_agent")

    state["planned_agents"] = planned_agents
    return state


def _keyword_fallback(question: str) -> list[str]:
    q = question.lower()
    if any(w in q for w in ("train", "rail", "railway", "irctc")):
        return ["train_agent", "reasoning_agent", "response_agent"]
    if any(w in q for w in ("flight", "airline", "fly", "airport")):
        return ["flight_agent", "reasoning_agent", "response_agent"]
    # default → knowledge graph
    return ["sparql_agent", "kg_agent", "reasoning_agent", "response_agent"]