from llm.groq_client import client

def generate_explanation(state):
    question = state["question"]
    result = state["kg_result"]

    prompt = f"""
User Question:
{question}

GraphDB Result:
{result}

Convert the result into a short natural sentence.

Example:
Founder of Microsoft is Bill Gates.

Return only the final sentence.
"""

    response = client.responses.create(
        model="openai/gpt-oss-20b",
        input=prompt
    )

    state["final_answer"] = response.output_text.strip()

    return state