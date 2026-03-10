"""
agents/sparql_agent.py
Generate a SPARQL query from the user's natural language question.
"""
from llm.groq_client import chat


_PROMPT = """
You are a SPARQL expert. Convert the user's question into a valid SPARQL SELECT query
for a company knowledge graph that contains entities like companies, founders, employees,
products, and relationships between them.

Return ONLY the SPARQL query. No explanation.

Question: {question}
""".strip()


def generate_sparql(state: dict) -> dict:
    question = state.get("question", "")
    sparql_query = chat(_PROMPT.format(question=question), max_tokens=256)
    state["sparql_query"] = sparql_query
    print(f"[sparql_agent] Query generated.")
    return state