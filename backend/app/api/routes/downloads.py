# backend/app/api/routes/downloads.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import zipfile
import tempfile

from app.database import get_db
from app.models.video import Video
from app.models.variant import Variant

router = APIRouter()

@router.get("/video/{video_id}")
async def download_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download source video"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not video.source_path or not os.path.exists(video.source_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        video.source_path,
        media_type="video/mp4",
        filename=f"{video.title or video.video_id}.mp4"
    )

@router.get("/variant/{variant_id}")
async def download_variant(
    variant_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download a single variant"""
    result = await db.execute(select(Variant).where(Variant.id == variant_id))
    variant = result.scalar_one_or_none()
    
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    if not variant.file_path or not os.path.exists(variant.file_path):
        raise HTTPException(status_code=404, detail="Variant file not found")
    
    return FileResponse(
        variant.file_path,
        media_type="video/mp4",
        filename=f"variant_{variant.variant_index}.mp4"
    )

@router.post("/batch/{video_id}")
async def batch_download_variants(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download all variants as ZIP"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Get all variants
    result = await db.execute(
        select(Variant).where(Variant.video_id == video_id).order_by(Variant.variant_index)
    )
    variants = result.scalars().all()
    
    if not variants:
        raise HTTPException(status_code=404, detail="No variants found")
    
    # Create ZIP file
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        with zipfile.ZipFile(tmp.name, 'w') as zf:
            for variant in variants:
                if variant.file_path and os.path.exists(variant.file_path):
                    zf.write(variant.file_path, f"variant_{variant.variant_index}.mp4")
        
        return FileResponse(
            tmp.name,
            media_type="application/zip",
            filename=f"variants_video_{video_id}.zip"
        )

@router.get("/metadata/{video_id}")
async def download_metadata(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download metadata JSON for video and variants"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Get all variants
    result = await db.execute(
        select(Variant).where(Variant.video_id == video_id).order_by(Variant.variant_index)
    )
    variants = result.scalars().all()
    
    metadata = {
        "video": {
            "id": video.id,
            "platform": video.platform,
            "title": video.title,
            "description": video.description,
            "duration": video.duration
        },
        "variants": [
            {
                "index": v.variant_index,
                "title": v.title,
                "description": v.description,
                "tags": v.tags,
                "effects": v.effects_applied
            }
            for v in variants
        ]
    }
    
    import json
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as tmp:
        json.dump(metadata, tmp, indent=2, ensure_ascii=False)
        
        return FileResponse(
            tmp.name,
            media_type="application/json",
            filename=f"metadata_video_{video_id}.json"
        )
