# backend/app/tasks/celery_tasks.py
"""
Celery 异步任务 - 下载视频和生成变体
支持多种下载方式：
1. Scrapling（推荐）- 绕过 Cloudflare，无需 cookies
2. yt-dlp-api 代理服务
3. 直接 yt-dlp

优化：
- 模型预热：Worker 启动时预先加载 WhisperX 模型
- 并行生成：使用 ThreadPoolExecutor 并行生成变体
"""
import os
import subprocess
import threading
from pathlib import Path
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from celery import Celery, signals
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


# ==================== 模型预热 ====================

@signals.worker_process_init.connect
def warmup_models(**kwargs):
    """
    Worker 进程初始化时预热模型
    
    解决 WhisperX 模型每次请求都重新加载的问题
    预热后，首次处理视频时不需要等待模型加载
    """
    logger.info("[Worker] 开始预热模型...")
    
    try:
        from app.services.model_warmup import warmup_whisperx
        
        # 预热 WhisperX 模型
        success = warmup_whisperx(model_size="base")
        
        if success:
            logger.info("[Worker] 模型预热完成 ✅")
        else:
            logger.warning("[Worker] 模型预热失败，将在首次使用时加载")
    
    except Exception as e:
        logger.warning(f"[Worker] 模型预热异常: {e}")


# ==================== 初始化服务 ====================

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
        import re
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


# ==================== 并行生成辅助函数 ====================

# 进度追踪锁（线程安全）
_progress_lock = threading.Lock()
_completed_count = 0

