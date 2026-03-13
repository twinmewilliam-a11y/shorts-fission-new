# backend/app/api/routes/variants.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
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
    from fastapi.responses import FileResponse
    import zipfile
    import tempfile
    import os
    from pathlib import Path
    
    # 获取视频的所有变体
    result = await db.execute(
        select(Variant).where(Variant.video_id == video_id)
    )
    variants = result.scalars().all()
    
    if not variants:
        raise HTTPException(status_code=404, detail="No variants found")
    
    # 创建临时 ZIP 文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        with zipfile.ZipFile(tmp.name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for variant in variants:
                if variant.file_path and Path(variant.file_path).exists():
                    zf.write(
                        variant.file_path,
                        Path(variant.file_path).name
                    )
        
        return FileResponse(
            tmp.name,
            media_type='application/zip',
            filename=f'variants_{video_id}.zip'
        )
