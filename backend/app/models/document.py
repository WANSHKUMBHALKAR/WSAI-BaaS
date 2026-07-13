"""Document model for RAG ingestion pipeline."""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)          # pdf | docx | txt | url
    file_path = Column(String)                          # local storage path
    file_size_bytes = Column(BigInteger, default=0)
    status = Column(String, default="pending")          # pending|processing|completed|failed
    error_message = Column(Text)
    chunk_count = Column(String, default="0")
    collection_name = Column(String)                    # Qdrant collection
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project")
