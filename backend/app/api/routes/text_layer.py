# backend/app/api/routes/text_layer.py
"""
文字层 v2.0 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.text_layer_engine_v2 import (
    get_available_effects,
    get_available_scenes,
)
from app.services.effect_templates import (
    SCENE_CONFIG,
    EFFECT_TEMPLATES,
    get_random_effects,
)

router = APIRouter(prefix="/api/text-layer", tags=["text-layer"])


class GenerateVariantsRequest(BaseModel):
    """生成变体请求"""
    scene: str
    effects: Optional[List[str]] = None
    variant_count: int = 10
    enable_subtitle: bool = True
    subtitle_source: str = "auto"


@router.get("/scenes")
async def list_scenes():
    """获取所有可用场景"""
    scenes = get_available_scenes()
    return {"success": True, "scenes": scenes}


@router.get("/scenes/{scene_id}/effects")
async def get_scene_effects_api(scene_id: str):
    """获取场景对应的特效列表"""
    if scene_id not in SCENE_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid scene: {scene_id}")
    
    effects = get_available_effects(scene_id)
    return {
        "success": True,
        "scene": scene_id,
        "scene_name": SCENE_CONFIG[scene_id]['name'],
        "effects": effects
    }


@router.get("/effects")
async def list_all_effects():
    """获取所有可用特效"""
    effects = get_available_effects()
    return {"success": True, "effects": effects}


@router.get("/effects/{effect_id}")
async def get_effect_detail(effect_id: str):
    """获取特效详情"""
    if effect_id not in EFFECT_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid effect: {effect_id}")
    
    template = EFFECT_TEMPLATES[effect_id]
    
    return {
        "success": True,
        "effect": {
            "id": effect_id,
            "name": template['name'],
            "scene": template['scene'],
            "performance": template['performance'],
            "color_variants": template.get('color_variants', []),
        }
    }


@router.post("/scenes/{scene_id}/random-effects")
async def get_random_effects_api(scene_id: str, count: Optional[int] = None):
    """获取场景的随机特效组合"""
    if scene_id not in SCENE_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid scene: {scene_id}")
    
    effects = get_random_effects(scene_id, count)
    
    return {
        "success": True,
        "scene": scene_id,
        "effects": effects,
        "count": len(effects)
    }
