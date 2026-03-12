from agents.sparql_agent    import generate_sparql
from agents.kg_agent        import kg_agent
from agents.reasoning_agent import generate_explanation
from agents.response_agent  import format_response
from agents.train_agent     import train_agent
from agents.flight_agent    import flight_agent
from agents.followup_agent import followup_agent

AGENT_REGISTRY: dict = {
    "followup_agent":  followup_agent,
    "sparql_agent":    generate_sparql,
    "kg_agent":        kg_agent,
    "reasoning_agent": generate_explanation,
    "response_agent":  format_response,
    "train_agent":     train_agent,
    "flight_agent":    flight_agent,
}