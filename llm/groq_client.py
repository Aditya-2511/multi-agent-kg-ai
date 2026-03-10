from openai import OpenAI
from config import GROQ_API_KEY, GROQ_MODEL

# Groq exposes an OpenAI-compatible endpoint.
# Use client.chat.completions.create() — NOT client.responses.create()
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def chat(prompt: str, model: str = GROQ_MODEL, max_tokens: int = 512) -> str:
    """
    Thin wrapper around the Groq chat completion endpoint.

    Args:
        prompt     : User message text.
        model      : Groq model ID (default from config).
        max_tokens : Maximum tokens in the response.

    Returns:
        Response text as a plain string.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()