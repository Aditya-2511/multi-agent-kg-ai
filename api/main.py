from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from orchestrator.agent_controller import run_agents

app = FastAPI(
    title="Multi-Agent KG AI",
    description="Knowledge Graph + multi-domain AI agent pipeline",
    version="1.0.0",
)

# ── In-memory session store ───────────────────────────────────────────────────
session_store: dict = {}


class QueryRequest(BaseModel):
    question:    str
    journey_date: str | None = None
    session_id:   str | None = None   # ← new


@app.post("/ask")
def ask_agent(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # ── Load previous conversation history from session ───────────────────────
    session_id           = request.session_id
    conversation_history = []

    if session_id and session_id in session_store:
        conversation_history = session_store[session_id]
        print(f"[session] Loaded {len(conversation_history)} turn(s) for session '{session_id}'")
    elif session_id:
        print(f"[session] New session started: '{session_id}'")

    # ── Run agents ────────────────────────────────────────────────────────────
    state = run_agents(
        request.question,
        request.journey_date,
        conversation_history,
    )

    # ── Save this turn into session store ────────────────────────────────────
    if session_id:
        turn = {
            "question":    request.question,
            "answer":      state.get("formatted_response", {}).get("final_answer", ""),
            "train_result": state.get("train_result", []),
        }
        if session_id not in session_store:
            session_store[session_id] = []
        session_store[session_id].append(turn)
        print(f"[session] Saved turn {len(session_store[session_id])} for session '{session_id}'")

    return state.get("formatted_response", state)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear a session's conversation history."""
    if session_id in session_store:
        del session_store[session_id]
        return {"status": "cleared", "session_id": session_id}
    return {"status": "not_found", "session_id": session_id}