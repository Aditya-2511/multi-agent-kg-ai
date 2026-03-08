from graphdb.graphdb_client import run_query

def kg_agent(state):

    query = state["sparql_query"]

    result = run_query(query)

    bindings = result["results"]["bindings"]

    if bindings:
        value = list(bindings[0].values())[0]["value"]
        result_value = value.split("#")[-1]
    else:
        return "No result"
    
    state["kg_result"] = result_value

    return state