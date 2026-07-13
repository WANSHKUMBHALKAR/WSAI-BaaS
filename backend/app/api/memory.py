import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.memory import Memory
from app.memory.manager import MemoryManager

router = APIRouter()

class MemoryCreate(BaseModel):
    agent_id: str
    user_id: str
    content: str
    memory_type: str = "episodic"
    importance: float = 0.5

class MemoryQuery(BaseModel):
    agent_id: str
    user_id: str
    query: str
    top_k: int = 5

@router.post("/")
async def add_memory(req: MemoryCreate, db: Session = Depends(get_db)):
    try:
        manager = MemoryManager(agent_id=req.agent_id, user_id=req.user_id, db=db)
        mem = await manager.add_long_term(
            content=req.content,
            memory_type=req.memory_type,
            importance=req.importance
        )
        return {
            "id": str(mem.id),
            "agent_id": str(mem.agent_id),
            "user_id": str(mem.user_id),
            "content": mem.content,
            "memory_type": mem.memory_type,
            "created_at": mem.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/search")
async def search_memory(req: MemoryQuery, db: Session = Depends(get_db)):
    try:
        manager = MemoryManager(agent_id=req.agent_id, user_id=req.user_id, db=db)
        results = await manager.search_long_term(query=req.query, top_k=req.top_k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{memory_id}")
def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    mem = db.query(Memory).filter(Memory.id == uuid.UUID(memory_id)).first()
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    db.delete(mem)
    db.commit()
    return {"status": "deleted"}
