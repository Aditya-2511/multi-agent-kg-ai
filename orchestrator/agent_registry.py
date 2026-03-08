from agents.sparql_agent import generate_sparql
from agents.kg_agent import kg_agent
from agents.reasoning_agent import generate_explanation
from agents.response_agent import format_response

AGENT_REGISTRY = {
    "sparql_agent": generate_sparql,
    "kg_agent": kg_agent,
    "reasoning_agent": generate_explanation,
    "response_agent": format_response
}