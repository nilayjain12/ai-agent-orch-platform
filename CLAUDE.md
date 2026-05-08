# AgentOrch: AI Agent Orchestration Platform

A local-first platform for designing, managing, and executing autonomous multi-agent workflows using LangGraph and Groq LLMs.

## Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy (SQLite), LangChain, LangGraph, Groq API.
- **Frontend**: Next.js (App Router), TypeScript, React Flow, Tailwind CSS, Lucide Icons.

## Setup & Commands

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key (Set in `.env`)

### Backend Setup
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py  # Initialize database with templates
uvicorn app.main:app --reload
```

### Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

### Key URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Project Structure

### Backend (`/backend`)
- `app/api/`: FastAPI routers for agents, workflows, and execution monitoring.
- `app/core/`:
  - `runtime.py`: Core LangGraph logic for compiling and executing workflows.
  - `tools.py`: Python functions available to agents (web search, weather, etc.).
- `app/db/`: Database configuration (`database.py`) and SQLAlchemy models (`models.py`).
- `app/messaging/`: Telegram bot integration for remote workflow interaction.
- `seed.py`: Script to populate the local SQLite database with default agents and workflows.

### Frontend (`/frontend`)
- `src/app/`: Next.js pages:
  - `page.tsx`: Dashboard/Platform Overview with execution history.
  - `builder/page.tsx`: Visual workflow builder using React Flow.
  - `agents/page.tsx`: Agent fleet management.
- `src/lib/api.ts`: Centralized fetch-based API client.

---

## Code Conventions

### Backend
- **Dependency Injection**: Always use `Depends(get_db)` for database sessions in API routes.
- **Schema Validation**: Use Pydantic models (e.g., `AgentCreate`, `WorkflowResponse`) for all request/response bodies.
- **Workflow State**: Workflows use LangGraph's `StateGraph` with a unified `AgentState` (messages, sender, context).
- **Environment**: All secrets (Groq Key, Telegram Token) must be in the root `.env` file and accessed via `os.getenv`.

### Frontend
- **Client Directives**: Use `"use client";` at the top of all pages that utilize React hooks (Next.js default is Server Components).
- **Persistence**: Builder canvas state (nodes/edges) is persisted in `localStorage` until explicitly saved to the database.
- **Custom Nodes**: React Flow custom nodes (`AgentNode`, `TriggerNode`) are styled in `globals.css` with dark-mode glassmorphism.
- **Icons**: Standardize on `lucide-react` for all UI elements.

## Development Workflow
1. **Adding Tools**: Define a new `@tool` function in `backend/app/core/tools.py` and add it to the `AVAILABLE_TOOLS` dictionary.
2. **Adding Agents**: Create agents via the UI or `seed.py`. Model defaults to `llama-3.1-8b-instant`.
3. **Execution**: Workflows run as background tasks in FastAPI to prevent UI blocking. Results are polled by the frontend from the `/executions` endpoint.
