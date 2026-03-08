# agents/planner_agent.py
import ast
from llm.groq_client import client

def plan_agents(state):
    question = state["question"]

    prompt = f"""
You are an AI Planner Agent. Your task is to determine which agents
should be executed to answer the user's question efficiently.

Available agents:
- sparql_agent : Generate SPARQL query from natural language
- kg_agent : Execute SPARQL query on the GraphDB
- reasoning_agent : Convert raw result to human-readable answer
- response_agent : Format the final response for output

Decide which agents to run and output ONLY a Python list of agent names.
Answer ONLY as a Python list.
Do NOT include explanations or quotes around the list.

Question: {question}
Answer:
"""

    response = client.responses.create(
        model="openai/gpt-oss-20b",
        input=prompt
    )

    llm_output = response.output_text.strip()

    # safely parse
    try:
        planned_agents = ast.literal_eval(llm_output)
        if not isinstance(planned_agents, list):
            raise ValueError
    except:
        planned_agents = ["sparql_agent", "kg_agent", "reasoning_agent"]

    # Ensure response_agent is always last for consistent output
    if "response_agent" not in planned_agents:
        planned_agents.append("response_agent")

    state["planned_agents"] = planned_agents
    return state