def _generate_single_variant(
    variant_index: int,
    source_path: str,
    output_dir: Path,
    subtitle_video_path: Optional[str],
    subtitle_path: Optional[str],
    engine: VariantEngine,
    audio_engine: AudioVariantEngine,
    video_id: int,
    total_count: int,
    progress_callback
) -> Dict:
    """
    生成单个变体（线程安全）
    
    Args:
        variant_index: 变体索引
        source_path: 源视频路径
        output_dir: 输出目录
        subtitle_video_path: 字幕视频路径（PNG 序列或 WebM）
        subtitle_path: 字幕文件路径（ASS）
        engine: 变体引擎
        audio_engine: 音频引擎
        video_id: 视频 ID
        total_count: 总变体数量
        progress_callback: 进度回调函数
    
    Returns:
        变体生成结果
    """
    global _completed_count
    
    try:
        output_path = str(output_dir / f"variant_{variant_index:03d}.mp4")
        
        # 1. 生成 PIP 变体
        visual_result = engine.generate_variant(
            source_path,
            output_path,
            seed=video_id * 1000 + variant_index
        )
        
        if not visual_result['success']:
            return {
                'index': variant_index,
                'status': 'failed',
                'error': visual_result.get('error', 'PIP 生成失败')
            }
        
        intermediate_path = output_path
        subtitle_result = None
        
        # 2. 叠加字幕
        if subtitle_video_path:
            if '|' in subtitle_video_path:
                # PNG 序列模式
                parts = subtitle_video_path.split('|')
                png_dir = parts[0]
                png_pattern = parts[1] if len(parts) > 1 else 'element-%d.png'
                png_fps = int(parts[2]) if len(parts) > 2 else 30
                
                subtitle_burned_path = str(output_dir / f"subtitle_{variant_index:03d}.mp4")
                
                overlay_cmd = [
                    'ffmpeg', '-y',
                    '-threads', '2',  # v4.1.6: 4核CPU + 4变体并行，每任务2线程
                    '-i', intermediate_path,
                    '-framerate', str(png_fps),
                    '-i', f"{png_dir}/{png_pattern}",
                    '-filter_complex', 
                    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];[bg][1:v]overlay=0:0:eof_action=pass[out]",
                    '-map', '[out]',
                    '-map', '0:a?',
                    '-c:v', 'mpeg4',
                    '-q:v', '10',  # v4.1.6: PNG overlay最终输出，质量最高 5→10
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-shortest',
                    subtitle_burned_path,
                ]
                
                overlay_result = subprocess.run(overlay_cmd, capture_output=True, text=True)
                
                if overlay_result.returncode == 0 and os.path.exists(subtitle_burned_path):
                    intermediate_path = subtitle_burned_path
                    subtitle_result = {'success': True}
                    logger.info(f"[视频{video_id}] 变体 {variant_index} PNG overlay 完成")
                else:
                    logger.warning(f"[视频{video_id}] 变体 {variant_index} PNG overlay 失败")
                    
            elif os.path.exists(subtitle_video_path):
                # WebM 文件模式
                subtitle_burned_path = str(output_dir / f"subtitle_{variant_index:03d}.mp4")
                
                overlay_cmd = [
                    'ffmpeg', '-y',
                    '-threads', '2',  # v4.1.6: 避免CPU过载
                    '-i', intermediate_path,
                    '-i', subtitle_video_path,
                    '-filter_complex', 
                    "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[main];[0:v]scale=1080:1920:force_original_aspect_ratio=increase,gblur=sigma=50[blur];[blur][main]overlay=(W-w)/2:(H-h)/2[bg];[bg][1:v]overlay=0:0[out]",
                    '-map', '[out]',
                    '-map', '0:a?',
                    '-c:v', 'mpeg4',
                    '-q:v', '10',  # v4.1.6: WebM overlay，与PNG一致
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    subtitle_burned_path,
                ]
                
                overlay_result = subprocess.run(overlay_cmd, capture_output=True, text=True)
                
                if overlay_result.returncode == 0 and os.path.exists(subtitle_burned_path):
                    intermediate_path = subtitle_burned_path
                    subtitle_result = {'success': True}
                    logger.info(f"[视频{video_id}] 变体 {variant_index} WebM overlay 完成")
                    
        elif subtitle_path and os.path.exists(subtitle_path):
            # ASS 烧录
            subtitle_burned_path = str(output_dir / f"subtitle_{variant_index:03d}.mp4")
            subtitle_result = _burn_subtitle(intermediate_path, subtitle_burned_path, subtitle_path)
            if subtitle_result.get('success'):
                intermediate_path = subtitle_burned_path
                logger.info(f"[视频{video_id}] 变体 {variant_index} ASS 字幕烧录完成")
        
        # 3. BGM 替换
        final_path = str(output_dir / f"final_{variant_index:03d}.mp4")
        audio_result = audio_engine.replace_bgm(
            intermediate_path,
            final_path,
            sport_type='default'
        )
        
        # 4. 构建效果描述
        params = visual_result.get('params', {})
        
        bg_layer = []
        bg_layer.append(f"全景模糊σ={params.get('bg_blur', 70):.0f}")
        bg_layer.append(f"放大{params.get('bg_scale', 1.75)*100:.0f}%")
        bg_layer.append(f"变速{params.get('speed', 1.1):.2f}x")
        
        mid_layer = []
        mid_layer.append(f"缩放{params.get('fg_scale', 1.0)*100:.0f}%")
        
        text_layer = []
        if subtitle_result and subtitle_result.get('success'):
            text_layer.append(f"字体24px")
            text_layer.append("词级动画")
        elif subtitle_path and os.path.exists(subtitle_path):
            text_layer.append('字幕烧录')
        else:
            text_layer.append('无文字层')
        
        effects_desc = ['[背景层]'] + bg_layer + ['[中间层]'] + mid_layer + ['[文字层]'] + text_layer
        
        # 5. 更新进度（线程安全）- 实时更新数据库
        with _progress_lock:
            _completed_count += 1
            progress = int((_completed_count / total_count) * 100)
            
            # 实时更新数据库进度
            try:
                import sqlite3
                db_path = Path(settings.DATA_DIR) / 'shorts_fission.db'
                conn = sqlite3.connect(str(db_path))
                c = conn.cursor()
                # 变体生成阶段进度：30% - 100%
                # 计算公式：30 + (完成数/总数) * 70
                stage_progress = 30 + int((_completed_count / total_count) * 70)
                c.execute("""
                    UPDATE videos 
                    SET variant_count = ?, variant_progress = ?
                    WHERE id = ?
                """, (_completed_count, stage_progress, video_id))
                conn.commit()
                conn.close()
            except Exception as db_err:
                logger.warning(f"[进度更新] 数据库更新失败: {db_err}")
            
            if progress_callback:
                progress_callback(stage_progress, _completed_count, total_count)
        
        logger.info(f"变体 {variant_index} 生成完成 ({_completed_count}/{total_count})")
        
        return {
            'index': variant_index,
            'status': 'completed',
            'effects': effects_desc,
            'file_path': final_path if audio_result['success'] else output_path,
        }
    
    except Exception as e:
        logger.error(f"变体 {variant_index} 生成异常: {e}")
        return {
            'index': variant_index,
            'status': 'failed',
            'error': str(e)
        }


