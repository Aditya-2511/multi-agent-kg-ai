from orchestrator.agent_controller import run_agents

# question = "Who founded Microsoft?"
question = "Give me SPARQL query for Microsoft founders"

state = run_agents(question)

# Print final answer
print("\nFinal Answer:")
print(state.get("formatted_response", state.get("final_answer")))
