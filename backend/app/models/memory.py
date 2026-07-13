"""Memory model — stores long-term facts and episodic memories for agents."""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.session import Base


class Memory(Base):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    memory_type = Column(String, default="episodic")  # episodic | semantic | procedural
    content = Column(Text, nullable=False)
    importance = Column(Float, default=0.5)            # 0.0 – 1.0 for recency/salience scoring
    qdrant_id = Column(String)                         # reference into the memory vector collection
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True))
