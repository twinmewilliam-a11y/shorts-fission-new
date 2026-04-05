"""
字幕处理工具函数模块

包含：
- _render_remotion_subtitle_v2：使用 Remotion v2 渲染字幕视频
- _prepare_subtitle：准备字幕文件
- _burn_subtitle：烧录字幕到视频
- _get_video_resolution：获取视频分辨率

从此模块导入：
    - _render_remotion_subtitle_v2
    - _prepare_subtitle
    - _burn_subtitle
    - _get_video_resolution
"""
import json
import os
import random
import re
import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger

from app.config import settings


def _render_remotion_subtitle_v2(
    video_id: int,
    words_data: list,
    animation_template: str = 'pop_highlight',
    animation_position: str = 'bottom_center',
    fps: int = 30,
) -> Optional[str]:
    """使用 Remotion v2 渲染字幕视频（方案 A2: PNG 序列 + FFmpeg overlay）"""
    from app.services.subtitle.processor import process_subtitle
    
    try:
        remotion_dir = Path(__file__).parent.parent.parent.parent / 'remotion-caption'
        src_dir = remotion_dir / 'src'
        
        # 1. 处理字幕数据
        logger.info(f"[Remotion v2] 处理字幕: {len(words_data)} 词")
        subtitle_config = process_subtitle(
            words_data,
            template=animation_template,
            position=animation_position,
            font_size=56,  # 放大1倍：28 → 56
        )
        
        # 2. 保存配置
        config_path = src_dir / 'subtitle_config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(subtitle_config, f, ensure_ascii=False, indent=2)
        
        # 3. 计算时长（精确到最后一个词结束，不加缓冲）
        last_word = words_data[-1] if words_data else {'end': 5}
        duration_in_frames = int(last_word['end'] * fps) + 1  # 只加1帧，避免多余字幕
        
        # 4. 输出目录（PNG 序列）
        png_dir = remotion_dir / 'out' / f'png_{video_id}'
        png_dir.mkdir(parents=True, exist_ok=True)
        
        # 5. 渲染 PNG 序列（带 alpha 通道）
        # Remotion --sequence 需要使用相对路径（绝对路径会报错）
        relative_output = f'out/png_{video_id}/frames'
        
        # 方案 1: Remotion 并发渲染优化
        # Remotion 4.0+ 支持 --concurrency 参数
        render_cmd = [
            'npx', 'remotion', 'render',
            'src/index.ts', 'Caption',
            relative_output,  # 使用相对路径
            '--frames', f'0-{duration_in_frames}',
            '--fps', str(fps),
            '--width', '1080',
            '--height', '1920',
            '--sequence',
            '--concurrency', '4',  # 并发渲染 4 帧（根据 CPU 核心数调整）
        ]
        
        logger.info(f"[Remotion v2] 开始渲染 PNG 序列: {duration_in_frames} 帧")
        
        result = subprocess.run(render_cmd, capture_output=True, text=True, timeout=600, cwd=str(remotion_dir))
        
        if result.returncode != 0:
            logger.error(f"[Remotion v2] PNG 序列渲染失败: {result.stderr[-500:] if result.stderr else '未知错误'}")
            logger.error(f"[Remotion v2] stdout: {result.stdout[-500:] if result.stdout else '无'}")
            return None
        
        # 6. PNG 文件在 frames 子目录中
        frames_dir = png_dir / 'frames'
        if not frames_dir.exists():
            logger.error(f"[Remotion v2] PNG 目录不存在: {frames_dir}")
            return None
        
        # 7. 使用 FFmpeg 将 PNG 序列编码为带透明通道的视频
        output_path = remotion_dir / 'out' / f'caption_{video_id}.webm'
        
        # 检测实际的文件名格式
        import glob
        png_files = sorted(glob.glob(str(frames_dir / 'element-*.png')))
        if not png_files:
            logger.error(f"[Remotion v2] 没有找到 PNG 文件: {frames_dir}")
            return None
        
        # 获取文件名格式
        sample_file = Path(png_files[0]).name
        # 可能是 element-0.png 或 element-00.png
        match = re.match(r'element-(\d+)\.png', sample_file)
        if match:
            num_digits = len(match.group(1))
            pattern = f'element-%0{num_digits}d.png'
        else:
            pattern = 'element-%d.png'
        
        logger.info(f"[Remotion v2] PNG 文件格式: {pattern}, 共 {len(png_files)} 个文件")
        
        # 方案 C: 直接返回 PNG 目录路径，跳过 WebM 编码（alpha 通道在 WebM 中会丢失）
        # 之前的 WebM 编码步骤已移除，因为：
        # 1. WebM 编码非常慢（特别是带 alpha 通道）
        # 2. 最终使用的是 PNG 序列 overlay，不需要 WebM
        logger.info(f"[Remotion v2] PNG 序列渲染完成: {len(png_files)} 帧")
        logger.info(f"[Remotion v2] 返回 PNG 目录: {frames_dir}")
        # 返回格式: "PNG目录|文件名格式|fps"
        return f"{frames_dir}|{pattern}|{fps}"
            
    except Exception as e:
        logger.error(f"[Remotion v2] 渲染异常: {e}")
        import traceback
        traceback.print_exc()
        return None


