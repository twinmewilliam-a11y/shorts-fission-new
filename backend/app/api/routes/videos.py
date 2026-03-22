# backend/app/api/routes/videos.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import os
import shutil
import subprocess
import uuid
import asyncio

from app.database import get_db
from app.models.video import Video, VideoStatus
from app.services.downloader import VideoDownloader
from app.config import settings

# 初始化下载器
downloader = VideoDownloader({
    'proxy_url': settings.PROXY_URL,
    'proxy_enabled': settings.PROXY_ENABLED,
    'videos_dir': settings.VIDEOS_DIR,
})

router = APIRouter()

# Schemas
class VideoCreate(BaseModel):
    url: str
    platform: Optional[str] = None
    target_variant_count: int = 15

class VideoResponse(BaseModel):
    id: int
    platform: str
    video_id: str
    url: str
    title: Optional[str]
    duration: int
    status: VideoStatus
    variant_count: int
    target_variant_count: int
    download_progress: int
    variant_progress: int
    resolution: Optional[str] = None  # e.g., "720p", "1080p", "360p"
    has_subtitle: bool = False  # 是否有字幕
    created_at: datetime

    class Config:
        from_attributes = True

class VideoListResponse(BaseModel):
    total: int
    videos: List[VideoResponse]

# Routes
@router.post("/single", response_model=VideoResponse)
async def create_single_video(
    video_data: VideoCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Add a single video for download"""
    # 检测平台
    platform = downloader._detect_platform(video_data.url)
    
    # 创建视频记录
    video = Video(
        url=video_data.url,
        platform=platform,
        video_id="temp_" + str(datetime.now().timestamp()),
        target_variant_count=video_data.target_variant_count,
        status=VideoStatus.DOWNLOADING
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    # 使用 Celery 后台下载
    from app.tasks.celery_tasks import download_video_task
    download_video_task.delay(video.id, video_data.url, settings.VIDEOS_DIR)
    
    return video

@router.post("/batch")
async def create_batch_download(
    account_url: str,
    start_date: str,
    end_date: str,
    db: AsyncSession = Depends(get_db)
):
    """Batch download videos from account within date range"""
    # TODO: Implement batch download logic
    return {"message": "Batch download started", "account_url": account_url}

@router.get("", response_model=VideoListResponse)
async def list_videos(
    status: Optional[VideoStatus] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all videos with optional status filter"""
    query = select(Video)
    if status:
        query = query.where(Video.status == status)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    return {"total": len(videos), "videos": videos}

# ==================== 词级动画模板 API（必须在 /{video_id} 之前）====================

from app.services.word_level_animation import get_available_templates, get_available_positions

class AnimationTemplateResponse(BaseModel):
    """动画模板响应"""
    id: str
    name: str
    name_en: str
    description: str
    scene: List[str]

class AnimationPositionResponse(BaseModel):
    """动画位置响应"""
    id: str
    name: str

@router.get("/animation-templates", response_model=List[AnimationTemplateResponse])
async def list_animation_templates():
    """
    获取可用的词级动画模板列表
    
    模板说明：
    - pop_highlight: MrBeast 风格，当前词放大+黄色高亮
    - karaoke_flow: 卡拉OK风格，逐字变色
    - hype_gaming: 电竞风格，荧光色+发光+抖动
    """
    templates = get_available_templates()
    return templates

@router.get("/animation-positions", response_model=List[AnimationPositionResponse])
async def list_animation_positions():
    """
    获取可用的字幕位置列表
    
    位置说明：
    - bottom_center: 底部居中（默认）
    - bottom_left: 底部左
    - bottom_right: 底部右
    - center: 屏幕中央
    - top_center: 顶部居中
    """
    positions = get_available_positions()
    return positions

# ==================== 动态路由（{video_id}）====================

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get video details"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a video and all its variants (including files)"""
    import os
    import shutil
    from sqlalchemy import delete as sql_delete
    from app.models.variant import Variant
    
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 删除变体文件夹
    variant_dir = Path(settings.DATA_DIR) / "variants" / str(video_id)
    if variant_dir.exists():
        shutil.rmtree(variant_dir)
    
    # 删除源视频文件
    if video.source_path and os.path.exists(video.source_path):
        os.remove(video.source_path)
    
    # 手动删除所有变体记录（外键不是 CASCADE）
    await db.execute(sql_delete(Variant).where(Variant.video_id == video_id))
    
    # 删除视频记录
    await db.delete(video)
    await db.commit()
    
    return {"message": "Video and all variants deleted", "video_id": video_id}


# ==================== 视频上传功能 ====================

def get_video_resolution(file_path: str) -> Optional[str]:
    """使用 ffprobe 获取视频分辨率"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            parts = result.stdout.strip().split(',')
            if len(parts) == 2:
                width, height = int(parts[0]), int(parts[1])
                # 返回标准分辨率格式
                if height >= 1080:
                    return "1080p"
                elif height >= 720:
                    return "720p"
                elif height >= 480:
                    return "480p"
                elif height >= 360:
                    return "360p"
                else:
                    return f"{height}p"
    except Exception as e:
        print(f"获取分辨率失败: {e}")
    return None


@router.post("/upload", response_model=List[VideoResponse])
async def upload_videos(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """批量上传视频文件"""
    uploaded_videos = []
    videos_dir = Path(settings.VIDEOS_DIR)
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        if not file.filename:
            continue
            
        # 检查文件类型
        allowed_types = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_types:
            continue
        
        # 生成唯一文件名
        video_id = f"upload_{uuid.uuid4().hex[:12]}"
        filename = f"{video_id}{file_ext}"
        file_path = videos_dir / filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 获取视频分辨率
        resolution = get_video_resolution(str(file_path))
        
        # 创建数据库记录
        video = Video(
            platform="upload",
            video_id=video_id,
            url=f"file://{file_path}",
            title=file.filename,
            source_path=str(file_path),
            resolution=resolution,
            status=VideoStatus.DOWNLOADED,  # 上传完成即视为已下载
            target_variant_count=0,  # 默认不处理，需要用户选择
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)
        uploaded_videos.append(video)
    
    return uploaded_videos


# ==================== Animated Caption 请求模型 ====================

class SetVariantCountRequest(BaseModel):
    """设置变体数量请求体"""
    count: int
    append: bool = False
    enable_subtitle: bool = True
    animation_template: Optional[str] = None
    animation_position: str = 'center'

@router.post("/{video_id}/set-variant-count")
async def set_variant_count(
    video_id: int,
    request: SetVariantCountRequest,
    db: AsyncSession = Depends(get_db)
):
    """设置变体数量并开始处理 - Animated Caption 版本
    
    Args:
        count: 变体数量
        append: True=累加到现有变体数量，False=设置为新数量
        enable_subtitle: 是否启用 Animated Caption
        animation_template: 动画模板 ID (pop_highlight/karaoke_flow/hype_gaming)，None=随机
        animation_position: 字幕位置 (bottom_center/bottom_left/bottom_right/center/top_center)
        use_remotion: 是否使用 Remotion 渲染（True=Remotion词级动画, False=ASS静态字幕）
    """
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.status not in [VideoStatus.DOWNLOADED, VideoStatus.COMPLETED, VideoStatus.FAILED]:
        raise HTTPException(status_code=400, detail="视频状态不允许处理")
    
    if request.count <= 0:
        raise HTTPException(status_code=400, detail="变体数量必须大于0")
    
    # 计算新的变体数量
    if request.append:
        new_count = video.target_variant_count + request.count
        start_index = video.variant_count + 1
    else:
        new_count = request.count
        start_index = 1
    
    # 更新视频记录
    video.target_variant_count = new_count
    video.status = VideoStatus.PROCESSING
    video.has_subtitle = request.enable_subtitle
    await db.commit()
    
    # 触发变体生成任务
    from app.tasks.celery_tasks import generate_variants_task
    if video.source_path:
        generate_variants_task.delay(
            video.id, 
            video.source_path, 
            request.count, 
            start_index=start_index,
            enable_subtitle=request.enable_subtitle,
            animation_template=request.animation_template,
            animation_position=request.animation_position,
        )
    
    return {
        "message": "开始生成变体",
        "new_count": new_count,
        "adding": request.count,
        "enable_subtitle": request.enable_subtitle,
        "animation_template": request.animation_template or "random",
        "animation_position": request.animation_position,
    }


@router.post("/{video_id}/upload-subtitle")
async def upload_subtitle(
    video_id: int,
    subtitle: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """上传字幕文件
    
    支持 .srt, .vtt, .ass 格式
    """
    # 检查视频是否存在
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 检查文件格式
    allowed_extensions = ['.srt', '.vtt', '.ass', '.ssa']
    file_ext = os.path.splitext(subtitle.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的字幕格式，支持: {allowed_extensions}")
    
    # 保存字幕文件
    subtitle_dir = Path(settings.SUBTITLES_DIR) / str(video_id)
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    
    subtitle_path = subtitle_dir / f"uploaded{file_ext}"
    
    with open(subtitle_path, "wb") as f:
        content = await subtitle.read()
        f.write(content)
    
    # 更新视频记录
    video.subtitle_path = str(subtitle_path)
    video.has_subtitle = True
    await db.commit()
    
    return {
        "message": "字幕上传成功",
        "path": str(subtitle_path),
        "filename": subtitle.filename
    }


# ==================== 词级动画配置 Schema ====================

class SetVariantCountWithAnimation(BaseModel):
    """设置变体数量（带词级动画配置）"""
    count: int
    append: bool = False
    enable_subtitle: bool = True
    subtitle_source: str = "auto"  # auto/upload/whisperx
    animation_template: Optional[str] = None  # 指定模板，None 表示随机
    animation_position: str = "bottom_center"  # 位置

@router.post("/{video_id}/set-variant-count-v2")
async def set_variant_count_v2(
    video_id: int,
    config: SetVariantCountWithAnimation,
    db: AsyncSession = Depends(get_db)
):
    """
    设置变体数量并开始处理（v2 - 支持词级动画配置）
    
    Args:
        count: 变体数量
        append: True=累加到现有变体数量，False=设置为新数量
        enable_subtitle: 是否启用词级动画字幕
        subtitle_source: 字幕来源 - auto（自动检测）/ upload（上传）/ whisperx（转录）
        animation_template: 动画模板 ID
            - pop_highlight: MrBeast 风格
            - karaoke_flow: 卡拉OK风格
            - hype_gaming: 电竞风格
            - None: 随机选择
        animation_position: 字幕位置
            - bottom_center: 底部居中（默认）
            - bottom_left: 底部左
            - bottom_right: 底部右
            - center: 屏幕中央
            - top_center: 顶部居中
    """
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.status not in [VideoStatus.DOWNLOADED, VideoStatus.COMPLETED, VideoStatus.FAILED]:
        raise HTTPException(status_code=400, detail="视频状态不允许处理")
    
    if config.count <= 0:
        raise HTTPException(status_code=400, detail="变体数量必须大于0")
    
    # 验证模板
    if config.animation_template:
        valid_templates = [t['id'] for t in get_available_templates()]
        if config.animation_template not in valid_templates:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的模板 ID: {config.animation_template}，可选: {valid_templates}"
            )
    
    # 验证位置
    valid_positions = [p['id'] for p in get_available_positions()]
    if config.animation_position not in valid_positions:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的位置 ID: {config.animation_position}，可选: {valid_positions}"
        )
    
    # 计算新的变体数量
    if config.append:
        new_count = video.target_variant_count + config.count
        start_index = video.variant_count + 1
    else:
        new_count = config.count
        start_index = 1
    
    # 更新视频记录
    video.target_variant_count = new_count
    video.status = VideoStatus.PROCESSING
    video.has_subtitle = config.enable_subtitle
    await db.commit()
    
    # 触发变体生成任务
    from app.tasks.celery_tasks import generate_variants_task
    if video.source_path:
        # v2 API 默认启用词级动画
        generate_variants_task.delay(
            video.id, 
            video.source_path, 
            config.count, 
            start_index=start_index,
            enable_subtitle=config.enable_subtitle,
            subtitle_source=config.subtitle_source,
            use_text_layer_v2=True,  # 启用词级动画
            animation_template=config.animation_template,
            animation_position=config.animation_position,
        )
    
    return {
        "message": "开始生成变体",
        "new_count": new_count,
        "adding": config.count,
        "enable_subtitle": config.enable_subtitle,
        "subtitle_source": config.subtitle_source,
        "animation_template": config.animation_template or "random",
        "animation_position": config.animation_position,
    }

