from llm.groq_client import client

def generate_sparql(state):

    question = state["question"]

    prompt = f"""
You are a SPARQL expert.

Knowledge Graph Schema:

Person → founded → Company
Person → CEO_of → Company
Company → founded_year → Year

Prefixes:
PREFIX : <http://example.org/company#>

Example triples:

:Bill_Gates :founded :Microsoft .
:Satya_Nadella :CEO_of :Microsoft .

Generate SPARQL for the question.

Question: {question}

Return ONLY SPARQL query.
"""

    response = client.responses.create(
        # model="openai/gpt-oss-20b",
        model="llama-3.3-70b-versatile",
        input=prompt
    )

    sparql_query = response.output_text

    # Remove markdown code blocks if present
    sparql_query = sparql_query.replace("```sparql", "")
    sparql_query = sparql_query.replace("```", "")
    sparql_query = sparql_query.strip()

    state["sparql_query"] = sparql_query

    return state