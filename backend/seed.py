import os
from app.db.database import SessionLocal, init_db
from app.db.models import Agent, Workflow

def seed():
    init_db()
    db = SessionLocal()

    # Create Agents
    agents = [
        Agent(
            name="Research Agent",
            description="Gathers information from the web.",
            role="Researcher",
            system_prompt="You are a meticulous researcher. Use the web_search tool to find accurate information on the requested topic. Provide detailed findings.",
            tools=["web_search"]
        ),
        Agent(
            name="Summarizer Agent",
            description="Summarizes research findings.",
            role="Summarizer",
            system_prompt="You are an expert summarizer. Take the research findings provided to you and create a concise, well-structured summary report.",
            tools=[]
        ),
        Agent(
            name="Reviewer Agent",
            description="Reviews the final summary.",
            role="Reviewer",
            system_prompt="You are a strict reviewer. Check the summary for clarity and completeness. Output the final, polished result.",
            tools=[]
        ),
        Agent(
            name="Intake Agent",
            description="Classifies customer issues.",
            role="Intake",
            system_prompt="You are a customer support intake agent. Classify the user's issue and gather preliminary information.",
            tools=[]
        ),
        Agent(
            name="Knowledge Agent",
            description="Answers support questions.",
            role="Support",
            system_prompt="You are a helpful support agent. Answer the user's questions based on general knowledge.",
            tools=["web_search"]
        ),
        Agent(
            name="Escalation Agent",
            description="Handles unresolved cases.",
            role="Escalation",
            system_prompt="You handle cases that the Knowledge Agent cannot resolve. Apologize and inform the user that a human agent will contact them shortly.",
            tools=[]
        )
    ]

    for a in agents:
        existing = db.query(Agent).filter(Agent.name == a.name).first()
        if not existing:
            db.add(a)
    db.commit()
    
    # Reload agents to get IDs
    db_agents = db.query(Agent).all()
    agent_map = {a.name: a.id for a in db_agents}

    # Workflow 1: Research Workflow
    wf1_nodes = [
        {"id": "trigger", "type": "trigger", "position": {"x": 100, "y": 100}},
        {"id": "agent_1", "type": "agent", "position": {"x": 300, "y": 100}, "data": {"agent_id": agent_map.get("Research Agent")}},
        {"id": "agent_2", "type": "agent", "position": {"x": 500, "y": 100}, "data": {"agent_id": agent_map.get("Summarizer Agent")}},
        {"id": "agent_3", "type": "agent", "position": {"x": 700, "y": 100}, "data": {"agent_id": agent_map.get("Reviewer Agent")}}
    ]
    wf1_edges = [
        {"id": "e1", "source": "trigger", "target": "agent_1"},
        {"id": "e2", "source": "agent_1", "target": "agent_2"},
        {"id": "e3", "source": "agent_2", "target": "agent_3"}
    ]

    wf1 = db.query(Workflow).filter(Workflow.name == "Research Workflow").first()
    if not wf1:
        wf1 = Workflow(name="Research Workflow", description="Research -> Summarizer -> Reviewer", nodes=wf1_nodes, edges=wf1_edges)
        db.add(wf1)

    # Workflow 2: Customer Support Workflow
    wf2_nodes = [
        {"id": "trigger", "type": "trigger", "position": {"x": 100, "y": 100}},
        {"id": "agent_4", "type": "agent", "position": {"x": 300, "y": 100}, "data": {"agent_id": agent_map.get("Intake Agent")}},
        {"id": "agent_5", "type": "agent", "position": {"x": 500, "y": 100}, "data": {"agent_id": agent_map.get("Knowledge Agent")}},
        {"id": "agent_6", "type": "agent", "position": {"x": 700, "y": 100}, "data": {"agent_id": agent_map.get("Escalation Agent")}}
    ]
    wf2_edges = [
        {"id": "e1", "source": "trigger", "target": "agent_4"},
        {"id": "e2", "source": "agent_4", "target": "agent_5"},
        {"id": "e3", "source": "agent_5", "target": "agent_6"}
    ]

    wf2 = db.query(Workflow).filter(Workflow.name == "Customer Support Workflow").first()
    if not wf2:
        wf2 = Workflow(name="Customer Support Workflow", description="Intake -> Knowledge -> Escalation", nodes=wf2_nodes, edges=wf2_edges)
        db.add(wf2)

    db.commit()
    db.close()
    print("Database seeded with default agents and workflows.")

if __name__ == "__main__":
    seed()
