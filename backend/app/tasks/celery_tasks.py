# backend/app/tasks/celery_tasks.py
"""
Celery 异步任务 - 下载视频和生成变体
支持多种下载方式：
1. Scrapling（推荐）- 绕过 Cloudflare，无需 cookies
2. yt-dlp-api 代理服务
3. 直接 yt-dlp
"""
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
from celery import Celery
from loguru import logger
import asyncio

from app.config import settings
from app.services.downloader import VideoDownloader, YtDlpApiClient
from app.services.scrapling_downloader import ScraplingDownloader, SCRAPLING_AVAILABLE
from app.services.variant_engine import VariantEngine, AudioVariantEngine

# 创建 Celery 应用
celery_app = Celery(
    'shorts_fission',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
)

# 初始化服务
downloader = VideoDownloader({
    'proxy_url': settings.PROXY_URL,
    'proxy_enabled': settings.PROXY_ENABLED,
    'videos_dir': settings.VIDEOS_DIR,
    'use_yt_dlp_api': True,  # 使用 yt-dlp-api
})

# yt-dlp-api 客户端
yt_dlp_api = YtDlpApiClient()

# Scrapling 下载器（推荐）
scrapling_downloader = None
if SCRAPLING_AVAILABLE:
    scrapling_downloader = ScraplingDownloader({
        'headless': True,
        'use_stealth': True,
        'yt_dlp_path': 'yt-dlp',
        'cookies_file': '/root/.openclaw/workspace/projects/shorts-fission/backend/cookies.txt',
    })
    logger.info("Scrapling 下载器已启用")
else:
    logger.warning("Scrapling 不可用，使用传统下载方式")

# v4.0 PIP 变体引擎
variant_engine = VariantEngine({
    'min_enhanced': 3,
    'max_enhanced': 5,
    'whisperx_enabled': False,  # 暂时禁用字幕提取，后续启用
})

audio_engine = AudioVariantEngine({
    'bgm_dir': settings.BGM_DIR,
    'bgm_volume': 0.3,
})



def _render_remotion_subtitle_v2(
    video_id: int,
    words_data: list,
    animation_template: str = 'pop_highlight',
    animation_position: str = 'bottom_center',
    fps: int = 30,
) -> Optional[str]:
    """使用 Remotion v2 渲染字幕视频（方案 A2: PNG 序列 + FFmpeg overlay）"""
    import json
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
        
        render_cmd = [
            'npx', 'remotion', 'render',
            'src/index.ts', 'Caption',
            relative_output,  # 使用相对路径
            '--frames', f'0-{duration_in_frames}',
            '--fps', str(fps),
            '--width', '1080',
            '--height', '1920',
            '--sequence',
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
        import re
        match = re.match(r'element-(\d+)\.png', sample_file)
        if match:
            num_digits = len(match.group(1))
            pattern = f'element-%0{num_digits}d.png'
        else:
            pattern = 'element-%d.png'
        
        logger.info(f"[Remotion v2] PNG 文件格式: {pattern}, 共 {len(png_files)} 个文件")
        
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-framerate', str(fps),
            '-i', str(frames_dir / pattern),
            '-c:v', 'libvpx',
            '-b:v', '2M',
            '-pix_fmt', 'yuva420p',  # 带透明通道
            '-auto-alt-ref', '0',
            str(output_path),
        ]
        
        logger.info(f"[Remotion v2] 编码 WebM (带透明通道)")
        
        ffmpeg_result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        # 方案 C: 直接返回 PNG 目录路径，跳过 WebM 编码（alpha 通道在 WebM 中会丢失）
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
        except:
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
    except:
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
    except:
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
        '-c:v', 'mpeg4', '-q:v', '8',
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


