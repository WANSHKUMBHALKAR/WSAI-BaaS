"""
Ingestion service — orchestrates parse → chunk → embed → store for uploaded documents.
Designed to be called from both sync API endpoints and Celery background tasks.
"""
from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models.document import Document
from app.rag.parsers import parse_document
from app.rag.chunking import chunk_recursive
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/wsai_uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class DocumentIngestionService:
    """Handles the full lifecycle of a document from upload to vector storage."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    async def ingest(
        self,
        project_id: str,
        filename: str,
        file_bytes: Optional[bytes] = None,
        url: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> Document:
        """
        Full ingestion pipeline.
        Returns the updated Document record after processing.
        """
        doc = self._create_record(project_id, filename, file_bytes, url)

        try:
            self._set_status(doc, "processing")

            # 1. Parse
            text = await parse_document(file_bytes=file_bytes, filename=filename, url=url)

            # 2. Chunk
            chunks = chunk_recursive(
                text,
                chunk_size=chunk_size,
                overlap=chunk_overlap,
                metadata={"document_id": str(doc.id), "filename": filename},
            )

            # 3. Embed + store in Qdrant
            store = VectorStore(project_id=project_id)
            await store.upsert_chunks(
                texts=[c.text for c in chunks],
                document_id=str(doc.id),
                extra_payload={"filename": filename},
            )

            doc.chunk_count = str(len(chunks))
            doc.collection_name = store.collection_name
            self._set_status(doc, "completed")
        except Exception as exc:
            logger.error("Ingestion failed for document %s: %s", doc.id, exc, exc_info=True)
            doc.error_message = str(exc)
            self._set_status(doc, "failed")

        return doc

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _create_record(
        self,
        project_id: str,
        filename: str,
        file_bytes: Optional[bytes],
        url: Optional[str],
    ) -> Document:
        file_type = "url" if url else Path(filename).suffix.lstrip(".")
        doc = Document(
            id=uuid.uuid4(),
            project_id=project_id,
            filename=filename,
            file_type=file_type,
            file_size_bytes=len(file_bytes) if file_bytes else 0,
            status="pending",
        )
        self._db.add(doc)
        self._db.commit()
        self._db.refresh(doc)

        if file_bytes:
            save_path = UPLOAD_DIR / str(doc.id) / filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(file_bytes)
            doc.file_path = str(save_path)
            self._db.commit()

        return doc

    def _set_status(self, doc: Document, status: str) -> None:
        doc.status = status
        self._db.add(doc)
        self._db.commit()
