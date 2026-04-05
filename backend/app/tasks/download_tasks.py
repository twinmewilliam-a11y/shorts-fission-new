"""
视频下载任务模块

包含：
- download_video_task：单个视频下载任务
- batch_download_task：批量下载任务
- 下载逻辑与进度管理

从此模块导入：
    - download_video_task
    - batch_download_task
"""
import asyncio
import os
from pathlib import Path
from loguru import logger

from app.tasks.celery_app import celery_app, scrapling_downloader, yt_dlp_api
from app.config import settings
from app.database import async_session
from app.models.video import Video
from sqlalchemy import select


def _get_video_resolution(filepath: str) -> str:
    """获取视频分辨率"""
    if not filepath or not os.path.exists(filepath):
        return 'unknown'
    try:
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height', '-of', 'csv=p=0', filepath],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            w, h = result.stdout.strip().split(',')
            h = int(h)
            if h >= 1080:
                return '1080p'
            elif h >= 720:
                return '720p'
            elif h >= 480:
                return '480p'
            elif h >= 360:
                return '360p'
            return f'{h}p'
    except Exception as e:
        logger.error(f"获取分辨率失败: {e}")
    return 'unknown'


@celery_app.task(bind=True)
def download_video_task(self, video_id: int, url: str, output_dir: str):
    """下载视频任务 - 优先使用 Scrapling，回退到 yt-dlp-api"""
    logger.info(f"开始下载视频: {url}")
    
    # 更新状态
    self.update_state(
        state='PROGRESS',
        meta={'status': 'downloading', 'progress': 0}
    )
    
    result = None
    
    # 方案1: 使用 Scrapling（推荐，绕过 Cloudflare）
    if scrapling_downloader and scrapling_downloader.is_available():
        logger.info("使用 Scrapling 下载...")
        result = scrapling_downloader.download(
            url=url,
            output_dir=output_dir,
            no_watermark=True
        )
        if result.get('success'):
            result['resolution'] = _get_video_resolution(result.get('filepath'))
        else:
            logger.warning(f"Scrapling 下载失败: {result.get('error')}，尝试 yt-dlp-api...")
            result = None
    
    # 方案2: 回退到 yt-dlp-api
    if not result or not result.get('success'):
        logger.info("使用 yt-dlp-api 下载...")
        result = yt_dlp_api.download_video_sync(url, output_dir, "720p")
    
    # 更新数据库状态
    async def update_status():
        async with async_session() as session:
            stmt = select(Video).where(Video.id == video_id)
            result_db = await session.execute(stmt)
            video = result_db.scalar_one_or_none()
            
            if video:
                if result['success']:
                    video.status = 'downloaded'
                    video.video_id = result.get('video_id')
                    video.title = result.get('title')
                    video.duration = result.get('duration', 0)
                    video.thumbnail = result.get('thumbnail')
                    video.source_path = result.get('file_path')
                    video.resolution = result.get('resolution')
                    video.download_progress = 100
                    from datetime import datetime
                    video.downloaded_at = datetime.now()
                    logger.info(f"视频 {video_id} 下载完成，分辨率: {result.get('resolution')}")
                else:
                    video.status = 'failed'
                    video.error_message = result.get('error')
                    logger.error(f"视频 {video_id} 下载失败: {result.get('error')}")
                
                await session.commit()
    
    # 运行异步更新
    try:
        asyncio.run(update_status())
    except Exception as e:
        logger.error(f"更新数据库状态失败: {e}")
    
    if result['success']:
        return {
            'status': 'completed',
            'video_id': video_id,
            'file_path': result.get('file_path'),
            'title': result.get('title'),
            'duration': result.get('duration'),
            'resolution': result.get('resolution'),
        }
    else:
        raise Exception(result.get('error'))


@celery_app.task(bind=True)
def batch_download_task(self, account_url: str, output_dir: str, start_date: str = None, end_date: str = None):
    """批量下载任务"""
    logger.info(f"开始批量下载: {account_url}")
    
    # 使用全局的下载器实例
    from app.tasks.celery_app import downloader
    
    result = downloader.batch_download(
        account_url,
        output_dir,
        start_date,
        end_date,
        max_count=50
    )
    
    return result


# ==================== 导出 ====================

__all__ = [
    'download_video_task',
    'batch_download_task'
]