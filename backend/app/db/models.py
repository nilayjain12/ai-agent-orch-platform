from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    role = Column(String)
    system_prompt = Column(Text)
    model_name = Column(String, default="llama-3.1-8b-instant")
    temperature = Column(String, default="0.7")
    tools = Column(JSON, default=list)  # List of tool names like ["web_search", "calculator"]
    memory_enabled = Column(Boolean, default=True)
    memory_config = Column(JSON, default=dict)
    channels = Column(JSON, default=list)  # List of channels like ["Telegram"]
    schedule = Column(String)
    interaction_rules = Column(Text)
    guardrails = Column(Text)
    active = Column(Boolean, default=True)

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    nodes = Column(JSON, default=list)  # React Flow nodes
    edges = Column(JSON, default=list)  # React Flow edges
    active = Column(Boolean, default=True)

class Execution(Base):
    __tablename__ = "executions"
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=True)
    status = Column(String, default="running")  # running, completed, failed
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)

class LogEntry(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    level = Column(String, default="info")
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
