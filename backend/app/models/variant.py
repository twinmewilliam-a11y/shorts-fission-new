# backend/app/models/variant.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class VariantStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Variant(Base):
    __tablename__ = "variants"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    
    # Variant info
    variant_index = Column(Integer, nullable=False)  # 1-20
    status = Column(Enum(VariantStatus), default=VariantStatus.PENDING)
    
    # Content
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array
    
    # Effects applied
    effects_applied = Column(Text, nullable=True)  # JSON array
    
    # File info
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Relationship
    # video = relationship("Video", back_populates="variants")
    
    def __repr__(self):
        return f"<Variant(id={self.id}, video_id={self.video_id}, index={self.variant_index}, status={self.status})>"
