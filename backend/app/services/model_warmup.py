# backend/app/services/model_warmup.py
"""
模型预热服务 - 启动时预先加载模型

解决 WhisperX 模型每次请求都重新加载的问题
通过 Celery Worker 启动时预热，减少首次请求延迟

Created: 2026-03-26
"""

import os
import time
from loguru import logger
from typing import Optional

# 全局模型缓存
_warmup_status = {
    "whisperx_loaded": False,
    "whisperx_model": None,
    "whisperx_device": None,
    "warmup_time": None,
}


def warmup_whisperx(model_size: str = "base") -> bool:
    """
    预热 WhisperX 模型
    
    Args:
        model_size: 模型大小 (tiny/base/small/medium)
    
    Returns:
        True = 预热成功, False = 预热失败
    """
    if _warmup_status["whisperx_loaded"]:
        logger.info("[预热] WhisperX 模型已加载，跳过预热")
        return True
    
    start_time = time.time()
    
    try:
        import whisperx
        
        # 检测设备
        device = "cpu"
        compute_type = "int8"
        
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                compute_type = "float16"
                logger.info(f"[预热] 检测到 GPU: {torch.cuda.get_device_name(0)}")
        except:
            pass
        
        logger.info(f"[预热] 开始加载 WhisperX 模型: {model_size}, 设备: {device}")
        
        # 加载模型
        model = whisperx.load_model(
            model_size,
            device,
            compute_type=compute_type
        )
        
        # 缓存模型
        _warmup_status["whisperx_loaded"] = True
        _warmup_status["whisperx_model"] = model
        _warmup_status["whisperx_device"] = device
        _warmup_status["warmup_time"] = time.time() - start_time
        
        logger.info(f"[预热] WhisperX 模型预热完成，耗时: {_warmup_status['warmup_time']:.2f}秒")
        
        return True
    
    except Exception as e:
        logger.error(f"[预热] WhisperX 模型预热失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_warmup_status() -> dict:
    """获取预热状态"""
    return _warmup_status.copy()


def get_cached_whisperx_model():
    """获取缓存的 WhisperX 模型"""
    if _warmup_status["whisperx_loaded"]:
        return _warmup_status["whisperx_model"]
    return None


def get_cached_device() -> Optional[str]:
    """获取缓存的设备"""
    if _warmup_status["whisperx_loaded"]:
        return _warmup_status["whisperx_device"]
    return None
