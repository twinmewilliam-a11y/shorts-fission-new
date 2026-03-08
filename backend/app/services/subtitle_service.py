# backend/app/services/subtitle_service.py
"""
字幕处理服务 - 使用 WhisperX 提取字幕
"""
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

class SubtitleService:
    """字幕处理服务"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.whisper_model = config.get('whisper_model', 'base')
    
    def extract_subtitles(
        self, 
        video_path: str, 
        output_dir: str,
        language: str = None
    ) -> Dict:
        """从视频中提取字幕"""
        output_srt = os.path.join(output_dir, 'subtitles.srt')
        
        try:
            # 使用 whisper 命令行工具
            cmd = [
                'whisper',
                video_path,
                '--model', self.whisper_model,
                '--output_format', 'srt',
                '--output_dir', output_dir,
            ]
            
            if language:
                cmd.extend(['--language', language])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                # 读取生成的字幕文件
                srt_files = list(Path(output_dir).glob('*.srt'))
                if srt_files:
                    with open(srt_files[0], 'r', encoding='utf-8') as f:
                        srt_content = f.read()
                    
                    return {
                        'success': True,
                        'srt_path': str(srt_files[0]),
                        'srt_content': srt_content,
                        'segments': self._parse_srt(srt_content)
                    }
            
            return {'success': False, 'error': result.stderr}
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '字幕提取超时'}
        except FileNotFoundError:
            return {'success': False, 'error': 'Whisper 未安装'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _parse_srt(self, srt_content: str) -> List[Dict]:
        """解析 SRT 字幕文件"""
        segments = []
        lines = srt_content.strip().split('\n')
        
        i = 0
        while i < len(lines):
            # 跳过序号
            if lines[i].strip().isdigit():
                i += 1
                if i >= len(lines):
                    break
                
                # 时间戳
                time_line = lines[i].strip()
                if '-->' in time_line:
                    start, end = time_line.split('-->')
                    i += 1
                    
                    # 字幕文本
                    text_lines = []
                    while i < len(lines) and lines[i].strip():
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    segments.append({
                        'start': self._parse_time(start.strip()),
                        'end': self._parse_time(end.strip()),
                        'text': ' '.join(text_lines)
                    })
            
            i += 1
        
        return segments
    
    def _parse_time(self, time_str: str) -> float:
        """解析 SRT 时间格式为秒数"""
        # 格式: 00:00:00,000
        parts = time_str.replace(',', ':').split(':')
        hours, minutes, seconds, millis = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds + millis / 1000
    
    def translate_subtitles(
        self, 
        srt_content: str, 
        target_language: str,
        llm_provider: str = 'gemini'
    ) -> Dict:
        """翻译字幕（使用 LLM）"""
        # TODO: 实现 LLM 翻译
        # 可以使用 Gemini / DeepSeek / OpenAI
        return {
            'success': False,
            'error': '翻译功能待实现'
        }
    
    def burn_subtitles(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        style: Dict = None
    ) -> Dict:
        """将字幕烧录到视频中"""
        # 默认样式
        default_style = {
            'fontsize': 24,
            'fontcolor': 'white',
            'borderw': 2,
            'bordercolor': 'black',
            'margin_v': 50,
        }
        
        if style:
            default_style.update(style)
        
        # 构建 FFmpeg 字幕滤镜
        subtitle_filter = (
            f"subtitles={srt_path}:"
            f"force_style='FontSize={default_style['fontsize']},"
            f"PrimaryColour=&H{self._color_to_ass(default_style['fontcolor'])},"
            f"Outline={default_style['borderw']},"
            f"OutlineColour=&H{self._color_to_ass(default_style['bordercolor'])},"
            f"MarginV={default_style['margin_v']}'"
        )
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', subtitle_filter,
            '-c:a', 'copy',
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            
            if result.returncode == 0:
                return {'success': True, 'output_path': output_path}
            else:
                return {'success': False, 'error': result.stderr.decode()}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _color_to_ass(self, color: str) -> str:
        """转换颜色为 ASS 格式"""
        colors = {
            'white': 'FFFFFF',
            'black': '000000',
            'yellow': 'FFFF00',
            'red': 'FF0000',
            'blue': '0000FF',
            'green': '00FF00',
        }
        return colors.get(color.lower(), 'FFFFFF')
