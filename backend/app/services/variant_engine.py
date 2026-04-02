# backend/app/services/variant_engine.py
"""
视觉变体引擎 v4.1 - 背景模糊+画中画（PIP）模式 + 词级动画

架构：三层合成
1. 背景层：v3.0 强化版（全景模糊 + 7项必做 + 增强效果）
2. 中间层：画中画（60-70% 缩放，同步变速）
3. 文字层：词级动画字幕（Word Level Animation v3.0）

v4.1 更新：
- 升级文字层：静态字幕 → 词级动画
- 支持 3 种动画模板：pop_highlight, karaoke_flow, hype_gaming
- 随机选择模板，增加变体独特性

Created: 2026-03-10
Updated: 2026-03-22 - 集成词级动画引擎
"""
import random
import subprocess
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger


class PIPVariantEngineV4:
    """
    画中画变体引擎 v4.0
    
    核心特性：
    - 三层架构：背景层 + 中间层 + 文字层
    - 背景层采用 v3.0 强化版（7项必做 + 增强效果）
    - 中间层与背景同步变速
    - 文字层显示字幕（WhisperX 提取）
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # 增强组合数量范围
        self.min_enhanced = self.config.get('min_enhanced', 3)
        self.max_enhanced = self.config.get('max_enhanced', 5)
        
        # WhisperX 配置
        self.whisperx_enabled = self.config.get('whisperx_enabled', True)
        
    def generate_variant(
        self, 
        input_path: str, 
        output_path: str, 
        seed: Optional[int] = None
    ) -> Dict:
        """
        生成画中画变体
        
        流程：
        1. 提取字幕（WhisperX）
        2. 生成随机参数
        3. 构建 FFmpeg 滤镜
        4. 执行三层合成
        """
        if seed is not None:
            random.seed(seed)
        
        logger.info(f"[v4.0 PIP] 开始处理: {input_path}")
        
        # 获取视频信息
        duration = self._get_duration(input_path)
        if duration == 0:
            return {'success': False, 'error': '无法获取视频时长'}
        
        # Step 1: 提取字幕
        subtitle_path = None
        if self.whisperx_enabled:
            subtitle_path = self._extract_subtitles(input_path)
        
        # Step 2: 生成随机参数
        params = self._random_params()
        
        # Step 2.5: 计算抽帧时间点
        drop_times = self._calculate_frame_drop_times(duration)
        params['drop_times'] = drop_times
        
        logger.info(f"[v4.0 PIP] 参数: 变速={params['speed']:.2f}x, 模糊σ={params['bg_blur']:.1f}, "
                   f"放大={params['bg_scale']:.2f}x, 抽帧={len(drop_times)}帧")
        
        # Step 3: 构建滤镜
        filter_complex = self._build_filter_complex(params, duration, subtitle_path, drop_times)
        
        # Step 4: 执行 FFmpeg
        success = self._run_ffmpeg(input_path, output_path, filter_complex, params['speed'])
        
        result = {
            'success': success,
            'params': params,
            'has_subtitle': subtitle_path is not None,
            'output_path': output_path if success else None
        }
        
        # 清理临时字幕文件
        if subtitle_path and os.path.exists(subtitle_path):
            try:
                os.remove(subtitle_path)
            except:
                pass
        
        return result
    
    # ==================== 参数生成 ====================
    
    def _random_params(self) -> Dict:
        """
        生成随机参数（v4.0 规范）
        
        必做特效（7项）：
        1. 全景模糊 σ=60-80
        2. 背景放大 150-200%
        3. 变速 1.05-1.2x
        4. 抽帧（每10秒抽1帧 / 不足10秒抽2帧）
        5. 镜像翻转 50%
        6. 裁剪 5-10%
        7. 旋转 ±10°
        """
        return {
            # 必做特效
            'bg_blur': random.uniform(30, 50),          # 全景模糊 σ=30-50（调整后）
            'bg_brightness': 0,                          # 无暗化
            'bg_scale': random.uniform(1.1, 1.4),       # 放大 110-140%（调整后）
            'speed': random.uniform(1.05, 1.2),         # 变速 1.05-1.2x
            'mirror': random.random() > 0.5,            # 50% 镜像
            'crop_ratio': random.uniform(0.03, 0.05),   # 裁剪 3-5%
            'rotation': random.uniform(-10, 10),        # 旋转 ±10°
            
            # 中间层模式：landscape（横屏）/ portrait_crop（竖屏裁剪，默认）
            # 由前端配置决定，不是随机
            'fg_mode': self.config.get('fg_mode', 'portrait_crop'),

            # 增强特效（从 7 项选 3-5 个，已移除画中画）
            'enhance_effects': self._select_enhance_effects(),
        }
    
    def _select_enhance_effects(self) -> List[str]:
        """
        从 7 项增强特效中随机选 3-5 个
        
        注意：画中画已移除（已作为架构层处理）
        """
        all_effects = [
            'saturation',   # 饱和度
            'brightness',   # 亮度
            'contrast',     # 对比度
            'rgb_shift',    # RGB偏移
            'darken',       # 暗化
            'color_temp',   # 色调统一
            'frame_swap',   # 帧交换
        ]
        count = random.randint(self.min_enhanced, self.max_enhanced)
        return random.sample(all_effects, min(count, len(all_effects)))
    
    # ==================== 滤镜构建 ====================
    
    def _build_filter_complex(
        self, 
        params: Dict, 
        duration: float,
        subtitle_path: Optional[str] = None,
        drop_times: Optional[List[float]] = None
    ) -> str:
        """
        构建 FFmpeg filter_complex（三层合成）
        
        结构：
        [0:v] → 背景层处理 → [bg]
        [0:v] → 中间层处理 → [fg]
        [bg][fg] → overlay → [video]
        [video] → 字幕叠加（如果有）→ [out]
        """
        bg_filters = []
        fg_filters = []
        
        # ========== 背景层处理 ==========
        
        # 1. 镜像翻转（50%概率）
        if params['mirror']:
            bg_filters.append("hflip")
        
        # 2. 放大 110-140%
        bg_filters.append(f"scale=iw*{params['bg_scale']:.2f}:ih*{params['bg_scale']:.2f}")
        
        # 3. 全景模糊 σ=40-60
        bg_filters.append(f"gblur=sigma={params['bg_blur']:.1f}")
        
        # 3.5 背景层暗化 -0.3~-0.1（随机）
        bg_filters.append(f"eq=brightness={params['bg_brightness']:.2f}")
        
        # 4. 同步变速（移到 rotate 之前）
        speed = params.get('speed', 1.1)
        bg_filters.append(f"setpts={1/speed:.3f}*PTS")
        
        # 5. 旋转 ±10°（移到 setpts 之后，避免帧冻结）
        rotation_rad = params.get('rotation', params.get('fg_rotation', 0)) * 3.14159 / 180
        if abs(rotation_rad) > 0.01:  # 只在旋转角度 > 0.5° 时应用
            bg_filters.append(f"rotate={rotation_rad:.4f}:c=black:fillcolor=black")
        
        # 6. 裁剪 5-10%
        crop_ratio = params.get('crop_ratio', 0.08)
        bg_filters.append(f"crop=iw*(1-{crop_ratio*2:.2f}):ih*(1-{crop_ratio*2:.2f}):iw*{crop_ratio:.2f}:ih*{crop_ratio:.2f}")
        
        # 7. 增强效果
        for effect in params.get('enhance_effects', []):
            effect_filter = self._build_enhance_filter(effect)
            if effect_filter:
                bg_filters.append(effect_filter)
        
        # ========== 中间层处理（v4.0 规范）==========

        fg_mode = params.get('fg_mode', 'portrait_crop')
        params['fg_mode'] = fg_mode

        if fg_mode == 'landscape':
            # 横屏模式：保持原始比例，横屏视频（16:9）居中显示
            # 适用于：源视频本身就是横屏（16:9）
            # 如果源视频是竖屏，会自动 fallback 到 portrait_crop 效果
            
            # 缩放：让中间层在竖屏背景中居中，高度占屏幕 60-70%
            # 横屏视频（如 1920x1080）缩放后：
            # - 高度 = 原高 * fg_height_ratio
            # - 宽度 = 按比例自动计算（-2）
            fg_height_ratio = random.uniform(0.60, 0.70)
            fg_filters.append(f"scale=-2:ih*{fg_height_ratio:.2f}")
            
            params['fg_height_ratio'] = fg_height_ratio
            params['fg_target_ratio'] = fg_height_ratio

            # 无暗化
            fg_brightness = 0
            fg_filters.append(f"eq=brightness={fg_brightness:.2f}")
            params['fg_brightness'] = fg_brightness

        else:
            # 竖屏裁剪模式（默认）
            # 1. 缩放：与背景层同比例放大
            fg_scale = params.get('bg_scale', 1.75)  # 使用背景层的放大比例
            fg_filters.append(f"scale=iw*{fg_scale:.2f}:ih*{fg_scale:.2f}")
            params['fg_scale'] = fg_scale

            # 2. 无暗化
            fg_brightness = 0
            fg_filters.append(f"eq=brightness={fg_brightness:.2f}")
            params['fg_brightness'] = fg_brightness

            # 3. 裁剪上下边缘，剩余 60-70%
            remaining = random.uniform(0.60, 0.70)  # 剩余 60-70%
            total_crop = 1.0 - remaining
            # 上下分配：顶部占 40-60%，底部占剩余
            top_ratio = random.uniform(0.40, 0.60)
            crop_top_ratio = total_crop * top_ratio
            crop_bottom_ratio = total_crop * (1 - top_ratio)
            # 使用 crop 滤镜（只裁剪上下，宽度保持不变）
            fg_filters.append(f"crop=iw:ih*{remaining:.2f}:0:ih*{crop_top_ratio:.2f}")
            params['fg_crop_top'] = crop_top_ratio
            params['fg_crop_bottom'] = crop_bottom_ratio
            params['fg_remaining'] = remaining

            # 4. 边框（50% 概率）- 只有上下边缘有边框
            has_border = random.random() > 0.5
            params['has_border'] = has_border

            if has_border:
                # 边框粗细 14-18px
                border_width = random.randint(14, 18)
                # 边框颜色随机：白/黄/浅蓝/浅紫
                border_colors = ['white', 'yellow', 'lightblue', 'lavender']
                border_color = random.choice(border_colors)
                params['border_width'] = border_width
                params['border_color'] = border_color

                # FFmpeg 颜色映射
                color_map = {
                    'white': 'white',
                    'yellow': 'yellow',
                    'lightblue': '0xADD8E6',  # 浅蓝色
                    'lavender': '0xE6E6FA',   # 浅紫色
                }
                # 只在上下添加边框（pad 只增加上下高度，左右宽度不变）
                fg_filters.append(f"pad=iw:ih+{border_width*2}:0:{border_width}:color={color_map[border_color]}")

        # 同步变速（与背景相同）
        fg_filters.append(f"setpts={1/speed:.3f}*PTS")
        
        # ========== 构建 filter_complex ==========
        
        # 背景层
        bg_chain = ','.join(bg_filters)
        
        # 中间层
        fg_chain = ','.join(fg_filters)
        
        # 三层合成 - 中间层居中
        filter_complex = f"[0:v]{bg_chain}[bg];[0:v]{fg_chain}[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[video]"
        
        # 抽帧处理（在合成后应用）
        if drop_times:
            drop_filter = self._build_frame_drop_filter(drop_times)
            if drop_filter:
                filter_complex += f";[video]{drop_filter}[v_dropped]"
                final_video = "[v_dropped]"
            else:
                final_video = "[video]"
        else:
            final_video = "[video]"
        
        # 字幕叠加（如果有）
        if subtitle_path:
            # 转义路径中的特殊字符
            escaped_path = subtitle_path.replace(':', '\\:').replace('\\', '/')
            filter_complex += f";{final_video}subtitles='{escaped_path}':force_style='Fontsize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H1A1A1A,Outline=3'[out]"
            final_video = "[out]"
        
        # 保存最终视频流标签供 FFmpeg 使用
        self._final_video_label = final_video
        return filter_complex
    
    def _build_enhance_filter(self, effect: str) -> str:
        """构建增强效果滤镜（背景层专用）"""
        
        if effect == 'saturation':
            # 饱和度 0.90-1.15
            val = random.uniform(0.90, 1.15)
            return f"eq=saturation={val:.2f}"
        
        elif effect == 'brightness':
            # 亮度 -0.10~0.15（背景层建议暗化）
            val = random.uniform(-0.10, 0.05)
            return f"eq=brightness={val:.2f}"
        
        elif effect == 'contrast':
            # 对比度 0.90-1.15
            val = random.uniform(0.90, 1.15)
            return f"eq=contrast={val:.2f}"
        
        elif effect == 'rgb_shift':
            # RGB偏移 2-5
            shift = random.randint(2, 5)
            return f"colorchannelmixer=rr=1.{shift:02d}:gg=1.{shift:02d}:bb=1.{shift:02d}"
        
        elif effect == 'darken':
            # 暗化 -0.15~-0.25
            val = random.uniform(-0.25, -0.15)
            return f"eq=brightness={val:.2f}"
        
        elif effect == 'color_temp':
            # 色调统一 ±10%（使用色彩平衡）
            val = random.uniform(-0.10, 0.10)
            return f"colorbalance=rs={val:.2f}:gs={val:.2f}:bs={val:.2f}"
        
        elif effect == 'frame_swap':
            # 帧交换 - 简化实现
            return "fps=fps=29.97"
        
        return ""
    
    # ==================== 字幕提取（v4.1 词级动画）====================
    
    def _extract_subtitles(self, video_path: str) -> Optional[str]:
        """
        使用 WhisperX 提取字幕 → 生成词级动画 ASS
        
        v4.1 升级：
        - 提取词级时间戳（word_timestamps=True）
        - 支持指定动画模板（从配置读取，None 则随机）
        - 支持指定字幕位置（从配置读取）
        - 生成动态词级动画 ASS
        
        Returns:
            ASS 字幕文件路径，或 None（无字幕）
        """
        try:
            import whisperx
            
            # 临时字幕文件
            ass_path = video_path.replace('.mp4', '_animated.ass')
            
            # 加载模型（使用 base 模型平衡速度和准确度）
            device = "cuda" if self._check_cuda() else "cpu"
            model = whisperx.load_model("base", device)
            
            # 转录（启用词级时间戳）
            audio = whisperx.load_audio(video_path)
            result = model.transcribe(audio, batch_size=16, word_timestamps=True)
            
            # 检测到语音
            segments = result.get("segments", [])
            if not segments:
                logger.info(f"[v4.1 PIP] 未检测到语音，跳过文字层")
                return None
            
            # 提取词级数据
            words = []
            for segment in segments:
                segment_words = segment.get('words', [])
                for word_data in segment_words:
                    words.append({
                        'word': word_data.get('word', '').strip(),
                        'start': round(word_data.get('start', 0), 3),
                        'end': round(word_data.get('end', 0), 3),
                        'confidence': round(word_data.get('probability', word_data.get('confidence', 1.0)), 3),
                    })
            
            if not words or len(words) < 5:
                reason = "无词级数据" if not words else f"词数过少({len(words)}个)"
                logger.info(f"[v4.1 PIP] {reason}，检查是否启用占位字幕...")
                
                # 检查是否启用占位字幕（默认启用）
                placeholder_enabled = self.config.get('placeholder_subtitle_enabled', True)
                
                if placeholder_enabled:
                    # 生成占位字幕
                    placeholder_result = self._generate_placeholder_subtitle(
                        video_path=video_path,
                        ass_path=ass_path
                    )
                    if placeholder_result:
                        logger.info(f"[v4.1 PIP] 使用占位字幕替代")
                        return ass_path
                    else:
                        logger.info(f"[v4.1 PIP] 占位字幕生成失败，跳过文字层")
                        return None
                else:
                    logger.info(f"[v4.1 PIP] 占位字幕未启用，跳过文字层")
                    return None
            
            # 从配置获取动画模板（None 则随机）
            template_id = self.config.get('animation_template')
            if not template_id:
                # PyCaps 12 个预设模板
                templates = [
                    'minimalist', 'default', 'classic', 'neo_minimal',
                    'hype', 'explosive', 'fast', 'vibrant',
                    'word_focus', 'line_focus', 'retro_gaming', 'model'
                ]
                template_id = random.choice(templates)
            
            # 从配置获取位置（简化为 3 个位置）
            position = self.config.get('animation_position', 'bottom_center')
            
            template_names = {
                'minimalist': '极简风格',
                'default': '默认风格',
                'classic': '经典风格',
                'neo_minimal': '新极简风格',
                'hype': '动感风格',
                'explosive': '爆炸风格',
                'fast': '快速风格',
                'vibrant': '活力风格',
                'word_focus': '词焦点风格',
                'line_focus': '行焦点风格',
                'retro_gaming': '复古游戏风格',
                'model': '模特风格',
            }
            
            position_names = {
                'top_center': '顶部居中',
                'center': '中部居中',
                'bottom_center': '底部居中',
            }
            
            # 生成词级动画 ASS
            from .word_level_animation import generate_word_level_animation
            
            result = generate_word_level_animation(
                words_data=words,
                output_path=ass_path,
                video_width=1080,
                video_height=1920,
                template_id=template_id,
                position=position,
            )
            
            if result['success']:
                logger.info(f"[v4.1 PIP] 词级动画字幕生成成功: 模板={template_names.get(template_id, template_id)}, 位置={position}, 词数={len(words)}")
                return ass_path
            else:
                logger.warning(f"[v4.1 PIP] 词级动画生成失败: {result.get('error')}")
                return None
                
        except ImportError:
            logger.warning("[v4.1 PIP] WhisperX 未安装，跳过字幕提取")
            return None
        except Exception as e:
            logger.warning(f"[v4.1 PIP] 字幕提取失败: {e}")
            return None
    
    # 保留旧方法作为 fallback
    def _save_srt(self, segments: List, output_path: str):
        """保存 SRT 格式字幕（fallback）"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start = self._format_srt_time(seg['start'])
                end = self._format_srt_time(seg['end'])
                text = seg['text'].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    
    def _format_srt_time(self, seconds: float) -> str:
        """格式化 SRT 时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"
    
    def _check_cuda(self) -> bool:
        """检查 CUDA 是否可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def _generate_placeholder_subtitle(self, video_path: str, ass_path: str) -> bool:
        """
        为无字幕视频生成占位字幕
        
        规则：
        - 从第 3 秒开始
        - 每 3 秒显示一次
        - 方案1: "Don't Miss Next Game👀   ⚽🏀🏈⚾🏒Sports Highlights & Live HD   🔥 Link in My Bio🔥" (2.5秒)
        - 方案2: "Watch HD LIVE → 🔥Link in My Bio🔥" (2秒)
        - 位置固定在顶部
        - 使用用户指定的动画模板
        """
        try:
            import subprocess
            import json
            
            # 获取视频时长
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            video_info = json.loads(result.stdout)
            duration = float(video_info.get('format', {}).get('duration', 0))
            
            if duration <= 3:
                logger.info(f"[占位字幕] 视频时长 {duration}s 太短，跳过")
                return False
            
            # 占位字幕模板
            templates = [
                {
                    'text': "Don't Miss Next Game👀   ⚽🏀🏈⚾🏒Sports Highlights & Live HD   🔥 Link in My Bio🔥",
                    'duration': 2.5,
                    'words': ["Don't", "Miss", "Next", "Game👀", "⚽🏀🏈⚾🏒Sports", "Highlights", "&", "Live", "HD", "🔥", "Link", "in", "My", "Bio🔥"]
                },
                {
                    'text': "Watch HD LIVE → 🔥Link in My Bio🔥",
                    'duration': 2.0,
                    'words': ["Watch", "HD", "LIVE", "→", "🔥Link", "in", "My", "Bio🔥"]
                }
            ]
            
            # 随机选择模板
            template = random.choice(templates)
            template_idx = templates.index(template) + 1
            logger.info(f"[占位字幕] 选择模板: 方案{template_idx}")
            
            # 生成词级数据
            words = []
            start_time = 3.0  # 从第3秒开始
            interval = 3.0  # 间隔3秒
            
            while start_time < duration:
                # 计算这一条的结束时间
                end_time = min(start_time + template['duration'], duration)
                
                # 逐词分配时间
                word_count = len(template['words'])
                word_duration = (end_time - start_time) / word_count
                
                for i, word in enumerate(template['words']):
                    word_start = start_time + i * word_duration
                    word_end = word_start + word_duration
                    words.append({
                        'word': word,
                        'start': round(word_start, 3),
                        'end': round(word_end, 3),
                        'confidence': 1.0
                    })
                
                # 移动到下一个时间点
                start_time += interval
            
            if not words:
                logger.warning(f"[占位字幕] 未生成任何词级数据")
                return False
            
            # 获取动画模板（从配置中读取用户选择，None 则随机）
            template_id = self.config.get('animation_template')
            if not template_id:
                templates_list = [
                    'minimalist', 'default', 'classic', 'neo_minimal',
                    'hype', 'explosive', 'fast', 'vibrant',
                    'word_focus', 'line_focus', 'retro_gaming', 'model'
                ]
                template_id = random.choice(templates_list)
            
            # 固定位置为顶部
            position = 'top_center'
            
            logger.info(f"[占位字幕] 生成 {len(words)} 个词，模板={template_id}, 位置={position}")
            
            # 生成 ASS 字幕
            from .word_level_animation import generate_word_level_animation
            
            result = generate_word_level_animation(
                words_data=words,
                output_path=ass_path,
                video_width=1080,
                video_height=1920,
                template_id=template_id,
                position=position,
            )
            
            if result['success']:
                logger.info(f"[占位字幕] 生成成功: {ass_path}")
                return True
            else:
                logger.warning(f"[占位字幕] 生成失败: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.warning(f"[占位字幕] 生成异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ==================== FFmpeg 执行 ====================
    
    def _run_ffmpeg(
        self, 
        input_path: str, 
        output_path: str, 
        filter_complex: str,
        speed: float = 1.0
    ) -> bool:
        """执行 FFmpeg 命令（三层合成）"""
        
        # 基础命令
        cmd = [
            'ffmpeg', '-i', input_path,
            '-filter_complex', filter_complex,
        ]
        
        # 变速（音频同步）
        if speed != 1.0:
            cmd.extend(['-filter:a', f'atempo={speed:.2f}'])
        
        # 选择输出流 - 使用动态视频流标签
        video_label = getattr(self, '_final_video_label', '[video]')
        cmd.extend(['-map', video_label, '-map', '0:a'])
        
        # 编码设置 - v4.1.6 优化：质量换速度
        cmd.extend([
            '-c:v', 'mpeg4', '-q:v', '15',  # PIP合成：8→15，加速编码
            '-threads', '2',                # 4核CPU + 4变体并行，每任务2线程
            '-c:a', 'aac',
            '-y', output_path
        ])
        
        logger.debug(f"[v4.0 PIP] FFmpeg: {' '.join(cmd[:10])}...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=1800)  # 30分钟超时
            if result.returncode != 0:
                logger.error(f"FFmpeg 错误: {result.stderr.decode()[:500]}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg 超时: {input_path}")
            return False
        except Exception as e:
            logger.error(f"FFmpeg 错误: {e}")
            return False
    
    # ==================== 工具方法 ====================
    
    def _get_duration(self, video_path: str) -> float:
        """获取视频时长"""
        cmd = [
            'ffprobe', '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except:
            return 0.0
    
    def _calculate_frame_drop_times(self, duration: float) -> List[float]:
        """
        计算抽帧时间点（v4.0 规范）
        
        规则：
        - 每 10 秒区间内随机抽 1 帧
        - 不足 10 秒：在视频总长内随机抽 2 帧
        
        Returns:
            需要丢弃的帧时间点列表（秒）
        """
        drop_times = []
        
        if duration < 10:
            # 不足 10 秒：随机抽 2 帧（确保不重复且间隔合理）
            min_gap = 0.5  # 最小间隔 0.5 秒
            available = duration - min_gap
            if available > min_gap:
                t1 = random.uniform(0.2, available / 2)
                t2 = random.uniform(t1 + min_gap, duration - 0.2)
                drop_times = [t1, t2]
            else:
                # 视频太短，只抽 1 帧
                drop_times = [random.uniform(0.1, duration - 0.1)]
        else:
            # 每 10 秒区间内随机抽 1 帧
            num_segments = int(duration / 10)
            for i in range(num_segments):
                segment_start = i * 10
                segment_end = min((i + 1) * 10, duration)
                # 在该区间内随机选一个时间点（避开开头和结尾 0.2 秒）
                if segment_end - segment_start > 0.5:
                    drop_time = random.uniform(segment_start + 0.2, segment_end - 0.2)
                    drop_times.append(drop_time)
        
        logger.info(f"[v4.0 PIP] 抽帧时间点: {[f'{t:.2f}s' for t in drop_times]}")
        return drop_times
    
    def _build_frame_drop_filter(self, drop_times: List[float], fps: float = 30.0) -> str:
        """
        构建抽帧滤镜（简化版）
        
        由于 select 滤镜在某些情况下会导致视频流失效，
        这里改用 fps 滤镜进行简单的帧率调整
        
        Args:
            drop_times: 要丢弃的时间点列表
            fps: 视频帧率
        
        Returns:
            FFmpeg 滤镜字符串
        """
        if not drop_times:
            return ""
        
        # 简化实现：使用 fps 滤镜进行帧率调整
        # 这样更稳定，虽然不是精确抽帧，但能达到去重效果
        # 原帧率 → 29.97fps（轻微改变帧序列）
        return "fps=fps=29.97"
    
    def _get_video_fps(self, video_path: str) -> float:
        """获取视频帧率"""
        cmd = [
            'ffprobe', '-v', 'error', 
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            fps_str = result.stdout.strip()
            # 处理 "30000/1001" 格式
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den)
            return float(fps_str)
        except:
            return 30.0  # 默认 30fps


# ==================== 统一入口（替代 v3.0）====================

class VariantEngine:
    """
    变体引擎 v4.0 - PIP 模式（唯一版本）
    
    v3.0 已废弃，使用 PIPVariantEngineV4
    """
    
    def __init__(self, config: Dict = None):
        self.pip_engine = PIPVariantEngineV4(config)
    
    def generate_variant(
        self, 
        input_path: str, 
        output_path: str, 
        seed: Optional[int] = None
    ) -> Dict:
        """生成单个变体"""
        return self.pip_engine.generate_variant(input_path, output_path, seed)
    
    def generate_variants(
        self, 
        input_path: str, 
        output_dir: str, 
        count: int = 10
    ) -> List[Dict]:
        """
        批量生成变体
        
        Args:
            input_path: 源视频路径
            output_dir: 输出目录
            count: 变体数量
        
        Returns:
            变体结果列表
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i in range(count):
            output_path = os.path.join(output_dir, f"variant_{i+1:03d}.mp4")
            result = self.pip_engine.generate_variant(input_path, output_path)
            result['variant_index'] = i + 1
            results.append(result)
            
            if result['success']:
                logger.info(f"[v4.0 PIP] 变体 {i+1}/{count} 完成")
            else:
                logger.error(f"[v4.0 PIP] 变体 {i+1}/{count} 失败")
        
        return results


# ==================== 保留音频引擎（BGM 替换）====================

class AudioVariantEngine:
    """音频变体引擎 - BGM 替换"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.bgm_dir = Path(config.get('bgm_dir', './sports_bgm'))
        self.bgm_volume = config.get('bgm_volume', 0.1)
        
        self.sports_bgm = {
            'baseball': self.bgm_dir / 'baseball',
            'basketball': self.bgm_dir / 'basketball',
            'football': self.bgm_dir / 'football',
            'hockey': self.bgm_dir / 'hockey',
            'default': self.bgm_dir / 'general'
        }
    
    def replace_bgm(
        self, 
        input_path: str, 
        output_path: str, 
        sport_type: str = "default"
    ) -> Dict:
        """替换 BGM"""
        bgm_dir = self.sports_bgm.get(sport_type, self.sports_bgm['default'])
        
        if not bgm_dir.exists():
            subprocess.run(['cp', input_path, output_path], check=True)
            return {'success': True, 'bgm_replaced': False}
        
        bgm_files = list(bgm_dir.glob("*.mp3")) + list(bgm_dir.glob("*.wav"))
        if not bgm_files:
            subprocess.run(['cp', input_path, output_path], check=True)
            return {'success': True, 'bgm_replaced': False}
        
        bgm = random.choice(bgm_files)
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-i', str(bgm),
            '-filter_complex', 
            f"[0:a]volume=1.0[a0];[1:a]volume={self.bgm_volume}[a1];"
            f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=3[audio]",
            '-map', '0:v', '-map', '[audio]',
            '-c:v', 'copy', '-c:a', 'aac',
            '-y', output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, timeout=300, check=True)
            return {'success': True, 'bgm_replaced': True, 'bgm_file': str(bgm.name)}
        except subprocess.CalledProcessError as e:
            logger.error(f"BGM 替换失败: {e}")
            subprocess.run(['cp', input_path, output_path], check=True)
            return {'success': True, 'bgm_replaced': False}