# ==================== 主任务 ====================

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
    placeholder_subtitle_enabled: bool = True,  # 占位字幕开关
    target_language: str = 'auto',  # 目标语言 ('auto', 'en', 'zh')
):
    """生成视频变体任务 - 支持 Animated Caption + 并行生成 + 翻译
    
    Args:
        video_id: 视频ID
        source_path: 源视频路径
        count: 要生成的变体数量
        start_index: 起始变体索引（用于累加模式）
        enable_subtitle: 是否启用文字层（字幕烧录）
        subtitle_source: 字幕来源 - auto/upload/whisperx
        animation_template: 动画模板 (pop_highlight/karaoke_flow/hype_gaming)
        animation_position: 字幕位置
        placeholder_subtitle_enabled: 占位字幕开关
        target_language: 目标语言 ('auto'不翻译, 'en'英文, 'zh'中文)
    """
    global _completed_count
    _completed_count = 0  # 重置计数器
    
    logger.info(f"开始生成变体: {video_id}, 数量: {count}, 字幕: {enable_subtitle}, 模板: {animation_template}, 目标语言: {target_language}")
    
    # 辅助函数：更新阶段进度
    def update_stage_progress(stage: str, progress: int):
        """更新阶段进度到数据库"""
        try:
            import sqlite3
            db_path = Path(settings.DATA_DIR) / 'shorts_fission.db'
            conn = sqlite3.connect(str(db_path))
            c = conn.cursor()
            c.execute("UPDATE videos SET variant_progress = ? WHERE id = ?", (progress, video_id))
            conn.commit()
            conn.close()
            logger.info(f"[阶段进度] {stage}: {progress}%")
        except Exception as e:
            logger.warning(f"[阶段进度] 更新失败: {e}")
    
    # 创建变体引擎实例
    engine = VariantEngine({
        'min_enhanced': 3,
        'max_enhanced': 5,
        'whisperx_enabled': enable_subtitle and subtitle_source == 'whisperx',
        'enable_subtitle': enable_subtitle,
        'subtitle_source': subtitle_source,
        'placeholder_subtitle_enabled': placeholder_subtitle_enabled,  # 占位字幕开关
    })
    
    # 如果启用字幕，先提取字幕（只处理一次）
    subtitle_path = None
    subtitle_video_path = None
    
    if enable_subtitle:
        if animation_template:
            # 阶段 1: 字幕提取 (0% - 10%)
            update_stage_progress("字幕提取", 5)
            
            # 使用 Animated Caption (Remotion v2)
            from app.services.subtitle_extractor import extract_word_timestamps
            
            # 提取词级时间戳
            words_data = extract_word_timestamps(source_path, None)
            
            # 检查词数是否足够（少于 5 个词时使用占位字幕）
            min_words_threshold = 5
            if words_data and len(words_data) >= min_words_threshold:
                # 阶段 1.5: 字幕翻译 (如果需要)
                if target_language != 'auto':
                    update_stage_progress("字幕翻译", 8)
                    logger.info(f"[翻译] 开始翻译字幕到 {target_language}...")
                    
                    try:
                        import asyncio
                        from app.services.translator import translate_subtitle
                        words_data = asyncio.get_event_loop().run_until_complete(
                            translate_subtitle(words_data, target_language=target_language)
                        )
                        logger.info(f"[翻译] 翻译完成，共 {len(words_data)} 个词")
                    except Exception as e:
                        logger.warning(f"[翻译] 翻译失败，使用原文: {e}")
                
                # 阶段 2: Remotion 渲染 (10% - 30%)
                update_stage_progress("Remotion 渲染", 15)
                
                # 使用 Remotion v2 渲染
                subtitle_video_path = _render_remotion_subtitle_v2(
                    video_id=video_id,
                    words_data=words_data,
                    animation_template=animation_template or 'pop_highlight',
                    animation_position=animation_position,
                )
                
                if subtitle_video_path:
                    # Remotion 渲染完成，更新进度到 30%
                    update_stage_progress("Remotion 渲染完成", 30)
                    logger.info(f"[Animated Caption] 渲染完成: {subtitle_video_path}")
                else:
                    logger.warning("[Animated Caption] 渲染失败，回退到普通字幕")
                    subtitle_path = _prepare_subtitle(video_id, source_path, subtitle_source)
            else:
                # 词数不足或提取失败，检查是否启用占位字幕
                word_count = len(words_data) if words_data else 0
                reason = "词级时间戳提取失败" if not words_data else f"词数过少({word_count}个 < {min_words_threshold})"
                logger.info(f"[Animated Caption] {reason}，检查占位字幕...")
                
                if placeholder_subtitle_enabled:
                    # 生成占位字幕
                    logger.info(f"[占位字幕] 开始生成占位字幕...")
                    # VariantEngine 已在文件顶部导入
                    
                    # 获取视频时长
                    import subprocess
                    import json as json_module
                    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', source_path]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    video_info = json_module.loads(result.stdout)
                    duration = float(video_info.get('format', {}).get('duration', 0))
                    
                    if duration > 3:
                        # 生成占位字幕词级数据
                        import random
                        templates = [
                            {
                                'text': "Don't Miss Next Game👀   ⚽🏀🏈⚾🏒Sports Highlights & Live HD   🔥 Link in My Bio🔥",
                                'duration': 5.0,  # 方案1: 5秒
                                'words': ["Don't", "Miss", "Next", "Game👀", "⚽🏀🏈⚾🏒Sports", "Highlights", "&", "Live", "HD", "🔥", "Link", "in", "My", "Bio🔥"]
                            },
                            {
                                'text': "Watch HD LIVE → 🔥Link in My Bio🔥",
                                'duration': 4.0,  # 方案2: 4秒
                                'words': ["Watch", "HD", "LIVE", "→", "🔥Link", "in", "My", "Bio🔥"]
                            }
                        ]
                        template = random.choice(templates)
                        logger.info(f"[占位字幕] 选择模板: 方案{templates.index(template) + 1}, 视频时长: {duration}s")
                        
                        # 生成占位词级数据
                        placeholder_words = []
                        start_time = 3.0
                        interval = 5.0  # 字幕显示之间的间隔（从上一条结尾开始计算）
                        
                        while start_time < duration:
                            end_time = min(start_time + template['duration'], duration)
                            word_count_in_segment = len(template['words'])
                            word_duration = (end_time - start_time) / word_count_in_segment
                            
                            for i, word in enumerate(template['words']):
                                word_start = start_time + i * word_duration
                                word_end = word_start + word_duration
                                placeholder_words.append({
                                    'word': word,
                                    'start': round(word_start, 3),
                                    'end': round(word_end, 3),
                                })
                            
                            # 从上一条字幕的结尾 + 间隔 开始计算下一条
                            start_time = end_time + interval
                        
                        if placeholder_words:
                            logger.info(f"[占位字幕] 生成 {len(placeholder_words)} 个词")
                            
                            # 使用 Remotion 渲染占位字幕
                            selected_template = animation_template or random.choice(['minimalist', 'default', 'classic', 'neo_minimal', 'hype', 'explosive', 'fast', 'vibrant', 'word_focus', 'line_focus', 'retro_gaming', 'model'])
                            logger.info(f"[占位字幕] 使用动画模板: {selected_template}")
                            
                            subtitle_video_path = _render_remotion_subtitle_v2(
                                video_id=video_id,
                                words_data=placeholder_words,
                                animation_template=selected_template,
                                animation_position='top_center',  # 固定在顶部
                            )
                            
                            if subtitle_video_path:
                                update_stage_progress("占位字幕渲染完成", 30)
                                logger.info(f"[占位字幕] 渲染完成: {subtitle_video_path}")
                            else:
                                logger.warning("[占位字幕] 渲染失败")
                        else:
                            logger.warning("[占位字幕] 未生成任何词级数据")
                    else:
                        logger.warning(f"[占位字幕] 视频时长 {duration}s 太短，跳过")
                else:
                    logger.info("[占位字幕] 未启用，跳过")
        else:
            # 使用普通字幕
            subtitle_path = _prepare_subtitle(video_id, source_path, subtitle_source)
        
        if subtitle_path:
            logger.info(f"字幕准备完成: {subtitle_path}")
    
    # 创建输出目录
    output_dir = Path(settings.VARIANTS_DIR) / str(video_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== 并行生成变体 ====================
    
    # 更新阶段进度：开始变体生成 (30%)
    update_stage_progress("开始变体生成", 30)
    
    # 进度回调函数（简化版，只记录日志，不调用 update_state）
    # 注意：在线程中调用 self.update_state() 会导致错误
    # 进度追踪通过全局变量 _completed_count 实现
    def update_progress(progress: int, current: int, total: int):
        logger.info(f"[并行生成] 进度: {progress}% ({current}/{total})")
    
    # 计算并行度（最多 4 个并行）
    max_workers = min(count, 4)
    logger.info(f"[并行生成] 启动 {max_workers} 个并行线程，生成 {count} 个变体")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {
            executor.submit(
                _generate_single_variant,
                start_index + i - 1,  # actual_index
                source_path,
                output_dir,
                subtitle_video_path,
                subtitle_path,
                engine,
                audio_engine,
                video_id,
                count,
                update_progress
            ): i
            for i in range(1, count + 1)
        }
        
        # 收集结果
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                i = futures[future]
                logger.error(f"变体 {i} 执行异常: {e}")
                results.append({
                    'index': start_index + i - 1,
                    'status': 'failed',
                    'error': str(e)
                })
    
    # 按索引排序结果
    results.sort(key=lambda x: x['index'])
    
    # ==================== 后处理 ====================
    
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
                variant_count = ?, 
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
    
    # ==================== 缓存清理 ====================
    
    try:
        from app.hooks.cache_cleanup import cleanup_after_variant
        # 清理当前视频的 PNG 序列
        cleanup_after_variant(video_id, variant_id=None)
        logger.info(f"[缓存清理] 视频 #{video_id} 的 PNG 序列已清理")
    except Exception as cache_err:
        logger.warning(f"[缓存清理] 清理失败: {cache_err}")
    
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
