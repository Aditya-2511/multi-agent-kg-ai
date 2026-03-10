from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from orchestrator.agent_controller import run_agents

app = FastAPI(
    title="Multi-Agent KG AI",
    description="Knowledge Graph + multi-domain AI agent pipeline",
    version="1.0.0",
)


class QueryRequest(BaseModel):
    question: str
    journey_date: str | None = None


@app.post("/ask")
def ask_agent(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    state = run_agents(request.question, request.journey_date)
    return state.get("formatted_response", state)


@app.get("/health")
def health():
    return {"status": "ok"}