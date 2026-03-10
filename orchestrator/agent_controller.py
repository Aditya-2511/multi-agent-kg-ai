from agents.planner_agent       import plan_agents
from orchestrator.agent_registry import AGENT_REGISTRY


def run_agents(question: str, 
               journey_date: str | None = None) -> dict:
    """
    Main entry point called by the FastAPI layer.

    1. Builds initial state with the user's question.
    2. Runs planner_agent to decide which agents are needed.
    3. Executes each selected agent in order.
    4. Returns the final state dict (formatted_response key is the API response).
    """
    state: dict = {"question": question}

    if journey_date:
        state["journey_date"] = journey_date   # ← now train_agent can read it

    # ── Planner decides the agent sequence ───────────────────────────────────
    state = plan_agents(state)
    agents_to_run: list[str] = state.get("planned_agents", [])
    print(f"[controller] Pipeline: {' → '.join(agents_to_run)}")

    # ── Run each agent ────────────────────────────────────────────────────────
    for agent_name in agents_to_run:
        if agent_name not in AGENT_REGISTRY:
            print(f"[controller] WARNING: '{agent_name}' not in registry — skipping.")
            continue

        print(f"[controller] Running {agent_name} ...")

        state = AGENT_REGISTRY[agent_name](state)

        if not isinstance(state, dict):
            raise ValueError(
                f"Agent '{agent_name}' returned {type(state).__name__} instead of dict."
            )
        
    return state