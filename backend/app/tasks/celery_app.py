"""
Celery 应用配置与全局服务初始化

此模块包含：
- Celery 应用创建与配置
- 全局服务实例初始化（下载器、引擎等）
- 模型预热逻辑
- 工作进程初始化信号处理

注意：所有全局变量都在此模块中初始化，其他模块通过导入使用
"""
import threading
import loguru
from celery import Celery, signals

from app.config import settings
from app.services.downloader import VideoDownloader, YtDlpApiClient
from app.services.scrapling_downloader import ScraplingDownloader, SCRAPLING_AVAILABLE
from app.services.variant_engine import VariantEngine, AudioVariantEngine

# 初始化日志
logger = loguru.logger


# ==================== Celery 应用创建 ====================

# 创建 Celery 应用实例
celery_app = Celery(
    'shorts_fission',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery 配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
)


# ==================== 模型预热 ====================

@signals.worker_process_init.connect
def warmup_models(**kwargs):
    """
    Worker 进程初始化时预热模型
    
    解决 WhisperX 模型每次请求都重新加载的问题
    预热后，首次处理视频时不需要等待模型加载
    """
    logger.info("[Worker] 开始预热模型...")
    
    try:
        from app.services.model_warmup import warmup_whisperx
        
        # 预热 WhisperX 模型
        success = warmup_whisperx(model_size="base")
        
        if success:
            logger.info("[Worker] 模型预热完成 ✅")
        else:
            logger.warning("[Worker] 模型预热失败，将在首次使用时加载")
    
    except Exception as e:
        logger.warning(f"[Worker] 模型预热异常: {e}")


# ==================== 全局服务初始化 ====================

# 初始化下载服务
downloader = VideoDownloader({
    'proxy_url': settings.PROXY_URL,
    'proxy_enabled': settings.PROXY_ENABLED,
    'videos_dir': settings.VIDEOS_DIR,
    'use_yt_dlp_api': True,  # 使用 yt-dlp-api
})

# yt-dlp-api 客户端
yt_dlp_api = YtDlpApiClient()

# Scrapling 下载器（推荐）
scrapling_downloader = None
if SCRAPLING_AVAILABLE:
    scrapling_downloader = ScraplingDownloader({
        'headless': True,
        'use_stealth': True,
        'yt_dlp_path': 'yt-dlp',
        'cookies_file': '/root/.openclaw/workspace/projects/shorts-fission/backend/cookies.txt',
    })
    logger.info("Scrapling 下载器已启用")
else:
    logger.warning("Scrapling 不可用，使用传统下载方式")

# v4.0 PIP 变体引擎
variant_engine = VariantEngine({
    'min_enhanced': 3,
    'max_enhanced': 5,
    'whisperx_enabled': False,  # 暂时禁用字幕提取，后续启用
})

# 音频变体引擎
audio_engine = AudioVariantEngine({
    'bgm_dir': settings.BGM_DIR,
    'bgm_volume': 0.3,
})

# 进度追踪锁（线程安全）
_progress_lock = threading.Lock()
_completed_count = 0


# ==================== 导出 ====================

__all__ = [
    'celery_app',
    'downloader',
    'yt_dlp_api', 
    'scrapling_downloader',
    'variant_engine',
    'audio_engine',
    '_progress_lock',
    '_completed_count',
    'warmup_models'
]