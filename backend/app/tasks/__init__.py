"""
Celery 任务模块包

此包包含 Shorts-Fission 项目的所有 Celery 异步任务：
- celery_app: Celery 应用配置与全局服务
- variant_tasks: 视频变体生成任务
- download_tasks: 视频下载任务
- subtitle_utils: 字幕处理工具函数
- progress: 进度管理工具函数

兼容性：
- 支持 `celery -A app.tasks worker` 启动 worker
- 支持 `celery -A app.tasks.celery_tasks worker` 向后兼容

注意：此模块导出所有公共接口，保持向后兼容
"""

# 从 celery_app.py 导出 Celery 应用和全局变量
from .celery_app import (
    celery_app,
    downloader,
    yt_dlp_api,
    scrapling_downloader,
    variant_engine,
    audio_engine,
    _progress_lock,
    _completed_count,
    warmup_models
)

# 从 variant_tasks.py 导出任务函数
from .variant_tasks import (
    generate_variants_task,
    _generate_single_variant
)

# 从 download_tasks.py 导出任务函数
from .download_tasks import (
    download_video_task,
    batch_download_task
)

# 从 subtitle_utils.py 导出字幕工具函数
from .subtitle_utils import (
    _render_remotion_subtitle_v2,
    _prepare_subtitle,
    _burn_subtitle,
    _get_video_resolution
)

# 从 progress.py 导出进度管理函数
from .progress import (
    update_stage_progress,
    update_progress
)


# ==================== 向后兼容性处理 ====================

# 为了保持向后兼容性，创建 celery_tasks 模块的别名
# 这使得 `from app.tasks.celery_tasks import ...` 仍然可以工作

class _CeleryTasksCompat:
    """向后兼容性包装器"""
    
    def __init__(self):
        # 所有任务函数和变量
        self.celery_app = celery_app
        self.downloader = downloader
        self.yt_dlp_api = yt_dlp_api
        self.scrapling_downloader = scrapling_downloader
        self.variant_engine = variant_engine
        self.audio_engine = audio_engine
        self._progress_lock = _progress_lock
        self._completed_count = _completed_count
        self.warmup_models = warmup_models
        
        # 任务函数
        self.generate_variants_task = generate_variants_task
        self._generate_single_variant = _generate_single_variant
        self.download_video_task = download_video_task
        self.batch_download_task = batch_download_task
        
        # 字幕工具函数
        self._render_remotion_subtitle_v2 = _render_remotion_subtitle_v2
        self._prepare_subtitle = _prepare_subtitle
        self._burn_subtitle = _burn_subtitle
        self._get_video_resolution = _get_video_resolution
        
        # 进度管理函数
        self.update_stage_progress = update_stage_progress
        self.update_progress = update_progress


# 创建兼容性实例
_celery_compat = _CeleryTasksCompat()

# 添加到模块的 __all__ 中，以便向后兼容
_compat_exports = [
    'celery_app', 'downloader', 'yt_dlp_api', 'scrapling_downloader',
    'variant_engine', 'audio_engine', '_progress_lock', '_completed_count', 'warmup_models',
    'generate_variants_task', '_generate_single_variant', 'download_video_task', 'batch_download_task',
    '_render_remotion_subtitle_v2', '_prepare_subtitle', '_burn_subtitle', '_get_video_resolution',
    'update_stage_progress', 'update_progress'
]

# 将兼容性实例的属性添加到当前模块的命名空间
for attr_name in _compat_exports:
    locals()[attr_name] = getattr(_celery_compat, attr_name)


# ==================== 导出列表 ====================

__all__ = [
    # 核心应用和配置
    'celery_app',
    
    # 全局服务实例
    'downloader',
    'yt_dlp_api', 
    'scrapling_downloader',
    'variant_engine',
    'audio_engine',
    '_progress_lock',
    '_completed_count',
    'warmup_models',
    
    # 任务函数
    'generate_variants_task',
    '_generate_single_variant',
    'download_video_task',
    'batch_download_task',
    
    # 字幕工具函数
    '_render_remotion_subtitle_v2',
    '_prepare_subtitle',
    '_burn_subtitle',
    '_get_video_resolution',
    
    # 进度管理函数
    'update_stage_progress',
    'update_progress'
]


# ==================== 模块信息 ====================

__version__ = "1.0.0"
__description__ = "Shorts-Fission Celery 任务模块 - 支持视频下载和变体生成"