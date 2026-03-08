# backend/app/tasks/celery_tasks.py
"""
Celery 异步任务 - 下载视频和生成变体
支持通过 yt-dlp-api 代理服务下载（更稳定）
"""
import os
from pathlib import Path
from celery import Celery
from loguru import logger
import asyncio

from app.config import settings
from app.services.downloader import VideoDownloader, YtDlpApiClient
from app.services.variant_engine import VisualVariantEngine, AudioVariantEngine

# 创建 Celery 应用
celery_app = Celery(
    'shorts_fission',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
)

# 初始化服务
downloader = VideoDownloader({
    'proxy_url': settings.PROXY_URL,
    'proxy_enabled': settings.PROXY_ENABLED,
    'videos_dir': settings.VIDEOS_DIR,
    'use_yt_dlp_api': True,  # 使用 yt-dlp-api
})

# yt-dlp-api 客户端
yt_dlp_api = YtDlpApiClient()

variant_engine = VisualVariantEngine({
    'luts_dir': settings.LUTS_DIR,
    'masks_dir': settings.MASKS_DIR,
    'min_effects': settings.MIN_EFFECTS,
    'max_effects': settings.MAX_EFFECTS,
})

audio_engine = AudioVariantEngine({
    'bgm_dir': settings.BGM_DIR,
    'bgm_volume': 0.3,
})


@celery_app.task(bind=True)
def download_video_task(self, video_id: int, url: str, output_dir: str):
    """下载视频任务 - 使用 yt-dlp-api（同步方式）"""
    import asyncio
    from app.database import async_session
    from app.models.video import Video
    from sqlalchemy import select
    
    logger.info(f"开始下载视频: {url}")
    
    # 更新状态
    self.update_state(
        state='PROGRESS',
        meta={'status': 'downloading', 'progress': 0}
    )
    
    # 使用同步方法下载
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
def generate_variants_task(self, video_id: int, source_path: str, count: int = 15, start_index: int = 1):
    """生成视频变体任务
    
    Args:
        video_id: 视频ID
        source_path: 源视频路径
        count: 要生成的变体数量
        start_index: 起始变体索引（用于累加模式）
    """
    logger.info(f"开始生成变体: {video_id}, 数量: {count}")
    
    # 创建输出目录
    output_dir = Path(settings.VARIANTS_DIR) / str(video_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for i in range(1, count + 1):
        # 更新进度
        progress = int((i / count) * 100)
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'processing',
                'current': i,
                'total': count,
                'progress': progress,
            }
        )
        
        actual_index = start_index + i - 1  # 计算实际索引
        output_path = str(output_dir / f"variant_{actual_index:03d}.mp4")
        
        # 生成视觉变体
        visual_result = variant_engine.generate_variant(
            source_path,
            output_path,
            seed=video_id * 1000 + actual_index  # 使用实际索引作为种子
        )
        
        if visual_result['success']:
            # 生成音频变体 (BGM 替换)
            final_path = str(output_dir / f"final_{actual_index:03d}.mp4")
            audio_result = audio_engine.replace_bgm(
                output_path,
                final_path,
                sport_type='default'  # TODO: 根据视频内容识别球类
            )
            
            # 构建易读的效果描述
            effects_desc = []
            base_effects = visual_result.get('base_effects', {})
            if base_effects.get('flip'):
                effects_desc.append('镜像翻转')
            if base_effects.get('rotation'):
                effects_desc.append(f"旋转{base_effects['rotation']:.1f}°")
            if base_effects.get('scale'):
                effects_desc.append(f"缩放{base_effects['scale']:.2f}x")
            if base_effects.get('speed'):
                effects_desc.append(f"变速{base_effects['speed']:.2f}x")
            if base_effects.get('crop'):
                effects_desc.append(f"裁剪{base_effects['crop'].get('percent', 0)*100:.0f}%")
            
            enhanced = visual_result.get('enhanced_effects', [])
            effect_names = {
                'saturation': '饱和度',
                'brightness': '亮度',
                'contrast': '对比度',
                'rgb_shift': 'RGB偏移',
                'gaussian_blur': '高斯模糊',
                'frame_skip': '抽帧',
                'frame_swap': '帧交换',
                'pip': '画中画',
                'edge_blur': '背景模糊',
            }
            for e in enhanced:
                effects_desc.append(effect_names.get(e, e))
            
            results.append({
                'index': actual_index,  # 使用实际索引，而不是循环变量 i
                'status': 'completed',
                'effects': effects_desc,
                'file_path': final_path if audio_result['success'] else output_path,
            })
            
            logger.info(f"变体 {i}/{count} 生成完成")
        else:
            results.append({
                'index': actual_index,  # 使用实际索引
                'status': 'failed',
                'error': visual_result.get('error', '视觉变体生成失败'),
            })
    
    logger.info(f"变体生成完成: {len([r for r in results if r['status'] == 'completed'])}/{count}")
    
    # 更新数据库状态
    completed_count = len([r for r in results if r['status'] == 'completed'])
    try:
        import sqlite3
        from datetime import datetime
        
        db_path = Path(settings.DATA_DIR) / 'shorts_fission.db'
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 更新视频状态 - 累加 variant_count
        c.execute("""
            UPDATE videos 
            SET status = ?, 
                variant_count = variant_count + ?, 
                variant_progress = 100,
                completed_at = ?
            WHERE id = ?
        """, (
            'COMPLETED' if completed_count == count else 'FAILED',
            completed_count,
            datetime.now().isoformat(),
            video_id
        ))
        
        # 添加变体记录
        for r in results:
            if r['status'] == 'completed' and r.get('file_path'):
                effects_str = ' · '.join(r.get('effects', []))
                c.execute("""
                    INSERT INTO variants (video_id, variant_index, status, file_path, effects_applied, completed_at)
                    VALUES (?, ?, 'COMPLETED', ?, ?, ?)
                """, (
                    video_id,
                    r['index'],
                    r['file_path'],
                    effects_str,
                    datetime.now().isoformat()
                ))
        
        conn.commit()
        conn.close()
        logger.info(f"数据库更新完成: 视频 {video_id}, 变体 {completed_count}/{count}")
        
    except Exception as e:
        logger.error(f"更新数据库失败: {e}")
    
    return {
        'status': 'completed',
        'video_id': video_id,
        'total': count,
        'results': results,
    }


@celery_app.task(bind=True)
def batch_download_task(self, account_url: str, output_dir: str, start_date: str = None, end_date: str = None):
    """批量下载任务"""
    logger.info(f"开始批量下载: {account_url}")
    
    result = downloader.batch_download(
        account_url,
        output_dir,
        start_date,
        end_date,
        max_count=50
    )
    
    return result
