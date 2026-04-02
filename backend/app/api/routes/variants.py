# backend/app/api/routes/variants.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

from app.database import get_db
from app.models.variant import Variant, VariantStatus
from app.models.video import Video, VideoStatus
from app.services.variant_engine import VariantEngine, AudioVariantEngine
from app.config import settings
from app.api.websocket import notify_variant_progress

# 初始化变体引擎 v4.0 PIP
visual_engine = VariantEngine({
    'min_enhanced': 3,
    'max_enhanced': 5,
    'whisperx_enabled': False,
})

audio_engine = AudioVariantEngine({
    'bgm_dir': settings.BGM_DIR,
    'bgm_volume': 0.3,
})

router = APIRouter()

class VariantResponse(BaseModel):
    id: int
    video_id: int
    variant_index: int
    status: VariantStatus
    title: str | None
    effects_applied: str | None
    file_path: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True

class VariantListResponse(BaseModel):
    total: int
    variants: List[VariantResponse]

@router.post("/{video_id}/generate")
async def generate_variants(
    video_id: int,
    count: int = 15,
    sport_type: str = "default",
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Start generating variants for a video"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.status != VideoStatus.DOWNLOADED:
        raise HTTPException(status_code=400, detail="Video must be downloaded first")
    
    # Update video status
    video.status = VideoStatus.PROCESSING
    video.target_variant_count = count
    
    # Create variant records
    for i in range(1, count + 1):
        variant = Variant(
            video_id=video_id,
            variant_index=i,
            status=VariantStatus.PENDING
        )
        db.add(variant)
    
    await db.commit()
    
    # 后台生成变体
    async def generate_in_background():
        output_dir = Path(settings.VARIANTS_DIR) / str(video_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        source_path = video.source_path
        if not source_path or not Path(source_path).exists():
            return
        
        completed = 0
        async with db.begin():
            for i in range(1, count + 1):
                # 生成视觉变体
                output_path = str(output_dir / f"variant_{i:03d}.mp4")
                visual_result = visual_engine.generate_variant(
                    source_path,
                    output_path,
                    seed=video_id * 1000 + i
                )
                
                if visual_result['success']:
                    # 生成音频变体
                    final_path = str(output_dir / f"final_{i:03d}.mp4")
                    audio_result = audio_engine.replace_bgm(
                        output_path,
                        final_path,
                        sport_type=sport_type
                    )
                    
                    final_file = final_path if audio_result['success'] else output_path
                    
                    # 更新变体记录
                    variant_record = await db.execute(
                        select(Variant).where(
                            Variant.video_id == video_id,
                            Variant.variant_index == i
                        )
                    )
                    variant = variant_record.scalar_one()
                    variant.status = VariantStatus.COMPLETED
                    variant.file_path = final_file
                    variant.effects_applied = str(visual_result['effects_applied'])
                    variant.completed_at = datetime.now()
                    
                    completed += 1
                    
                    # 更新视频进度
                    video_record = await db.get(Video, video_id)
                    video_record.variant_count = completed
                    video_record.variant_progress = int((completed / count) * 100)
                    
                    await db.commit()
                    
                    # WebSocket 通知
                    await notify_variant_progress(
                        video_id=video_id,
                        current=completed,
                        total=count,
                        variant_index=i,
                        effects=visual_result['effects_applied']
                    )
        
        # 完成后更新视频状态
        async with db.begin():
            video_record = await db.get(Video, video_id)
            video_record.status = VideoStatus.COMPLETED
            video_record.completed_at = datetime.now()
            await db.commit()
    
    if background_tasks:
        background_tasks.add_task(generate_in_background)
    
    return {"message": f"Started generating {count} variants", "video_id": video_id}

@router.get("/{video_id}", response_model=VariantListResponse)
async def list_variants(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all variants for a video"""
    result = await db.execute(
        select(Variant).where(Variant.video_id == video_id).order_by(Variant.variant_index)
    )
    variants = result.scalars().all()
    return {"total": len(variants), "variants": variants}

@router.get("/detail/{variant_id}", response_model=VariantResponse)
async def get_variant(
    variant_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get variant details"""
    result = await db.execute(select(Variant).where(Variant.id == variant_id))
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return variant

@router.delete("/{variant_id}")
async def delete_variant(
    variant_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a variant"""
    result = await db.execute(select(Variant).where(Variant.id == variant_id))
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    await db.delete(variant)
    await db.commit()
    return {"message": "Variant deleted"}


@router.get("/{video_id}/download")
async def download_variants(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download all variants as ZIP"""
    import zipfile
    import tempfile
    from pathlib import Path
    import os
    
    # 获取视频的所有变体
    result = await db.execute(
        select(Variant).where(Variant.video_id == video_id)
    )
    variants = result.scalars().all()
    
    if not variants:
        raise HTTPException(status_code=404, detail="No variants found")
    
    # 过滤存在的文件
    files = [
        (variant.file_path, Path(variant.file_path).name)
        for variant in variants
        if variant.file_path and Path(variant.file_path).exists()
    ]
    
    if not files:
        raise HTTPException(status_code=404, detail="No variant files found")
    
    # 创建临时 ZIP 文件
    temp_fd, temp_zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(temp_fd)
    
    try:
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path, file_name in files:
                zf.write(file_path, file_name)
        
        return FileResponse(
            path=temp_zip_path,
            filename=f"variants_{video_id}.zip",
            media_type="application/zip"
        )
    except Exception as e:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
        raise HTTPException(status_code=500, detail=f"打包失败: {str(e)}")


# ==================== 批量操作 API ====================

class BatchDownloadRequest(BaseModel):
    """批量下载请求"""
    video_ids: List[int]


@router.post("/batch-download")
async def batch_download_variants(
    request: BatchDownloadRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量下载多个视频的变体（打包成 ZIP）"""
    import tempfile
    
    # 收集所有变体文件
    file_mapping = []  # (file_path, display_name)
    
    for video_id in request.video_ids:
        # 检查视频是否存在且已完成
        video_result = await db.execute(select(Video).where(Video.id == video_id))
        video = video_result.scalar_one_or_none()
        
        if not video or video.status != VideoStatus.COMPLETED:
            continue
        
        # 获取变体文件目录
        variant_dir = Path(settings.VARIANTS_DIR) / str(video_id)
        if not variant_dir.exists():
            continue
        
        # 收集所有 .mp4 文件
        for mp4_file in sorted(variant_dir.glob("*.mp4")):
            # 使用编号格式：#001_video_title_variant_001.mp4
            safe_title = (video.title or "video")[:50].replace("/", "_").replace("\\", "_")
            display_name = f"#{video_id:03d}_{safe_title}_{mp4_file.stem}.mp4"
            file_mapping.append((str(mp4_file), display_name))
    
    if not file_mapping:
        raise HTTPException(status_code=404, detail="没有找到可下载的变体文件")
    
    # 创建临时 ZIP 文件
    temp_fd, temp_zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(temp_fd)
    
    try:
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path, display_name in file_mapping:
                # 限制文件名长度
                if len(display_name.encode('utf-8')) > 200:
                    ext = Path(display_name).suffix
                    base = display_name[:100]
                    display_name = base + ext
                zf.write(file_path, display_name)
        
        return FileResponse(
            path=temp_zip_path,
            filename=f"variants_batch_{len(file_mapping)}.zip",
            media_type="application/zip"
        )
    except Exception as e:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
        raise HTTPException(status_code=500, detail=f"打包失败: {str(e)}")
