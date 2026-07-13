import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.workspace import Organization, Project
from app.models.team import Team, OrganizationMember
from app.models.user import User

router = APIRouter()

class OrgCreate(BaseModel):
    name: str
    owner_id: str

class TeamCreate(BaseModel):
    name: str
    org_id: str

@router.post("/")
def create_organization(req: OrgCreate, db: Session = Depends(get_db)):
    owner_uuid = uuid.UUID(req.owner_id)
    org = Organization(
        name=req.name,
        owner_id=owner_uuid
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # Add owner as a member
    member = OrganizationMember(
        org_id=org.id,
        user_id=owner_uuid,
        role="owner"
    )
    db.add(member)
    db.commit()

    return {
        "id": str(org.id),
        "name": org.name,
        "owner_id": str(org.owner_id),
        "created_at": org.created_at
    }

@router.get("/")
def list_organizations(user_id: str, db: Session = Depends(get_db)):
    user_uuid = uuid.UUID(user_id)
    # Get all organizations where the user is a member
    memberships = db.query(OrganizationMember).filter(OrganizationMember.user_id == user_uuid).all()
    org_ids = [m.org_id for m in memberships]
    orgs = db.query(Organization).filter(Organization.id.in_(org_ids)).all()
    
    return [{
        "id": str(o.id),
        "name": o.name,
        "owner_id": str(o.owner_id),
        "created_at": o.created_at
    } for o in orgs]

@router.post("/teams")
def create_team(req: TeamCreate, db: Session = Depends(get_db)):
    team = Team(
        name=req.name,
        org_id=uuid.UUID(req.org_id)
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return {
        "id": str(team.id),
        "name": team.name,
        "org_id": str(team.org_id)
    }

@router.get("/{org_id}/teams")
def list_teams(org_id: str, db: Session = Depends(get_db)):
    teams = db.query(Team).filter(Team.org_id == uuid.UUID(org_id)).all()
    return [{"id": str(t.id), "name": t.name} for t in teams]
