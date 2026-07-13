"""RAG REST API — document upload, status, and query endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.document import Document
from app.rag.ingestion import DocumentIngestionService
from app.rag.pipeline import RAGPipeline

router = APIRouter()


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
@router.post("/upload")
async def upload_document(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    svc = DocumentIngestionService(db=db)
    doc = await svc.ingest(
        project_id=project_id,
        filename=file.filename,
        file_bytes=file_bytes,
    )
    return {"document_id": str(doc.id), "status": doc.status, "chunks": doc.chunk_count}


@router.post("/ingest-url")
async def ingest_url(project_id: str, url: str, db: Session = Depends(get_db)):
    svc = DocumentIngestionService(db=db)
    doc = await svc.ingest(project_id=project_id, filename=url, url=url)
    return {"document_id": str(doc.id), "status": doc.status}


# ---------------------------------------------------------------------------
# Document Status
# ---------------------------------------------------------------------------
@router.get("/documents/{document_id}")
def get_document_status(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "error": doc.error_message,
        "created_at": doc.created_at,
    }


@router.get("/documents")
def list_documents(project_id: str, db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.project_id == project_id).all()
    return [
        {"id": str(d.id), "filename": d.filename, "status": d.status, "chunks": d.chunk_count}
        for d in docs
    ]


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    project_id: str
    question: str
    document_id: Optional[str] = None
    model: str = "gpt-4o"
    top_k: int = 5


@router.post("/query")
async def rag_query(req: QueryRequest):
    pipeline = RAGPipeline(
        project_id=req.project_id,
        model=req.model,
        top_k=req.top_k,
    )
    result = await pipeline.query(
        question=req.question,
        document_id=req.document_id,
    )
    return result
