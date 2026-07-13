import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.workspace import Project, Organization

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    org_id: str

@router.post("/")
def create_project(req: ProjectCreate, db: Session = Depends(get_db)):
    org_uuid = uuid.UUID(req.org_id)
    org = db.query(Organization).filter(Organization.id == org_uuid).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    project = Project(
        name=req.name,
        org_id=org_uuid
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {
        "id": str(project.id),
        "name": project.name,
        "org_id": str(project.org_id),
        "created_at": project.created_at
    }

@router.get("/")
def list_projects(org_id: str, db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.org_id == uuid.UUID(org_id)).all()
    return [{
        "id": str(p.id),
        "name": p.name,
        "org_id": str(p.org_id),
        "created_at": p.created_at
    } for p in projects]

@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {"status": "deleted"}
