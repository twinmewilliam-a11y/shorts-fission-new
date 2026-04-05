"""
视频变体生成任务模块

包含：
- generate_variants_task：主变体生成任务
- _generate_single_variant：单个变体生成函数（线程安全）
- 并行生成逻辑与进度管理

从此模块导入：
    - generate_variants_task
    - _generate_single_variant
"""
import os
import subprocess
import threading
from pathlib import Path
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from app.tasks.celery_app import celery_app, variant_engine, audio_engine, _progress_lock, _completed_count
from app.services.variant_engine import VariantEngine, AudioVariantEngine
from app.config import settings


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
    progress_callback,
    # 词级动画字幕参数
    animation_template: str = None,
    animation_position: str = 'bottom_center',
    used_placeholder: bool = False,
    target_language: str = 'auto',
    used_translation: bool = False,
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
        animation_template: 动画模板名称
        animation_position: 字幕位置
        used_placeholder: 是否使用了占位字幕
        target_language: 目标语言
        used_translation: 是否使用了翻译
    
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
        
        # 背景层 - 完整参数
        bg_layer = []
        bg_layer.append(f"🔮 模糊σ={params.get('bg_blur', 70):.0f}")
        bg_layer.append(f"🔍 放大{params.get('bg_scale', 1.75)*100:.0f}%")
        bg_layer.append(f"⏩ 变速{params.get('speed', 1.1):.2f}x")
        # 镜像翻转
        if params.get('mirror', False):
            bg_layer.append("🪞 镜像 ✓")
        # 旋转
        rotation = params.get('rotation', 0)
        if abs(rotation) > 0.1:
            bg_layer.append(f"🔄 旋转{rotation:.1f}°")
        
        # 中间层 - 完整参数
        mid_layer = []
        mid_layer.append(f"📐 缩放{params.get('fg_scale', 1.0)*100:.0f}%")
        # 裁剪
        crop_ratio = params.get('crop_ratio', 0.1)
        if crop_ratio > 0:
            mid_layer.append(f"✂️ 裁剪{crop_ratio*100:.0f}%")
        # 增强特效
        enhance_effects = params.get('enhance_effects', [])
        if enhance_effects:
            effect_names = {
                'saturation': '饱和',
                'brightness': '亮度',
                'contrast': '对比度',
                'rgb_shift': 'RGB偏移',
                'darken': '暗化',
                'color_temp': '色调',
                'frame_swap': '帧交换',
            }
            effect_str = ' + '.join([effect_names.get(e, e) for e in enhance_effects[:3]])
            mid_layer.append(f"✨ {effect_str}")
        
        # 文字层 - 新格式
        text_layer = []
        if subtitle_result and subtitle_result.get('success'):
            # 模板名称（转换为中文）
            template_map = {
                'pop_highlight': '高亮弹出',
                'karaoke_flow': '卡拉OK',
                'hype_gaming': '游戏炫酷',
                'minimalist': '极简',
                'default': '随机',
                'classic': '经典',
                'neo_minimal': '新极简',
                'hype': '炫酷',
                'explosive': '爆炸',
                'fast': '快节奏',
                'vibrant': '活力',
                'word_focus': '词焦点',
                'line_focus': '行焦点',
                'retro_gaming': '复古游戏',
                'model': '模特',
                'pop_highlight': '高亮弹出',
            }
            template_name = template_map.get(animation_template, animation_template or '随机')
            text_layer.append(f"🎨 {template_name}")
            
            # 位置（转换为中文）
            position_map = {
                'top_center': '📍 顶部居中',
                'bottom_center': '📍 底部居中',
                'center': '📍 屏幕中央',
            }
            position_name = position_map.get(animation_position, f"📍 {animation_position}")
            text_layer.append(position_name)
            
            # 占位字幕标记
            if used_placeholder:
                text_layer.append('🎬 占位字幕 ✓')
            
            # 翻译标记
            if used_translation and target_language and target_language != 'auto':
                lang_map = {'en': '🌐 翻译(英文) ✓', 'zh': '🌐 翻译(中文) ✓', 'ja': '🌐 翻译(日文) ✓', 'ko': '🌐 翻译(韩文) ✓'}
                lang_name = lang_map.get(target_language, f"🌐 翻译({target_language}) ✓")
                text_layer.append(lang_name)
            
        elif subtitle_path and os.path.exists(subtitle_path):
            text_layer.append('📝 字幕烧录')
        else:
            text_layer.append('🚫 无文字层')
        
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
    
    # 跟踪字幕处理状态（用于变体参数显示）
    used_placeholder = False  # 是否使用了占位字幕
    used_translation = False  # 是否使用了翻译
    
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
                        # 标记使用了翻译
                        used_translation = True
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
                            
                            # 标记使用了占位字幕
                            used_placeholder = True
                            
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
                update_progress,
                # 词级动画字幕参数
                animation_template,
                animation_position,
                used_placeholder,
                target_language,
                used_translation,
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


# ==================== 字幕工具函数（需要从 subtitle_utils.py 导入） ====================

# 这些函数将从 subtitle_utils.py 导入
# _render_remotion_subtitle_v2
# _prepare_subtitle  
# _burn_subtitle

# 预先导入，避免循环导入
def _render_remotion_subtitle_v2(*args, **kwargs):
    from app.tasks.subtitle_utils import _render_remotion_subtitle_v2
    return _render_remotion_subtitle_v2(*args, **kwargs)

def _prepare_subtitle(*args, **kwargs):
    from app.tasks.subtitle_utils import _prepare_subtitle
    return _prepare_subtitle(*args, **kwargs)

def _burn_subtitle(*args, **kwargs):
    from app.tasks.subtitle_utils import _burn_subtitle
    return _burn_subtitle(*args, **kwargs)

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
    'generate_variants_task',
    '_generate_single_variant'
]