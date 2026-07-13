import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.usage import UsageLog

router = APIRouter()

@router.get("/")
def get_analytics(project_id: str, db: Session = Depends(get_db)):
    project_uuid = uuid.UUID(project_id)
    
    # 1. Total Requests
    total_requests = db.query(UsageLog).filter(UsageLog.project_id == project_uuid).count()

    # 2. Total Tokens & Avg Latency
    totals = db.query(
        func.sum(UsageLog.prompt_tokens).label("prompt_tokens"),
        func.sum(UsageLog.completion_tokens).label("completion_tokens"),
        func.sum(UsageLog.total_tokens).label("total_tokens"),
        func.avg(UsageLog.latency_ms).label("avg_latency")
    ).filter(UsageLog.project_id == project_uuid).first()

    # 3. Breakdown by Provider
    provider_breakdown = db.query(
        UsageLog.provider,
        UsageLog.model,
        func.sum(UsageLog.total_tokens).label("tokens"),
        func.count(UsageLog.id).label("requests")
    ).filter(UsageLog.project_id == project_uuid).group_by(UsageLog.provider, UsageLog.model).all()

    # 4. Recent Logs
    recent_logs = db.query(UsageLog).filter(
        UsageLog.project_id == project_uuid
    ).order_by(UsageLog.created_at.desc()).limit(20).all()

    return {
        "summary": {
            "total_requests": total_requests,
            "prompt_tokens": int(totals.prompt_tokens or 0),
            "completion_tokens": int(totals.completion_tokens or 0),
            "total_tokens": int(totals.total_tokens or 0),
            "avg_latency_ms": round(float(totals.avg_latency or 0.0), 2)
        },
        "breakdown": [{
            "provider": pb.provider,
            "model": pb.model,
            "tokens": int(pb.tokens or 0),
            "requests": pb.requests
        } for pb in provider_breakdown],
        "recent_logs": [{
            "id": str(log.id),
            "provider": log.provider,
            "model": log.model,
            "total_tokens": log.total_tokens,
            "latency_ms": log.latency_ms,
            "created_at": log.created_at
        } for log in recent_logs]
    }
