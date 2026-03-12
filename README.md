# multi-agent-kg-ai

A multi-agent AI system built with FastAPI, LangGraph-style state pipeline, Groq LLM, and RapidAPI integrations. Supports natural language queries for train schedules, flight information, and knowledge graph lookups.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Train Data | IRCTC RapidAPI |
| Flight Data | Sky Scrapper RapidAPI |
| Knowledge Graph | GraphDB (SPARQL) |
| Runtime | Python 3.11+ |

---

## Features

- **Natural language understanding** — Groq extracts cities, dates and intent from free-text questions
- **Train agent** — fetches schedules, recommends best train, generates conversational answers
- **Flight agent** — searches flights between cities with AI-powered recommendations
- **Follow-up handling** — session-based memory so users can ask follow-up questions without repeating context
- **Knowledge graph** — SPARQL queries against GraphDB for company/entity data

---

## Folder Structure

```
multi-agent-kg-ai/
├── api/
│   └── main.py                  # FastAPI app, /ask and /health endpoints
├── agents/
│   ├── planner_agent.py         # LLM selects agent pipeline
│   ├── train_agent.py           # Train schedule + Groq recommendation
│   ├── flight_agent.py          # Flight search
│   ├── followup_agent.py        # Session-based follow-up handling
│   ├── sparql_agent.py          # Generates SPARQL query from question
│   ├── kg_agent.py              # Executes SPARQL on GraphDB
│   ├── reasoning_agent.py       # Converts raw results to natural language
│   └── response_agent.py        # Packages final JSON response
├── orchestrator/
│   ├── agent_controller.py      # Runs agent pipeline
│   └── agent_registry.py        # Maps agent names to functions
├── services/
│   ├── train_service.py         # IRCTC RapidAPI integration
│   └── flight_service.py        # Sky Scrapper RapidAPI integration
├── graphdb/
│   └── graphdb_client.py        # SPARQLWrapper client
├── llm/
│   └── groq_client.py           # Groq LLM wrapper
├── utils/
│   ├── station_utils.py         # Train station code resolver
│   └── flight_utils.py          # Airport code resolver
├── config.py                    # Constants, station codes, airport codes
├── .env                         # API keys (not committed)
├── .env.example                 # Environment variable template
└── requirements.txt
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/multi-agent-kg-ai.git
cd multi-agent-kg-ai
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your API keys:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
RAPIDAPI_KEY=your_rapidapi_key
GRAPHDB_ENDPOINT=http://localhost:7200/repositories/company_kg
GRAPHDB_UPDATE_ENDPOINT=http://localhost:7200/repositories/company_kg/statements
```

---

## Running the Server

```bash
uvicorn api.main:app --reload
```

Server runs at: `http://127.0.0.1:8000`

Interactive API docs: `http://127.0.0.1:8000/docs`

---

## API Endpoints

### `POST /ask`

Ask a natural language question.

**Request body:**
```json
{
  "question": "trains from ajmer to jaipur",
  "journey_date": "2026-03-15",
  "session_id": "my-session"
}
```

**Response:**
```json
{
  "question": "trains from ajmer to jaipur",
  "final_answer": "We found 5 trains from Ajmer to Jaipur...",
  "train_result": [...]
}
```

---

### `GET /health`

Check server status.

```json
{ "status": "ok" }
```

---

### `DELETE /session/{session_id}`

Clear a session's conversation history.

```json
{ "status": "cleared", "session_id": "my-session" }
```

---

## Example Questions

### Train Queries
{"question": "trains from ajmer to jaipur", "journey_date": "2026-03-15", "session_id": "s1"}
{"question": "fastest train from ajmer to jaipur", "journey_date": "2026-03-15", "session_id": "s1"}

### Train Follow-ups (same session_id)
{"question": "which of these has AC coaches?", "session_id": "s1"}
{"question": "which trains run on Sunday?", "session_id": "s1"}
{"question": "which one is cheapest?", "session_id": "s1"}

### Flight Queries
{"question": "flights from london to new york", "journey_date": "2026-03-13", "session_id": "f1"}

### Flight Follow-ups (same session_id)
{"question": "which is the cheapest flight?", "session_id": "f1"}
{"question": "any non-stop flights?", "session_id": "f1"}
{"question": "what is the fastest option?", "session_id": "f1"}

