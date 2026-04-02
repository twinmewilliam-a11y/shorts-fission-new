# backend/app/services/subtitle_extractor.py
"""
字幕提取服务 - 多来源支持

字幕来源优先级：
1. 外挂字幕文件（.srt/.vtt/.ass）← 优先级最高
2. 内嵌软字幕（视频容器内）    ← FFmpeg 提取
3. WhisperX 转录               ← 最后手段

策略：
- 只处理一次，所有变体共享
- CPU 模式：base 模型 ~20-30 秒处理 1 分钟视频
- GPU 模式：快 10 倍
- 自动降级：无语音/失败 → 返回 None

Created: 2026-03-11
Updated: 2026-03-11 - 增加多来源字幕支持
"""
import os
import glob
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from loguru import logger


class SubtitleExtractor:
    """多来源字幕提取器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.model_size = self.config.get('model_size', 'base')  # tiny/base/small/medium
        self.device = self._detect_device()
        self.model = None
        self._whisperx_available = None
        
    def _detect_device(self) -> str:
        """检测最佳设备"""
        try:
            import torch
            if torch.cuda.is_available():
                logger.info(f"[字幕] 检测到 GPU: {torch.cuda.get_device_name(0)}")
                return 'cuda'
        except:
            pass
        logger.info("[字幕] 使用 CPU 模式")
        return 'cpu'
    
    def _check_whisperx(self) -> bool:
        """检查 WhisperX 是否可用"""
        if self._whisperx_available is None:
            try:
                import whisperx
                self._whisperx_available = True
                logger.info("[字幕] WhisperX 可用")
            except ImportError:
                self._whisperx_available = False
                logger.warning("[字幕] WhisperX 未安装，仅支持提取已有字幕")
                logger.warning("[字幕] 安装命令: pip install whisperx")
        return self._whisperx_available
    
    # ==================== 主入口：智能提取 ====================
    
    def extract_smart(
        self, 
        video_path: str,
        output_dir: str = None,
        prefer_lang: str = None
    ) -> Optional[str]:
        """
        智能提取字幕（多来源优先级）
        
        优先级：
        1. 外挂字幕文件
        2. 内嵌软字幕
        3. WhisperX 转录
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录（默认与视频同目录）
            prefer_lang: 首选语言（如 'zh', 'en'）
        
        Returns:
            ASS 字幕文件路径，失败返回 None
        """
        if output_dir is None:
            output_dir = os.path.dirname(video_path)
        
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.ass")
        
        # 1. 检查外挂字幕文件
        external_sub = self._find_external_subtitle(video_path, output_dir)
        if external_sub:
            logger.info(f"[字幕] 使用外挂字幕: {external_sub}")
            return self._convert_to_ass(external_sub, output_path)
        
        # 2. 检查内嵌软字幕
        embedded_sub = self._extract_embedded_subtitle(video_path, output_dir, prefer_lang)
        if embedded_sub:
            logger.info(f"[字幕] 使用内嵌字幕")
            return self._convert_to_ass(embedded_sub, output_path)
        
        # 3. WhisperX 转录
        logger.info("[字幕] 无现成字幕，启动 WhisperX 转录...")
        return self._transcribe_with_whisperx(video_path, output_path)
    
    # ==================== 外挂字幕检测 ====================
    
    def _find_external_subtitle(self, video_path: str, search_dir: str = None) -> Optional[str]:
        """
        查找外挂字幕文件
        
        支持：.srt, .vtt, .ass, .ssa
        匹配规则：视频文件名相同，或包含视频文件名
        """
        if search_dir is None:
            search_dir = os.path.dirname(video_path)
        
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        subtitle_exts = ['.srt', '.vtt', '.ass', '.ssa']
        
        # 1. 精确匹配：video_name.srt
        for ext in subtitle_exts:
            exact_match = os.path.join(search_dir, f"{base_name}{ext}")
            if os.path.exists(exact_match):
                return exact_match
        
        # 2. 模糊匹配：包含视频名的字幕文件
        for ext in subtitle_exts:
            patterns = [
                os.path.join(search_dir, f"*{base_name}*{ext}"),
                os.path.join(search_dir, f"{base_name}.*{ext}"),
            ]
            for pattern in patterns:
                matches = glob.glob(pattern)
                if matches:
                    # 优先选择中文/英文字幕
                    for m in matches:
                        lower = m.lower()
                        if 'zh' in lower or 'cn' in lower or 'chinese' in lower:
                            return m
                        if 'en' in lower or 'english' in lower:
                            return m
                    # 返回第一个匹配
                    return matches[0]
        
        return None
    
    # ==================== 内嵌字幕提取 ====================
    
    def _extract_embedded_subtitle(
        self, 
        video_path: str,
        output_dir: str,
        prefer_lang: str = None
    ) -> Optional[str]:
        """
        提取视频内嵌软字幕
        
        使用 FFmpeg 提取
        """
        try:
            # 1. 列出所有字幕流
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 's',
                '-show_entries', 'stream=index,codec_name,language:title',
                '-of', 'json',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.debug("[字幕] 无法探测内嵌字幕")
                return None
            
            import json
            probe_data = json.loads(result.stdout)
            streams = probe_data.get('streams', [])
            
            if not streams:
                logger.debug("[字幕] 视频无内嵌字幕流")
                return None
            
            # 2. 选择最佳字幕流
            target_stream = self._select_best_subtitle_stream(streams, prefer_lang)
            if target_stream is None:
                return None
            
            stream_index = target_stream['index']
            logger.info(f"[字幕] 发现内嵌字幕流 #{stream_index}: {target_stream.get('language', 'unknown')}")
            
            # 3. 提取字幕
            output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}_embedded.srt")
            
            cmd = [
                'ffmpeg', '-y', '-i', video_path,
                '-map', f'0:{stream_index}',
                '-c:s', 'srt',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                logger.warning(f"[字幕] 内嵌字幕提取失败: {result.stderr.decode()[:200]}")
                return None
                
        except Exception as e:
            logger.warning(f"[字幕] 内嵌字幕提取异常: {e}")
            return None
    
    def _select_best_subtitle_stream(
        self, 
        streams: List[Dict], 
        prefer_lang: str = None
    ) -> Optional[Dict]:
        """
        选择最佳字幕流
        
        优先级：
        1. 指定语言
        2. 中文
        3. 英文
        4. 第一个
        """
        if not streams:
            return None
        
        lang_priority = ['zh', 'cn', 'chi', 'zho', 'en', 'eng']
        if prefer_lang:
            lang_priority.insert(0, prefer_lang.lower())
        
        for lang in lang_priority:
            for stream in streams:
                stream_lang = (stream.get('language') or '').lower()
                if lang in stream_lang:
                    return stream
        
        # 返回第一个
        return streams[0]
    
    # ==================== WhisperX 转录 ====================
    
    def _transcribe_with_whisperx(
        self, 
        video_path: str, 
        output_path: str
    ) -> Optional[str]:
        """使用 WhisperX 转录"""
        if not self._check_whisperx():
            logger.warning("[字幕] WhisperX 不可用，跳过转录")
            return None
        
        if not self._load_model():
            return None
        
        audio_path = None
        try:
            # 1. 提取音频
            logger.info(f"[字幕] 提取音频: {video_path}")
            audio_path = self._extract_audio(video_path)
            if audio_path is None:
                return None
            
            # 2. 转录
            logger.info(f"[字幕] 开始转录...")
            import whisperx
            
            result = self.model.transcribe(audio_path, batch_size=16)
            
            # 3. 检测语音
            segments = result.get('segments', [])
            if not segments:
                logger.info("[字幕] 未检测到语音内容")
                return None
            
            detected_lang = result.get('language', 'unknown')
            logger.info(f"[字幕] 检测到语言: {detected_lang}, 片段数: {len(segments)}")
            
            # 4. 对齐时间戳
            try:
                logger.info("[字幕] 对齐时间戳...")
                align_model, align_metadata = whisperx.load_align_model(
                    language_code=detected_lang, 
                    device=self.device
                )
                result = whisperx.align(
                    segments, 
                    align_model, 
                    align_metadata, 
                    audio_path, 
                    self.device,
                    return_char_alignments=False
                )
                segments = result.get('segments', segments)
                logger.info("[字幕] 时间戳对齐完成")
            except Exception as e:
                logger.warning(f"[字幕] 对齐失败，使用原始时间戳: {e}")
            
            # 5. 保存为 ASS 格式
            self._save_ass(segments, output_path)
            
            total_duration = segments[-1]['end'] if segments else 0
            logger.info(f"[字幕] 转录完成: {len(segments)} 个片段, 时长 {total_duration:.1f}s → {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"[字幕] 转录失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
    
    def _load_model(self) -> bool:
        """懒加载 WhisperX 模型（优先使用预热的缓存模型）"""
        if not self._check_whisperx():
            return False
        
        # 1. 优先使用缓存的预热模型
        if self.model is None:
            try:
                from app.services.model_warmup import get_cached_whisperx_model, get_cached_device
                
                cached_model = get_cached_whisperx_model()
                cached_device = get_cached_device()
                
                if cached_model is not None:
                    logger.info("[字幕] 使用预热的缓存模型 ✅")
                    self.model = cached_model
                    if cached_device:
                        self.device = cached_device
                    return True
            except ImportError:
                logger.debug("[字幕] 预热模块未加载，使用常规加载")
            except Exception as e:
                logger.warning(f"[字幕] 获取缓存模型失败: {e}")
        
        # 2. 常规加载（如果缓存不可用）
        if self.model is None:
            try:
                import whisperx
                logger.info(f"[字幕] 加载 WhisperX 模型: {self.model_size}, 设备: {self.device}")
                compute_type = "int8" if self.device == "cpu" else "float16"
                self.model = whisperx.load_model(
                    self.model_size, 
                    self.device,
                    compute_type=compute_type
                )
                logger.info("[字幕] 模型加载完成")
            except Exception as e:
                logger.error(f"[字幕] 模型加载失败: {e}")
                return False
        return True
    
    # ==================== 字幕转换 ====================
    
    def _convert_to_ass(self, input_path: str, output_path: str) -> Optional[str]:
        """
        将 SRT/VTT/SSA 转换为 ASS 格式
        
        使用 FFmpeg 转换
        """
        try:
            # 使用自定义 ASS 转换，确保正确的分辨率和样式
            return self._srt_to_ass_with_style(input_path, output_path)
            
        except Exception as e:
            logger.error(f"[字幕] 转换异常: {e}")
            return None

    def _srt_to_ass_with_style(self, srt_path: str, ass_path: str) -> Optional[str]:
        """
        将 SRT 转换为 ASS 格式，使用正确的 1080x1920 分辨率和样式
        
        样式基于之前确认的 3 种方案（随机选择）
        """
        import random
        
        # 读取 SRT 内容
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        # 解析 SRT
        subtitles = self._parse_srt(srt_content)
        if not subtitles:
            logger.warning("[字幕] SRT 文件无有效内容")
            return None
        
        # 三种字幕样式（基于之前确认的方案）
        # 字体大小 20~28，随机选择
        font_size = random.randint(20, 28)
        
        # 位置：中间层下边缘（Alignment=2 底部居中，MarginV 控制距离底部的高度）
        # 中间层大约占 55-65% 高度，所以字幕应该在 35-45% 的位置
        # MarginV 越大，字幕越靠上
        margin_v = random.randint(400, 500)  # 距离底部 400-500px（约在画面中下部）
        
        # 背景透明度降低：&H50 比 &H70 不透明度更高（50% vs 30% 不透明）
        styles = [
            # 方案 A - 黑底白字（50%不透明）
            f"Style: Default, Arial Black, {font_size}, &H00FFFFFF, &H000000FF, &H00000000, &H50000000, 1, 0, 0, 0, 100, 100, 0, 0, 4, 0, 0, 2, 60, 60, {margin_v}, 1",
            # 方案 B - 深蓝底白字（50%不透明）
            f"Style: Default, Arial Black, {font_size}, &H00FFFFFF, &H000000FF, &H00000000, &H50333366, 1, 0, 0, 0, 100, 100, 0, 0, 4, 0, 0, 2, 60, 60, {margin_v}, 1",
            # 方案 C - 浅蓝底白字（50%不透明）
            f"Style: Default, Arial Black, {font_size}, &H00FFFFFF, &H000000FF, &H00000000, &H50666699, 1, 0, 0, 0, 100, 100, 0, 0, 4, 0, 0, 2, 60, 60, {margin_v}, 1",
        ]
        
        # 随机选择样式
        style_index = random.randint(0, 2)
        style_names = ['黑底白字', '深蓝底白字', '浅蓝底白字']
        
        # 写入 ASS 文件
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write("[Script Info]\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 1080\n")
            f.write("PlayResY: 1920\n")
            f.write("ScaledBorderAndShadow: yes\n")
            f.write("\n")
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write(styles[style_index] + "\n")
            f.write("\n")
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            for sub in subtitles:
                start = self._format_ass_time(sub['start'])
                end = self._format_ass_time(sub['end'])
                text = sub['text'].replace('\n', '\\N')
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
        
        logger.info(f"[字幕] ASS 转换完成（样式 {style_index + 1}）: {ass_path}")
        return ass_path
    
    def _parse_srt(self, srt_content: str) -> List[Dict]:
        """解析 SRT 格式字幕"""
        subtitles = []
        blocks = srt_content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue
            
            # 跳过序号行
            if lines[0].isdigit():
                lines = lines[1:]
            
            if len(lines) < 1:
                continue
            
            # 解析时间
            time_line = lines[0]
            if '-->' not in time_line:
                continue
            
            times = time_line.split('-->')
            if len(times) != 2:
                continue
            
            start = self._parse_srt_time(times[0].strip())
            end = self._parse_srt_time(times[1].strip())
            
            # 解析文本
            text = '\n'.join(lines[1:]).strip()
            
            if text:
                subtitles.append({
                    'start': start,
                    'end': end,
                    'text': text
                })
        
        return subtitles
    
    def _parse_srt_time(self, time_str: str) -> float:
        """解析 SRT 时间格式 (00:00:00,000)"""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        return 0
    
    def _format_ass_time(self, seconds: float) -> str:
        """格式化 ASS 时间 (H:MM:SS.CC)"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
    
    # ==================== 音频提取 ====================
    
    def _extract_audio(self, video_path: str) -> Optional[str]:
        """提取音频为 16kHz wav"""
        audio_path = tempfile.mktemp(suffix='.wav')
        
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            audio_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            
            if result.returncode != 0:
                stderr = result.stderr.decode()[:500]
                logger.error(f"[字幕] 音频提取失败: {stderr}")
                return None
            
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                logger.error("[字幕] 音频文件为空")
                return None
            
            return audio_path
            
        except subprocess.TimeoutExpired:
            logger.error("[字幕] 音频提取超时")
            return None
        except Exception as e:
            logger.error(f"[字幕] 音频提取异常: {e}")
            return None
    
    # ==================== ASS 生成 ====================
    
    def _save_ass(self, segments: List[Dict], output_path: str):
        """保存 ASS 格式字幕"""
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("[Script Info]\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 1080\n")
            f.write("PlayResY: 1920\n")
            f.write("ScaledBorderAndShadow: yes\n")
            f.write("\n")
            
            # Styles
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write("Style: Default, Arial, 48, &H00FFFFFF, &H000000FF, &H00000000, &H00000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 3, 0, 2, 10, 10, 10, 1\n")
            f.write("Style: Passion, Arial, 56, &H000000FF, &H000000FF, &H00000000, &H00000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 3, 0, 2, 10, 10, 10, 1\n")
            f.write("Style: Excited, Arial, 52, &H0000DDFF, &H0000DDFF, &H00000000, &H00000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 3, 0, 2, 10, 10, 10, 1\n")
            f.write("\n")
            
            # Events
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            for seg in segments:
                start = self._format_ass_time(seg['start'])
                end = self._format_ass_time(seg['end'])
                text = seg['text'].strip().replace('\n', '\\N')
                if text:
                    # TODO: 根据情感分析选择样式
                    style = "Default"
                    f.write(f"Dialogue: 0,{start},{end},{style},,0,0,0,,{text}\n")
    
    def _format_ass_time(self, seconds: float) -> str:
        """ASS 时间格式: H:MM:SS.CC"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)  # centiseconds
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# ==================== 便捷函数 ====================

def extract_subtitle(
    video_path: str, 
    output_dir: str = None,
    prefer_lang: str = None
) -> Optional[str]:
    """
    从视频智能提取字幕（便捷函数）
    
    优先级：
    1. 外挂字幕文件
    2. 内嵌软字幕
    3. WhisperX 转录
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        prefer_lang: 首选语言
    
    Returns:
        ASS 字幕文件路径，失败返回 None
    """
    extractor = SubtitleExtractor()
    return extractor.extract_smart(video_path, output_dir, prefer_lang)


def extract_word_timestamps(
    video_path: str,
    output_dir: str = None
) -> Optional[List[Dict]]:
    """
    提取词级时间戳数据（用于 Animated Caption）
    
    使用 WhisperX 转录 + 对齐流程
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录（可选，用于保存中间文件）
    
    Returns:
        词级数据列表: [{"word": "hello", "start": 0.0, "end": 0.5}, ...]
        失败返回 None
    """
    extractor = SubtitleExtractor()
    
    # 检查 WhisperX
    if not extractor._check_whisperx():
        logger.warning("[词级时间戳] WhisperX 不可用")
        return None
    
    # 加载模型
    if not extractor._load_model():
        return None
    
    audio_path = None
    try:
        import whisperx
        
        # 提取音频
        audio_path = extractor._extract_audio(video_path)
        if audio_path is None:
            return None
        
        # 1. 转录
        logger.info("[词级时间戳] 开始转录...")
        result = extractor.model.transcribe(
            audio_path, 
            batch_size=16,
        )
        
        segments = result.get('segments', [])
        detected_lang = result.get('language', 'unknown')
        
        if not segments:
            logger.warning("[词级时间戳] 未检测到语音")
            return None
        
        logger.info(f"[词级时间戳] 检测到语言: {detected_lang}, 片段数: {len(segments)}")
        
        # 2. 对齐时间戳（词级时间戳在对齐后才有）
        try:
            logger.info("[词级时间戳] 对齐时间戳...")
            align_model, align_metadata = whisperx.load_align_model(
                language_code=detected_lang, 
                device=extractor.device
            )
            result = whisperx.align(
                segments, 
                align_model, 
                align_metadata, 
                audio_path, 
                extractor.device,
                return_char_alignments=False  # 返回词级对齐
            )
            segments = result.get('segments', segments)
            logger.info("[词级时间戳] 对齐完成")
        except Exception as e:
            logger.warning(f"[词级时间戳] 对齐失败，使用原始时间戳: {e}")
        
        # 3. 提取词级数据
        words = []
        for segment in segments:
            segment_words = segment.get('words', [])
            for word_data in segment_words:
                word = word_data.get('word', '').strip()
                if word:
                    words.append({
                        'word': word,
                        'start': round(word_data.get('start', 0), 3),
                        'end': round(word_data.get('end', 0), 3),
                        'confidence': round(word_data.get('probability', word_data.get('confidence', 1.0)), 3),
                    })
        
        logger.info(f"[词级时间戳] 提取完成: {len(words)} 个词")
        return words
        
    except Exception as e:
        logger.error(f"[词级时间戳] 提取失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