@celery_app.task(bind=True)
def download_video_task(self, video_id: int, url: str, output_dir: str):
    """下载视频任务 - 优先使用 Scrapling，回退到 yt-dlp-api"""
    import asyncio
    from app.database import async_session
    from app.models.video import Video
    from sqlalchemy import select
    
    logger.info(f"开始下载视频: {url}")
    
    # 更新状态
    self.update_state(
        state='PROGRESS',
        meta={'status': 'downloading', 'progress': 0}
    )
    
    result = None
    
    # 方案1: 使用 Scrapling（推荐，绕过 Cloudflare）
    if scrapling_downloader and scrapling_downloader.is_available():
        logger.info("使用 Scrapling 下载...")
        result = scrapling_downloader.download(
            url=url,
            output_dir=output_dir,
            no_watermark=True
        )
        if result.get('success'):
            result['resolution'] = _get_video_resolution(result.get('filepath'))
        else:
            logger.warning(f"Scrapling 下载失败: {result.get('error')}，尝试 yt-dlp-api...")
            result = None
    
    # 方案2: 回退到 yt-dlp-api
    if not result or not result.get('success'):
        logger.info("使用 yt-dlp-api 下载...")
        result = yt_dlp_api.download_video_sync(url, output_dir, "720p")
    
    # 更新数据库状态
    async def update_status():
        async with async_session() as session:
            stmt = select(Video).where(Video.id == video_id)
            result_db = await session.execute(stmt)
            video = result_db.scalar_one_or_none()
            
            if video:
                if result['success']:
                    video.status = 'downloaded'
                    video.video_id = result.get('video_id')
                    video.title = result.get('title')
                    video.duration = result.get('duration', 0)
                    video.thumbnail = result.get('thumbnail')
                    video.source_path = result.get('file_path')
                    video.resolution = result.get('resolution')
                    video.download_progress = 100
                    from datetime import datetime
                    video.downloaded_at = datetime.now()
                    logger.info(f"视频 {video_id} 下载完成，分辨率: {result.get('resolution')}")
                else:
                    video.status = 'failed'
                    video.error_message = result.get('error')
                    logger.error(f"视频 {video_id} 下载失败: {result.get('error')}")
                
                await session.commit()
    
    # 运行异步更新
    try:
        asyncio.run(update_status())
    except Exception as e:
        logger.error(f"更新数据库状态失败: {e}")
    
    if result['success']:
        return {
            'status': 'completed',
            'video_id': video_id,
            'file_path': result.get('file_path'),
            'title': result.get('title'),
            'duration': result.get('duration'),
            'resolution': result.get('resolution'),
        }
    else:
        raise Exception(result.get('error'))


