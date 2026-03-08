# orchestrator/agent_controller.py
from orchestrator.agent_registry import AGENT_REGISTRY
from agents.planner_agent import plan_agents

def run_agents(question):
    state = {"question": question}

    # Planner decides which agents to run
    state = plan_agents(state)
    agents_to_run = state.get("planned_agents", [])

    print("Planner selected agents:", agents_to_run)

    # Run each agent in sequence
    for agent_name in agents_to_run:
        print(f"Running {agent_name}...")
        agent_function = AGENT_REGISTRY[agent_name]
        state = agent_function(state)

    return state