# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Shorts Fission"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database - 使用绝对路径避免路径问题
    DATABASE_URL: str = "sqlite+aiosqlite:////root/.openclaw/workspace/projects/shorts-fission/data/shorts_fission.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Paths - 使用绝对路径
    DATA_DIR: str = "/root/.openclaw/workspace/projects/shorts-fission/data"
    VIDEOS_DIR: str = "/root/.openclaw/workspace/projects/shorts-fission/data/videos"
    VARIANTS_DIR: str = "/root/.openclaw/workspace/projects/shorts-fission/data/variants"
    SUBTITLES_DIR: str = "/root/.openclaw/workspace/projects/shorts-fission/data/subtitles"
    LUTS_DIR: str = "/root/.openclaw/workspace/projects/shorts-fission/luts"
    MASKS_DIR: str = "/root/.openclaw/workspace/projects/shorts-fission/masks"
    BGM_DIR: str = "/root/.openclaw/workspace/projects/shorts-fission/sports_bgm"
    
    # Variant Settings
    DEFAULT_VARIANT_COUNT: int = 15
    MIN_VARIANT_COUNT: int = 10
    MAX_VARIANT_COUNT: int = 20
    MIN_EFFECTS: int = 1
    MAX_EFFECTS: int = 5
    
    # Download Settings
    MAX_CONCURRENT_DOWNLOADS: int = 3
    MONITOR_CHECK_INTERVAL: int = 300  # 5 minutes
    
    # Proxy (for TikTok/YouTube)
    PROXY_ENABLED: bool = False
    PROXY_URL: str = "socks5://154.21.232.209:45001"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