@celery_app.task(bind=True)
def generate_variants_task(
    self, 
    video_id: int, 
    source_path: str, 
    count: int = 15, 
    start_index: int = 1,
    enable_subtitle: bool = False,
    subtitle_source: str = "auto",
    animation_template: str = None,
    animation_position: str = 'bottom_center',
):
    """生成视频变体任务 - 支持 Animated Caption
    
    Args:
        video_id: 视频ID
        source_path: 源视频路径
        count: 要生成的变体数量
        start_index: 起始变体索引（用于累加模式）
        enable_subtitle: 是否启用文字层（字幕烧录）
        subtitle_source: 字幕来源 - auto/upload/whisperx
        animation_template: 动画模板 (pop_highlight/karaoke_flow/hype_gaming)
        animation_position: 字幕位置
    """
    logger.info(f"开始生成变体: {video_id}, 数量: {count}, 字幕: {enable_subtitle}, 模板: {animation_template}")
    
    # 创建变体引擎实例
    engine = VariantEngine({
        'min_enhanced': 3,
        'max_enhanced': 5,
        'whisperx_enabled': enable_subtitle and subtitle_source == 'whisperx',
        'enable_subtitle': enable_subtitle,
        'subtitle_source': subtitle_source,
    })
    
    # 如果启用字幕，先提取字幕（只处理一次）
    subtitle_path = None
    subtitle_video_path = None
    
    if enable_subtitle:
        if animation_template:
            # 使用 Animated Caption (Remotion v2)
            from app.services.subtitle_extractor import extract_word_timestamps
            
            # 提取词级时间戳
            words_data = extract_word_timestamps(source_path, None)
            
            if words_data:
                # 使用 Remotion v2 渲染
                subtitle_video_path = _render_remotion_subtitle_v2(
                    video_id=video_id,
                    words_data=words_data,
                    animation_template=animation_template or 'pop_highlight',
                    animation_position=animation_position,
                )
                
                if subtitle_video_path:
                    logger.info(f"[Animated Caption] 渲染完成: {subtitle_video_path}")
                else:
                    logger.warning("[Animated Caption] 渲染失败，回退到普通字幕")
                    subtitle_path = _prepare_subtitle(video_id, source_path, subtitle_source)
            else:
                logger.warning("[Animated Caption] 词级时间戳提取失败")
                subtitle_path = _prepare_subtitle(video_id, source_path, subtitle_source)
        else:
            # 使用普通字幕
            subtitle_path = _prepare_subtitle(video_id, source_path, subtitle_source)
        
        if subtitle_path:
            logger.info(f"字幕准备完成: {subtitle_path}")
    
    # 创建输出目录
    output_dir = Path(settings.VARIANTS_DIR) / str(video_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for i in range(1, count + 1):
        # 更新进度
        progress = int((i / count) * 100)
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'processing',
                'current': i,
                'total': count,
                'progress': progress,
            }
        )
        
        actual_index = start_index + i - 1  # 计算实际索引
        output_path = str(output_dir / f"variant_{actual_index:03d}.mp4")
        
        # 生成视觉变体（使用带 fg_mode 配置的引擎）
        visual_result = engine.generate_variant(
            source_path,
            output_path,
            seed=video_id * 1000 + actual_index  # 使用实际索引作为种子
        )
        
        if visual_result['success']:
            # 中间文件路径
            intermediate_path = output_path
            
            # 如果有字幕，叠加字幕
            subtitle_result = None
            if subtitle_video_path:
                # 检查是 PNG 序列还是 WebM 文件
                # PNG 序列格式: "目录路径|文件名格式|fps"
                if '|' in subtitle_video_path:
                    # PNG 序列模式
                    parts = subtitle_video_path.split('|')
                    png_dir = parts[0]
                    png_pattern = parts[1] if len(parts) > 1 else 'element-%d.png'
                    png_fps = int(parts[2]) if len(parts) > 2 else 30
                    
                    subtitle_burned_path = str(output_dir / f"subtitle_{actual_index:03d}.mp4")
                    
                    # 直接用 PNG 序列 overlay
                    # PNG 序列时长可能 > 视频时长，需要在视频结束时停止 overlay
                    overlay_cmd = [
                        'ffmpeg', '-y',
                        '-i', intermediate_path,
                        '-framerate', str(png_fps),
                        '-i', f"{png_dir}/{png_pattern}",
                        '-filter_complex', 
                        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];[bg][1:v]overlay=0:0:eof_action=pass[out]",
                        '-map', '[out]',
                        '-map', '0:a?',
                        '-c:v', 'mpeg4',
                        '-q:v', '5',
                        '-c:a', 'aac',
                        '-b:a', '128k',
                        '-shortest',
                        subtitle_burned_path,
                    ]
                    
                    overlay_result = subprocess.run(overlay_cmd, capture_output=True, text=True)
                    
                    if overlay_result.returncode == 0 and os.path.exists(subtitle_burned_path):
                        intermediate_path = subtitle_burned_path
                        subtitle_result = {'success': True}
                        logger.info(f"[视频{video_id}] 变体 {actual_index} PNG overlay 完成（透明背景）")
                    else:
                        logger.warning(f"[视频{video_id}] 变体 {actual_index} PNG overlay 失败: {overlay_result.stderr[-300:] if overlay_result.stderr else '未知'}")
                        
                elif os.path.exists(subtitle_video_path):
                    # WebM 文件模式
                    subtitle_burned_path = str(output_dir / f"subtitle_{actual_index:03d}.mp4")
                    
                    overlay_cmd = [
                        'ffmpeg', '-y',
                        '-i', intermediate_path,
                        '-i', subtitle_video_path,
                        '-filter_complex', 
                        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[main];[0:v]scale=1080:1920:force_original_aspect_ratio=increase,gblur=sigma=50[blur];[blur][main]overlay=(W-w)/2:(H-h)/2[bg];[bg][1:v]overlay=0:0[out]",
                        '-map', '[out]',
                        '-map', '0:a?',
                        '-c:v', 'mpeg4',
                        '-q:v', '5',
                        '-c:a', 'aac',
                        '-b:a', '128k',
                        subtitle_burned_path,
                    ]
                    
                    overlay_result = subprocess.run(overlay_cmd, capture_output=True, text=True)
                    
                    if overlay_result.returncode == 0 and os.path.exists(subtitle_burned_path):
                        intermediate_path = subtitle_burned_path
                        subtitle_result = {'success': True}
                        logger.info(f"[视频{video_id}] 变体 {actual_index} WebM overlay 完成（透明背景）")
                    else:
                        logger.warning(f"[视频{video_id}] 变体 {actual_index} overlay 失败: {overlay_result.stderr[-300:] if overlay_result.stderr else '未知'}")
                    
            elif subtitle_path and os.path.exists(subtitle_path):
                # 回退：使用 ASS 烧录
                subtitle_burned_path = str(output_dir / f"subtitle_{actual_index:03d}.mp4")
                subtitle_result = _burn_subtitle(intermediate_path, subtitle_burned_path, subtitle_path)
                if subtitle_result.get('success'):
                    intermediate_path = subtitle_burned_path
                    logger.info(f"[视频{video_id}] 变体 {actual_index} ASS 字幕烧录完成")
                else:
                    logger.warning(f"[视频{video_id}] 变体 {actual_index} 字幕烧录失败，使用原视频")
            
            # 生成音频变体 (BGM 替换)
            final_path = str(output_dir / f"final_{actual_index:03d}.mp4")
            audio_result = audio_engine.replace_bgm(
                intermediate_path,
                final_path,
                sport_type='default'  # TODO: 根据视频内容识别球类
            )
            
            # 构建易读的效果描述（v4.0 PIP 模式 - 三层结构）
            params = visual_result.get('params', {})
            
            # 背景层参数
            bg_layer = []
            bg_layer.append(f"全景模糊σ={params.get('bg_blur', 70):.0f}")
            bg_layer.append(f"放大{params.get('bg_scale', 1.75)*100:.0f}%")
            bg_layer.append(f"变速{params.get('speed', 1.1):.2f}x")
            if params.get('mirror'):
                bg_layer.append('镜像翻转')
            if params.get('rotation'):
                bg_layer.append(f"旋转{params['rotation']:.1f}°")
            if params.get('crop_ratio'):
                bg_layer.append(f"裁剪{params['crop_ratio']*100:.0f}%")
            # 增强特效
            enhanced = params.get('enhance_effects', [])
            effect_names = {
                'saturation': '饱和度',
                'brightness': '亮度',
                'contrast': '对比度',
                'rgb_shift': 'RGB偏移',
                'darken': '暗化',
                'color_temp': '色调',
                'frame_swap': '帧交换',
            }
            for e in enhanced:
                name = effect_names.get(e, e)
                if name not in bg_layer:
                    bg_layer.append(name)
            
            # 中间层参数
            mid_layer = []
            mid_layer.append(f"缩放{params.get('fg_scale', 1.0)*100:.0f}%")
            crop_top = params.get('fg_crop_top', 0)
            crop_bottom = params.get('fg_crop_bottom', 0)
            if crop_top or crop_bottom:
                mid_layer.append(f"裁剪上{crop_top*100:.0f}%+下{crop_bottom*100:.0f}%")
            if params.get('has_border'):
                border_color_map = {'white': '白', 'yellow': '黄', 'lightblue': '浅蓝', 'lavender': '浅紫'}
                color_name = border_color_map.get(params.get('border_color', 'white'), '白')
                mid_layer.append(f"边框:{color_name}({params.get('border_width', 0)}px)")
            
            # 文字层参数（使用实际烧录的参数）
            text_layer = []
            if subtitle_result and subtitle_result.get('success'):
                # 使用烧录时的实际参数
                style_names = ['粗描边白字', '细描边+阴影', '渐变描边']
                style_idx = subtitle_result.get('style_index', 0)
                font_size = subtitle_result.get('font_size', 24)
                pos_y = subtitle_result.get('pos_y', 365)
                
                text_layer.append(f"字体{font_size}px")
                text_layer.append(f"艺术字-{style_names[style_idx]}")
                text_layer.append(f"位置Y:{pos_y}px")
                logger.info(f"[文字层] 字体: {font_size}px, 风格: {style_names[style_idx]}, 位置Y: {pos_y}px")
            elif subtitle_path and os.path.exists(subtitle_path):
                # 字幕文件存在但烧录失败
                text_layer.append('文字层生成失败')
            else:
                text_layer.append('无文字层')
            
            # 组合成 JSON 格式存储
            effects_json = {
                'bg_layer': bg_layer,
                'mid_layer': mid_layer,
                'text_layer': text_layer
            }
            
            # 同时保留易读的文本格式（用于简单显示）
            effects_desc = ['[背景层]'] + bg_layer + ['[中间层]'] + mid_layer + ['[文字层]'] + text_layer
            
            results.append({
                'index': actual_index,  # 使用实际索引，而不是循环变量 i
                'status': 'completed',
                'effects': effects_desc,
                'file_path': final_path if audio_result['success'] else output_path,
            })
            
            logger.info(f"变体 {i}/{count} 生成完成")
        else:
            results.append({
                'index': actual_index,  # 使用实际索引
                'status': 'failed',
                'error': visual_result.get('error', '视觉变体生成失败'),
            })
    
    logger.info(f"变体生成完成: {len([r for r in results if r['status'] == 'completed'])}/{count}")
    
    # 更新数据库状态
    completed_count = len([r for r in results if r['status'] == 'completed'])
    try:
        import sqlite3
        from datetime import datetime
        
        db_path = Path(settings.DATA_DIR) / 'shorts_fission.db'
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 更新视频状态 - 累加 variant_count
        c.execute("""
            UPDATE videos 
            SET status = ?, 
                variant_count = variant_count + ?, 
                variant_progress = 100,
                completed_at = ?
            WHERE id = ?
        """, (
            'COMPLETED' if completed_count == count else 'FAILED',
            completed_count,
            datetime.now().isoformat(),
            video_id
        ))
        
        # 添加变体记录
        for r in results:
            if r['status'] == 'completed' and r.get('file_path'):
                effects_str = ' · '.join(r.get('effects', []))
                c.execute("""
                    INSERT INTO variants (video_id, variant_index, status, file_path, effects_applied, completed_at)
                    VALUES (?, ?, 'COMPLETED', ?, ?, ?)
                """, (
                    video_id,
                    r['index'],
                    r['file_path'],
                    effects_str,
                    datetime.now().isoformat()
                ))
        
        conn.commit()
        conn.close()
        logger.info(f"数据库更新完成: 视频 {video_id}, 变体 {completed_count}/{count}")
        
    except Exception as e:
        logger.error(f"更新数据库失败: {e}")
    
    return {
        'status': 'completed',
        'video_id': video_id,
        'total': count,
        'results': results,
    }


@celery_app.task(bind=True)
def batch_download_task(self, account_url: str, output_dir: str, start_date: str = None, end_date: str = None):
    """批量下载任务"""
    logger.info(f"开始批量下载: {account_url}")
    
    result = downloader.batch_download(
        account_url,
        output_dir,
        start_date,
        end_date,
        max_count=50
    )
    
    return result
