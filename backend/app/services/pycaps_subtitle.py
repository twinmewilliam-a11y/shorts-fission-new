"""
PyCaps 字幕服务 - 使用 PyCaps 生成词级动画字幕
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PyCapsSubtitleService:
    """PyCaps 字幕服务"""
    
    # 模板映射
    TEMPLATE_MAP = {
        'pop_highlight': 'minimalist',
        'karaoke_flow': 'word-focus',
        'hype_gaming': 'hype',
    }
    
    def __init__(self):
        from pycaps import TemplateLoader
        self.TemplateLoader = TemplateLoader
    
    def render_subtitle_video(
        self,
        input_video_path: str,
        output_video_path: str,
        template: str = 'pop_highlight',
        language: str = None,
    ) -> Dict[str, Any]:
        """
        使用 PyCaps 渲染带字幕的视频
        
        Args:
            input_video_path: 输入视频路径
            output_video_path: 输出视频路径
            template: 模板名称 (pop_highlight/karaoke_flow/hype_gaming)
            language: 语言代码 (如 'en', 'zh')
        
        Returns:
            dict: 包含 success, output_path, error 等信息
        """
        try:
            # 映射模板名称
            pycaps_template = self.TEMPLATE_MAP.get(template, 'minimalist')
            
            logger.info(f"[PyCaps] 开始渲染: {input_video_path}")
            logger.info(f"[PyCaps] 模板: {template} -> {pycaps_template}")
            
            # 确保输出目录存在
            output_path = Path(output_video_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用 TemplateLoader 加载模板，返回 builder
            builder = (
                self.TemplateLoader(pycaps_template)
                .with_input_video(input_video_path)
                .load(False)  # 返回 CapsPipelineBuilder
            )
            
            # 设置输出路径
            builder = builder.with_output_video(output_video_path)
            
            # 配置 Whisper（可选语言）
            if language:
                builder = builder.with_whisper_config(language=language)
            
            # 构建 pipeline
            pipeline = builder.build()
            
            # 执行渲染
            pipeline.run()
            
            if output_path.exists():
                logger.info(f"[PyCaps] 渲染完成: {output_video_path}")
                return {
                    'success': True,
                    'output_path': str(output_path),
                    'template': pycaps_template,
                }
            else:
                logger.error("[PyCaps] 输出文件不存在")
                return {
                    'success': False,
                    'error': 'Output file not created',
                }
                
        except Exception as e:
            logger.error(f"[PyCaps] 渲染失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
            }


# 便捷函数
def render_pycaps_subtitle(
    input_video_path: str,
    output_video_path: str,
    template: str = 'pop_highlight',
    language: str = None,
) -> Dict[str, Any]:
    """
    使用 PyCaps 渲染字幕视频
    
    Args:
        input_video_path: 输入视频路径
        output_video_path: 输出视频路径
        template: 模板名称
        language: 语言代码
    
    Returns:
        dict: 渲染结果
    """
    service = PyCapsSubtitleService()
    return service.render_subtitle_video(
        input_video_path,
        output_video_path,
        template,
        language,
    )