def _prepare_subtitle(video_id: int, source_path: str, subtitle_source: str) -> Optional[str]:
    """准备字幕文件
    
    Args:
        video_id: 视频ID
        source_path: 源视频路径
        subtitle_source: 字幕来源 - auto/upload/whisperx
    
    Returns:
        字幕文件路径，失败返回 None
    """
    from app.services.subtitle_extractor import SubtitleExtractor
    
    subtitle_dir = Path(settings.SUBTITLES_DIR) / str(video_id)
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    
    ass_path = subtitle_dir / "subtitle.ass"
    
    # 如果明确指定使用上传的字幕
    if subtitle_source == 'upload':
        upload_path = subtitle_dir / "uploaded.srt"
        if upload_path.exists():
            # 强制从上传的 SRT 重新转换
            logger.info(f"[字幕] 从上传的 SRT 转换: {upload_path}")
            extractor = SubtitleExtractor()
            result = extractor._convert_to_ass(str(upload_path), str(ass_path))
            if result:
                return result
            else:
                logger.warning("[字幕] SRT 转换失败，尝试其他方式")
        else:
            logger.warning("[字幕] 未找到上传的字幕文件，尝试自动检测")
        subtitle_source = 'auto'
    
    # 检查是否已有有效的 ASS 字幕文件
    if ass_path.exists():
        # 验证 ASS 文件是否有有效内容
        try:
            with open(ass_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'Dialogue:' in content and len(content) > 200:
                logger.info(f"[字幕] 使用已有字幕: {ass_path}")
                return str(ass_path)
        except Exception:
            pass
    
    # 自动检测或强制 WhisperX
    extractor = SubtitleExtractor()
    if subtitle_source == 'whisperx':
        logger.info(f"[字幕] 强制使用 WhisperX 转录")
        return extractor.extract_smart(
            source_path, 
            str(subtitle_dir),
            prefer_lang='en',
            prefer_whisperx=True
        )
    else:
        return extractor.extract_smart(
            source_path, 
            str(subtitle_dir),
            prefer_lang='en'
        )


def _burn_subtitle(input_path: str, output_path: str, subtitle_path: str) -> dict:
    """
    烧录字幕到视频（使用 ASS override 标签精确控制位置）
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        subtitle_path: 字幕文件路径（ASS/SRT）
    
    Returns:
        dict: {'success': bool, 'style_index': int, 'font_size': int, 'pos_y': int}
    """
    if not os.path.exists(subtitle_path):
        logger.warning(f"字幕文件不存在: {subtitle_path}")
        return {'success': False, 'style_index': 0, 'font_size': 24, 'pos_y': 100}
    
    import random
    import re
    
    # 获取视频实际分辨率
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height', '-of', 'csv=p=0', input_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(',')
            video_width = int(parts[0])
            video_height = int(parts[1])
        else:
            video_width, video_height = 876, 1096
    except Exception:
        video_width, video_height = 876, 1096
    
    # 随机选择艺术字样式（3种风格）
    style_index = random.randint(0, 2)
    font_size = random.randint(50, 65)  # 字体大小 50~65px
    
    # 文字层位置：X轴居中，Y轴顶部向下1/4
    pos_x = video_width // 2
    pos_y = video_height // 4
    
    # 3种艺术字风格的 ASS override 参数
    style_names = ['粗描边白字', '细描边+阴影', '渐变描边']
    style_colors = [
        r'\c&HFFFFFF&\3c&H000000&',  # 白字黑边
        r'\c&HFFFFFF&\3c&H333333&',  # 白字深灰边
        r'\c&HFFFFCC&\3c&H666699&',  # 米黄字浅蓝紫边
    ]
    style_borders = [
        r'\bord3\shad1',   # 粗描边+小阴影
        r'\bord2\shad2',   # 细描边+大阴影
        r'\bord2.5\shad1.5',  # 中等描边+中阴影
    ]
    
    # 构建 override 标签：\an8\pos(x,y)\fs{size}{colors}{borders}
    override = r'{\an8\pos(' + str(pos_x) + ',' + str(pos_y) + r')\fs' + str(font_size) + style_borders[style_index] + style_colors[style_index] + '}'
    
    # 读取并修改 ASS 文件
    try:
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            ass_content = f.read()
    except Exception:
        with open(subtitle_path, 'r', encoding='latin-1') as f:
            ass_content = f.read()
    
    # 更新 PlayResX/PlayResY 为实际视频分辨率
    ass_content = re.sub(r'PlayResX: \d+', f'PlayResX: {video_width}', ass_content)
    ass_content = re.sub(r'PlayResY: \d+', f'PlayResY: {video_height}', ass_content)
    
    # 修改 Style 行：BorderStyle=1（描边模式），BackColour=透明，Outline=0，Shadow=0
    # 由 override 标签控制实际的描边和阴影效果
    new_style = f"Style: Default, Arial Black, {font_size}, &H00FFFFFF, &H000000FF, &H00000000, &H00000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 0, 0, 5, 0, 0, 0, 1"
    ass_content = re.sub(r'Style: Default,.*', new_style, ass_content)
    
    # 在每个 Dialogue 行添加 override 标签
    lines = ass_content.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith('Dialogue:'):
            parts = line.split(',', 9)
            if len(parts) >= 10:
                text = parts[9]
                # 移除已有的 override 标签（如果有）
                text = re.sub(r'\{[^}]*\}', '', text)
                parts[9] = override + text
                line = ','.join(parts)
        new_lines.append(line)
    
    modified_ass = '\n'.join(new_lines)
    
    # 保存修改后的 ASS 文件
    modified_ass_path = subtitle_path.replace('.ass', f'_modified_{style_index}.ass')
    with open(modified_ass_path, 'w', encoding='utf-8') as f:
        f.write(modified_ass)
    
    logger.info(f"[文字层] 风格: {style_names[style_index]}, 字体: {font_size}px, 位置: ({pos_x},{pos_y}), 视频分辨率: {video_width}x{video_height}")
    
    # 转义路径
    escaped_path = modified_ass_path.replace(':', '\\:').replace("'", "'\\''")
    
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', f"subtitles='{escaped_path}'",
        '-c:v', 'mpeg4', '-q:v', '12',  # v4.1.6: 字幕烧录 8→12，保持清晰
        '-threads', '2',                  # v4.1.6: 避免CPU过载
        '-c:a', 'copy',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode == 0 and os.path.exists(output_path):
            return {
                'success': True,
                'style_index': style_index,
                'font_size': font_size,
                'pos_y': pos_y,
                'style_name': style_names[style_index]
            }
        else:
            logger.error(f"字幕烧录失败: {result.stderr.decode()[:500]}")
            return {'success': False, 'style_index': style_index, 'font_size': font_size, 'pos_y': pos_y}
    except subprocess.TimeoutExpired:
        logger.error("字幕烧录超时")
        return {'success': False, 'style_index': style_index, 'font_size': font_size, 'pos_y': pos_y}
    except Exception as e:
        logger.error(f"字幕烧录异常: {e}")
        return {'success': False, 'style_index': style_index, 'font_size': font_size, 'pos_y': pos_y}


def _get_video_resolution(filepath: str) -> str:
    """获取视频分辨率"""
    if not filepath or not os.path.exists(filepath):
        return 'unknown'
    try:
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height', '-of', 'csv=p=0', filepath],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            w, h = result.stdout.strip().split(',')
            h = int(h)
            if h >= 1080:
                return '1080p'
            elif h >= 720:
                return '720p'
            elif h >= 480:
                return '480p'
            elif h >= 360:
                return '360p'
            return f'{h}p'
    except Exception as e:
        logger.error(f"获取分辨率失败: {e}")
    return 'unknown'


# ==================== 导出 ====================

__all__ = [
    '_render_remotion_subtitle_v2',
    '_prepare_subtitle',
    '_burn_subtitle',
    '_get_video_resolution'
]