# AI Agent Orchestration Platform

A fully functional, multi-agent orchestration platform built with a zero-cost local stack.

## Architecture & Technology Choices
- **Frontend**: Next.js, React, TailwindCSS, React Flow (for the visual workflow builder). Chosen for its robust component ecosystem and drag-and-drop capabilities.
- **Backend**: FastAPI, Python, AsyncIO. Selected because orchestration frameworks like LangGraph are Python-native, and FastAPI handles async/websockets well.
- **Runtime**: LangGraph. Ideal for stateful, complex graph orchestration and multi-agent coordination.
- **Database**: PostgreSQL (for persistent memory of agents, workflows, execution logs) and Redis (for pub/sub real-time messaging).
- **LLM**: GroqCloud. Provides extremely fast and free inference (requires API key).
- **Messaging**: Telegram Bot API. Simplest integration for external user-agent communication.

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (if running frontend locally)
- Python 3.11+ (if running backend locally)
- A Groq API Key (get one free at https://console.groq.com)
- A Telegram Bot Token (get one from @BotFather on Telegram)

### One-Command Setup

1. Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   cp .env.example .env
   ```

2. Start the entire stack using Docker Compose:
   ```bash
   docker compose up --build
   ```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Execution Instructions
- **Create Agents**: Navigate to the "Agents" tab in the frontend to define agents, their roles, and attach tools.
- **Execute Workflows**: Use the "Builder" to connect agents, trigger conditions, and save the workflow. Click "Execute" to run it.
- **Test Messaging**: Message your configured Telegram bot. The "Customer Support" workflow will automatically intercept and process it.

## Extensibility Guide
- **Add Tools**: Create a new tool definition in `backend/app/core/tools.py` using LangChain's `@tool` decorator.
- **Add Workflow Templates**: Define new templates in the database seeding logic or via the visual builder.
- **Add Agent Types**: Expand the `Agent` model and update `backend/app/core/runtime.py` to handle specialized prompts or capabilities.
