import uuid
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.workspace import APIKey, Project

router = APIRouter()

class APIKeyCreate(BaseModel):
    project_id: str
    name: str
    expires_in_days: Optional[int] = 30

@router.post("/")
def generate_api_key(req: APIKeyCreate, db: Session = Depends(get_db)):
    project_uuid = uuid.UUID(req.project_id)
    project = db.query(Project).filter(Project.id == project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate raw token
    raw_token = f"wsai_{secrets.token_urlsafe(32)}"
    
    # Hash raw token using SHA-256
    hash_object = hashlib.sha256(raw_token.encode())
    key_hash = hash_object.hexdigest()

    # Calculate expiration date
    expires_at = None
    if req.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)

    api_key = APIKey(
        key_hash=key_hash,
        name=req.name,
        project_id=project_uuid,
        expires_at=expires_at
    )
    db.add(api_key)
    db.commit()

    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "raw_key": raw_token,  # returned ONLY once
        "expires_at": api_key.expires_at,
        "created_at": api_key.created_at
    }

@router.get("/")
def list_api_keys(project_id: str, db: Session = Depends(get_db)):
    keys = db.query(APIKey).filter(APIKey.project_id == uuid.UUID(project_id)).all()
    return [{
        "id": str(k.id),
        "name": k.name,
        "expires_at": k.expires_at,
        "created_at": k.created_at
    } for k in keys]

@router.delete("/{key_id}")
def revoke_api_key(key_id: str, db: Session = Depends(get_db)):
    api_key = db.query(APIKey).filter(APIKey.id == uuid.UUID(key_id)).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    db.delete(api_key)
    db.commit()
    return {"status": "revoked"}
