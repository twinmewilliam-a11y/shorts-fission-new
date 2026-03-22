# backend/app/services/remotion_caption.py
"""
Remotion 词级动画生成器

使用 Remotion (React + CSS) 生成真正的逐词动画字幕

Created: 2026-03-22
Version: 1.0
Author: T.W (Twin William)
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


class RemotionCaptionGenerator:
    """Remotion 词级动画生成器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.remotion_dir = self.config.get(
            'remotion_dir',
            '/root/.openclaw/workspace/projects/shorts-fission/remotion-caption'
        )
        
    def generate_project(
        self,
        words_data: List[Dict],
        output_dir: str,
        template: str = 'pop_highlight',
        position: str = 'center',
        video_width: int = 1080,
        video_height: int = 1920,
        fps: int = 30,
    ) -> Dict:
        """
        生成 Remotion 项目
        
        Args:
            words_data: WhisperX 词级数据
            output_dir: 输出目录
            template: 动画模板
            position: 字幕位置
            video_width: 视频宽度
            video_height: 视频高度
            fps: 帧率
        
        Returns:
            {
                'success': True/False,
                'project_dir': 项目目录,
                'words_json': words.json 路径,
                'render_command': 渲染命令,
                'error': 错误信息
            }
        """
        try:
            # 计算视频时长（最后一词结束 + 1秒）
            last_word = words_data[-1] if words_data else {'end': 5}
            duration_in_frames = int((last_word['end'] + 1) * fps)
            
            # 创建项目目录
            project_dir = Path(output_dir) / 'remotion-caption'
            src_dir = project_dir / 'src'
            src_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成 words.json
            words_json_path = src_dir / 'words.json'
            with open(words_json_path, 'w', encoding='utf-8') as f:
                json.dump(words_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[Remotion] 项目已生成: {project_dir}")
            logger.info(f"[Remotion] words.json: {len(words_data)} 个词")
            
            # 构建渲染命令
            render_command = self._build_render_command(
                project_dir,
                duration_in_frames,
                fps,
                video_width,
                video_height
            )
            
            return {
                'success': True,
                'project_dir': str(project_dir),
                'words_json': str(words_json_path),
                'render_command': render_command,
                'duration_in_frames': duration_in_frames,
                'fps': fps,
            }
            
        except Exception as e:
            logger.error(f"[Remotion] 项目生成失败: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def _build_render_command(
        self,
        project_dir: Path,
        duration_in_frames: int,
        fps: int,
        width: int,
        height: int,
    ) -> str:
        """构建渲染命令"""
        output_path = project_dir / 'out' / 'caption.mp4'
        
        return (
            f"cd {project_dir} && "
            f"npx remotion render src/index.ts Caption {output_path} "
            f"--frames 0-{duration_in_frames} "
            f"--fps {fps} "
            f"--width {width} "
            f"--height {height} "
            f"--codec h264"
        )
    
    def render(
        self,
        words_data: List[Dict],
        output_video_path: str,
        template: str = 'pop_highlight',
        position: str = 'center',
    ) -> Dict:
        """
        生成并渲染 Remotion 字幕视频
        
        Args:
            words_data: WhisperX 词级数据
            output_video_path: 输出视频路径
            template: 动画模板
            position: 字幕位置
        
        Returns:
            {'success': True/False, 'output_path': 视频路径, 'error': 错误信息}
        """
        # 生成项目
        output_dir = Path(output_video_path).parent
        project_result = self.generate_project(
            words_data=words_data,
            output_dir=str(output_dir),
            template=template,
            position=position,
        )
        
        if not project_result['success']:
            return project_result
        
        # 执行渲染
        try:
            logger.info(f"[Remotion] 开始渲染: {project_result['render_command']}")
            
            result = subprocess.run(
                project_result['render_command'],
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
            )
            
            if result.returncode == 0:
                # 移动到目标位置
                caption_path = Path(project_result['project_dir']) / 'out' / 'caption.mp4'
                if caption_path.exists():
                    os.rename(caption_path, output_video_path)
                    logger.info(f"[Remotion] 渲染完成: {output_video_path}")
                    return {
                        'success': True,
                        'output_path': output_video_path,
                    }
                else:
                    return {
                        'success': False,
                        'error': '渲染输出文件不存在',
                    }
            else:
                logger.error(f"[Remotion] 渲染失败: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr[-500:] if result.stderr else '未知错误',
                }
                
        except subprocess.TimeoutExpired:
            logger.error("[Remotion] 渲染超时")
            return {
                'success': False,
                'error': '渲染超时（5分钟）',
            }
        except Exception as e:
            logger.error(f"[Remotion] 渲染异常: {e}")
            return {
                'success': False,
                'error': str(e),
            }


def generate_remotion_caption(
    words_data: List[Dict],
    output_path: str,
    template: str = 'pop_highlight',
    position: str = 'center',
) -> Dict:
    """
    生成 Remotion 词级动画字幕（便捷函数）
    
    Args:
        words_data: WhisperX 词级数据
        output_path: 输出视频路径
        template: 动画模板
        position: 字幕位置
    
    Returns:
        {'success': True/False, 'output_path': 视频路径, 'error': 错误信息}
    """
    generator = RemotionCaptionGenerator()
    return generator.render(
        words_data=words_data,
        output_video_path=output_path,
        template=template,
        position=position,
    )
