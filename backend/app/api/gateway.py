"""AI Gateway REST endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.ai_gateway.gateway import AIGateway
from app.services.ai_gateway.base import ChatMessage

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[dict]
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    project_id: Optional[str] = None


@router.post("/chat")
async def gateway_chat(req: ChatRequest, db: Session = Depends(get_db)):
    messages = [ChatMessage(**m) for m in req.messages]
    gw = AIGateway(db=db)

    if req.stream:
        async def _stream():
            async for chunk in gw.stream_chat(
                messages, model=req.model, temperature=req.temperature, max_tokens=req.max_tokens
            ):
                yield chunk

        return StreamingResponse(_stream(), media_type="text/plain")

    try:
        response = await gw.chat(
            messages, model=req.model, temperature=req.temperature, max_tokens=req.max_tokens
        )
        return response.__dict__
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    gw = AIGateway(db=db)
    return gw.list_all_models()
