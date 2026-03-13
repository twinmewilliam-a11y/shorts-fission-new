# backend/app/models/video.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base
import enum

class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source info
    platform = Column(String(50), nullable=False)  # youtube / tiktok
    video_id = Column(String(100), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    account_id = Column(String(100), nullable=True)
    
    # Video info
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    duration = Column(Integer, default=0)
    thumbnail = Column(String(500), nullable=True)
    upload_date = Column(DateTime, nullable=True)
    
    # Status tracking
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING)
    variant_count = Column(Integer, default=0)
    target_variant_count = Column(Integer, default=15)
    
    # Progress
    download_progress = Column(Integer, default=0)
    variant_progress = Column(Integer, default=0)
    
    # File paths
    source_path = Column(String(500), nullable=True)
    subtitle_path = Column(String(500), nullable=True)  # 字幕文件路径
    
    # Video quality
    resolution = Column(String(20), nullable=True)  # e.g., "720p", "1080p", "360p"
    has_subtitle = Column(Boolean, default=False)  # 是否有字幕
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    downloaded_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Video(id={self.id}, platform={self.platform}, video_id={self.video_id}, status={self.status})>"
