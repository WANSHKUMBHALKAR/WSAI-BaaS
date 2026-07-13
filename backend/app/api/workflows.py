import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.workflow import Workflow, WorkflowRun
from app.services.workflow_engine import WorkflowEngine

router = APIRouter()

class WorkflowCreate(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None
    definition: Dict[str, Any]  # nodes, edges

class WorkflowRunRequest(BaseModel):
    input_data: Dict[str, Any]

@router.post("/")
def create_workflow(req: WorkflowCreate, db: Session = Depends(get_db)):
    workflow = Workflow(
        project_id=uuid.UUID(req.project_id),
        name=req.name,
        description=req.description,
        definition=req.definition
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return {
        "id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "is_active": workflow.is_active
    }

@router.get("/")
def list_workflows(project_id: str, db: Session = Depends(get_db)):
    workflows = db.query(Workflow).filter(Workflow.project_id == uuid.UUID(project_id)).all()
    return [{
        "id": str(w.id),
        "name": w.name,
        "description": w.description,
        "is_active": w.is_active,
        "created_at": w.created_at
    } for w in workflows]

@router.get("/{workflow_id}")
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "definition": workflow.definition,
        "is_active": workflow.is_active,
        "created_at": workflow.created_at
    }

@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: str, 
    req: WorkflowRunRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    workflow_uuid = uuid.UUID(workflow_id)
    engine = WorkflowEngine(db=db)
    
    # We can run synchronously or background it. Let's do it sync for immediate feedback, or run it in background
    # Let's run it directly here to return output for fast workflows, but handle timeout gracefully.
    try:
        run = await engine.execute_run(workflow_uuid, req.input_data)
        return {
            "run_id": str(run.id),
            "status": run.status,
            "output": run.output_data,
            "error": run.error,
            "started_at": run.started_at,
            "completed_at": run.completed_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{workflow_id}/runs")
def list_workflow_runs(workflow_id: str, db: Session = Depends(get_db)):
    runs = db.query(WorkflowRun).filter(WorkflowRun.workflow_id == uuid.UUID(workflow_id)).all()
    return [{
        "id": str(r.id),
        "status": r.status,
        "started_at": r.started_at,
        "completed_at": r.completed_at
    } for r in runs]
