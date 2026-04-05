# backend/app/tasks/celery_tasks.py
"""
兼容入口 - 所有任务已拆分到独立模块
新代码请直接 import 子模块:
  from app.tasks.variant_tasks import generate_variants_task
  from app.tasks.download_tasks import download_video_task
"""
from app.tasks.celery_app import celery_app  # noqa: F401
from app.tasks.variant_tasks import generate_variants_task, _generate_single_variant  # noqa: F401
from app.tasks.download_tasks import download_video_task, batch_download_task  # noqa: F401
from app.tasks.subtitle_utils import (  # noqa: F401
    _render_remotion_subtitle_v2,
    _prepare_subtitle,
    _burn_subtitle,
    _get_video_resolution,
)
from app.tasks.progress import update_stage_progress, update_progress  # noqa: F401
