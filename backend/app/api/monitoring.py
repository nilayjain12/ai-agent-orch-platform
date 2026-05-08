from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Execution, LogEntry
from typing import List

router = APIRouter(prefix="/executions", tags=["Monitoring"])

@router.get("/{execution_id}")
def get_execution_status(execution_id: int, db: Session = Depends(get_db)):
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    logs = db.query(LogEntry).filter(LogEntry.execution_id == execution_id).order_by(LogEntry.timestamp.asc()).all()
    
    return {
        "id": execution.id,
        "workflow_id": execution.workflow_id,
        "status": execution.status,
        "result": execution.result,
        "logs": [
            {
                "id": l.id,
                "message": l.message,
                "timestamp": l.timestamp.isoformat()
            } for l in logs
        ]
    }

@router.get("/")
def get_recent_executions(db: Session = Depends(get_db)):
    executions = db.query(Execution).order_by(Execution.id.desc()).limit(10).all()
    return [{"id": e.id, "workflow_id": e.workflow_id, "status": e.status} for e in executions]

@router.delete("/")
def delete_all_executions(db: Session = Depends(get_db)):
    db.query(Execution).delete()
    db.commit()
    return {"message": "All executions cleared"}

