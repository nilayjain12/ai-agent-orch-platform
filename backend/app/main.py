import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import threading
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load env vars from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.api import agents, workflows, monitoring
from app.db.database import init_db
from app.messaging.telegram_bot import start_telegram_bot

# Initialize database
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start telegram bot in background thread since it's a blocking polling loop
    try:
        thread = threading.Thread(target=start_telegram_bot, daemon=True)
        thread.start()
        logger.info("Telegram bot thread started.")
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")
    yield
    # Cleanup on shutdown

app = FastAPI(title="AI Agent Orchestration Platform", lifespan=lifespan)

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Agent Orchestration Platform API"}

app.include_router(agents.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")

# WebSockets for live monitoring
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def get_manager():
    return manager

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
