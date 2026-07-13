"""Agent REST API endpoints."""
import uuid as uuidlib
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.agent import Agent, Conversation, Message
from app.agents.runtime import AgentRuntime
from app.memory.manager import MemoryManager

router = APIRouter()


# ---------------------------------------------------------------------------
# Agent CRUD
# ---------------------------------------------------------------------------
class AgentCreate(BaseModel):
    project_id: str
    name: str
    system_prompt: str = "You are a helpful AI assistant."
    model: str = "gpt-4o"


@router.post("/")
def create_agent(req: AgentCreate, db: Session = Depends(get_db)):
    agent = Agent(
        project_id=uuidlib.UUID(req.project_id),
        name=req.name,
        system_prompt=req.system_prompt,
        model=req.model,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    return {
        "id": str(agent.id),
        "name": agent.name,
        "model": agent.model,
    }


@router.get("/")
def list_agents(project_id: str, db: Session = Depends(get_db)):
    agents = db.query(Agent).filter(Agent.project_id == project_id).all()

    return [
        {
            "id": str(a.id),
            "name": a.name,
            "model": a.model,
        }
        for a in agents
    ]


@router.get("/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "id": str(agent.id),
        "name": agent.name,
        "model": agent.model,
        "system_prompt": agent.system_prompt,
    }


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[str] = None
    use_memory: bool = True


@router.post("/{agent_id}/chat")
async def chat_with_agent(
    agent_id: str,
    req: ChatRequest,
    db: Session = Depends(get_db),
):
    # Find agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Memory manager
    memory = None
    if req.use_memory:
        memory = MemoryManager(
            agent_id=agent_id,
            user_id=req.user_id,
            db=db,
        )

    # Runtime
    runtime = AgentRuntime(
        agent_id=agent_id,
        user_id=req.user_id,
        model=agent.model,
        system_prompt=agent.system_prompt,
        memory_manager=memory,
    )

    # Run agent
    result = await runtime.run(req.message)

    # Conversation ID
    if req.conversation_id:
        try:
            conv_uuid = uuidlib.UUID(req.conversation_id)
        except ValueError:
            conv_uuid = uuidlib.uuid4()
    else:
        conv_uuid = uuidlib.uuid4()

    # Create conversation if it doesn't exist
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conv_uuid)
        .first()
    )

    if conversation is None:
        conversation = Conversation(
            id=conv_uuid,
            agent_id=agent.id,
            user_id=uuidlib.UUID(req.user_id),
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=req.message,
    )

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["response"],
    )

    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()

    return {
        "conversation_id": str(conversation.id),
        "response": result["response"],
        "iterations": result["iterations"],
        "messages": result["messages"],
    }