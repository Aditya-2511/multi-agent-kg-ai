from SPARQLWrapper import SPARQLWrapper, JSON
from config import GRAPHDB_ENDPOINT

sparql = SPARQLWrapper(GRAPHDB_ENDPOINT)


def run_query(query: str) -> dict:
    """Execute a SPARQL SELECT query and return parsed JSON results."""
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        return sparql.query().convert()
    except Exception as exc:
        return {"error": str(exc)}