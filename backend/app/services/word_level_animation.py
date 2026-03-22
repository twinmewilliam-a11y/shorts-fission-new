# backend/app/services/word_level_animation.py
"""
词级动画引擎 v3.0 - Animated Caption

基于调研结果实现的 3 种基础动画模板：
1. pop_highlight - MrBeast 风格，当前词放大+黄色高亮
2. karaoke_flow - 卡拉OK风格，逐字变色
3. hype_gaming - 电竞风格，荧光色+发光+抖动

技术方案：ASS 硬烧（延续之前讨论的策略）
- 使用 \t() 标签实现渐变动画
- 使用 \c 标签实现颜色切换
- 使用 \fscx/\fscy 实现缩放
- 使用多层 Dialogue 实现词级高亮

Created: 2026-03-22
Version: 3.0
Author: T.W (Twin William)
"""
import os
import re
import json
import random
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from loguru import logger


# ==================== 动画模板定义 ====================

ANIMATION_TEMPLATES = {
    # PyCaps 12 个预设模板
    'minimalist': {
        'name': '极简风格',
        'name_en': 'Minimalist',
        'description': '白色无背景，极简设计',
        'scene': ['lifestyle', 'vlog', 'tutorial'],
        'style': {
            'font': 'Helvetica Neue',
            'font_size_base': 96,
            'primary_color': '&H00FFFFFF',
            'outline_color': '&H30000000',
            'outline_width': 2,
            'bold': False,
        },
        'animation': {'type': 'fade', 'fade_in_ms': 150, 'fade_out_ms': 150},
        'performance': 'high',
    },
    'default': {
        'name': '默认风格',
        'name_en': 'Default',
        'description': '经典字幕效果，黑色半透明背景',
        'scene': ['general', 'entertainment'],
        'style': {
            'font': 'Helvetica Neue',
            'font_size_base': 100,
            'primary_color': '&H00FFFFFF',
            'outline_color': '&H00000000',
            'outline_width': 3,
            'bold': True,
        },
        'animation': {'type': 'pop', 'scale': 1.1, 'fade_in_ms': 100, 'fade_out_ms': 100},
        'performance': 'high',
    },
    'classic': {
        'name': '经典风格',
        'name_en': 'Classic',
        'description': '衬线字体，优雅经典',
        'scene': ['documentary', 'education'],
        'style': {
            'font': 'Georgia',
            'font_size_base': 96,
            'primary_color': '&H00FFFFFF',
            'outline_color': '&H00000000',
            'outline_width': 4,
            'bold': False,
        },
        'animation': {'type': 'fade', 'fade_in_ms': 200, 'fade_out_ms': 200},
        'performance': 'high',
    },
    'neo_minimal': {
        'name': '新极简风格',
        'name_en': 'Neo Minimal',
        'description': '现代简约，浅色描边',
        'scene': ['lifestyle', 'fashion'],
        'style': {
            'font': 'SF Pro Display',
            'font_size_base': 104,
            'primary_color': '&H00FFFFFF',
            'outline_color': '&H20333333',
            'outline_width': 2,
            'bold': True,
        },
        'animation': {'type': 'fade', 'fade_in_ms': 100, 'fade_out_ms': 100},
        'performance': 'high',
    },
    'hype': {
        'name': '动感风格',
        'name_en': 'Hype',
        'description': '橙色高亮 + 缩放效果',
        'scene': ['sports', 'gaming', 'entertainment'],
        'style': {
            'font': 'Arial Black',
            'font_size_base': 108,
            'primary_color': '&H00FFFFFF',
            'highlight_color': '&H0000Ff76',
            'outline_color': '&H00000000',
            'outline_width': 4,
            'bold': True,
        },
        'animation': {'type': 'pop', 'scale': 1.15, 'fade_in_ms': 80, 'fade_out_ms': 80},
        'performance': 'medium',
    },
    'explosive': {
        'name': '爆炸风格',
        'name_en': 'Explosive',
        'description': '黄色爆炸效果，强力冲击',
        'scene': ['sports', 'gaming'],
        'style': {
            'font': 'Arial Black',
            'font_size_base': 112,
            'primary_color': '&H00FFFFFF',
            'highlight_color': '&H0000FFFF',
            'outline_color': '&H00000000',
            'outline_width': 5,
            'bold': True,
        },
        'animation': {'type': 'pop', 'scale': 1.2, 'fade_in_ms': 50, 'fade_out_ms': 100},
        'performance': 'medium',
    },
    'fast': {
        'name': '快速风格',
        'name_en': 'Fast',
        'description': 'Impact 字体，快速切换',
        'scene': ['sports', 'news'],
        'style': {
            'font': 'Impact',
            'font_size_base': 116,
            'primary_color': '&H00FFFFFF',
            'highlight_color': '&H00FFFF00',
            'outline_color': '&H00000000',
            'outline_width': 4,
            'bold': True,
        },
        'animation': {'type': 'pop', 'scale': 1.1, 'fade_in_ms': 50, 'fade_out_ms': 50},
        'performance': 'high',
    },
    'vibrant': {
        'name': '活力风格',
        'name_en': 'Vibrant',
        'description': '渐变背景，活力四射',
        'scene': ['music', 'dance', 'entertainment'],
        'style': {
            'font': 'Poppins',
            'font_size_base': 100,
            'primary_color': '&H00FFFFFF',
            'outline_color': '&H30333333',
            'outline_width': 3,
            'bold': True,
        },
        'animation': {'type': 'pop', 'scale': 1.1, 'fade_in_ms': 100, 'fade_out_ms': 100},
        'performance': 'medium',
    },
    'word_focus': {
        'name': '词焦点风格',
        'name_en': 'Word Focus',
        'description': '当前词绿色高亮',
        'scene': ['education', 'tutorial'],
        'style': {
            'font': 'Montserrat',
            'font_size_base': 96,
            'primary_color': '&H80FFFFFF',
            'highlight_color': '&H0000E600',
            'outline_color': '&H00000000',
            'outline_width': 3,
            'bold': True,
        },
        'animation': {'type': 'pop', 'scale': 1.15, 'fade_in_ms': 100, 'fade_out_ms': 100},
        'performance': 'high',
    },
    'line_focus': {
        'name': '行焦点风格',
        'name_en': 'Line Focus',
        'description': '整行高亮，清晰易读',
        'scene': ['news', 'education'],
        'style': {
            'font': 'Roboto',
            'font_size_base': 92,
            'primary_color': '&H00FFFFFF',
            'outline_color': '&H00000000',
            'outline_width': 3,
            'bold': True,
        },
        'animation': {'type': 'fade', 'fade_in_ms': 150, 'fade_out_ms': 150},
        'performance': 'high',
    },
    'retro_gaming': {
        'name': '复古游戏风格',
        'name_en': 'Retro Gaming',
        'description': '像素风，复古游戏效果',
        'scene': ['gaming', 'retro'],
        'style': {
            'font': 'Press Start 2P',
            'font_size_base': 64,
            'primary_color': '&H0000FF00',
            'highlight_color': '&H0000FFFF',
            'outline_color': '&H00008800',
            'outline_width': 2,
            'bold': False,
        },
        'animation': {'type': 'pop', 'scale': 1.2, 'fade_in_ms': 100, 'fade_out_ms': 100},
        'performance': 'high',
    },
    'model': {
        'name': '模特风格',
        'name_en': 'Model',
        'description': '高端斜体，优雅大气',
        'scene': ['fashion', 'lifestyle'],
        'style': {
            'font': 'Playfair Display',
            'font_size_base': 92,
            'primary_color': '&H00FFFFFF',
            'outline_color': '&H20000000',
            'outline_width': 2,
            'bold': False,
            'italic': True,
        },
        'animation': {'type': 'fade', 'fade_in_ms': 200, 'fade_out_ms': 200},
        'performance': 'high',
    },
}


# ==================== 位置配置 - 简化为 3 个，距边缘 300px ====================

POSITION_GRID = {
    'top_center': {'align': 8, 'margin_v': 300, 'name': '顶部居中 (距顶 300px)'},
    'center': {'align': 5, 'margin_v': 0, 'name': '中部居中'},
    'bottom_center': {'align': 2, 'margin_v': 300, 'name': '底部居中 (距底 300px)'},
    # 保留旧位置的兼容性
    'bottom_left': {'align': 1, 'margin_v': 300, 'margin_l': 40, 'name': '底部左'},
    'bottom_right': {'align': 3, 'margin_v': 300, 'margin_r': 40, 'name': '底部右'},
}


# ==================== 词级动画引擎 ====================

class WordLevelAnimationEngine:
    """词级动画引擎 v3.0"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.templates = ANIMATION_TEMPLATES
        self.positions = POSITION_GRID
        
    def generate_variant(
        self,
        words_data: List[Dict],
        output_ass_path: str,
        video_width: int = 1080,
        video_height: int = 1920,
        template_id: str = 'pop_highlight',
        position: str = 'bottom_center',
        seed: int = None
    ) -> Dict:
        """
        生成词级动画 ASS 字幕
        
        Args:
            words_data: WhisperX 词级数据 [{"word": "hello", "start": 0.0, "end": 0.5}, ...]
            output_ass_path: 输出 ASS 文件路径
            video_width: 视频宽度
            video_height: 视频高度
            template_id: 模板 ID
            position: 位置 ID
            seed: 随机种子
        
        Returns:
            {
                'success': True/False,
                'ass_path': 输出文件路径,
                'template': 模板信息,
                'word_count': 词数量,
                'error': 错误信息（失败时）
            }
        """
        if seed is not None:
            random.seed(seed)
        
        # 验证模板
        if template_id not in self.templates:
            return {
                'success': False,
                'error': f'Invalid template: {template_id}. Available: {list(self.templates.keys())}'
            }
        
        template = self.templates[template_id]
        
        # 验证数据
        if not words_data or len(words_data) == 0:
            return {
                'success': False,
                'error': 'Empty words_data'
            }
        
        # 随机化参数
        params = self._randomize_params(template, position)
        
        # 生成 ASS 内容
        ass_content = self._generate_ass(
            words_data, 
            params, 
            video_width, 
            video_height,
            template['animation']['type']
        )
        
        # 写入文件
        os.makedirs(os.path.dirname(output_ass_path), exist_ok=True)
        with open(output_ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        logger.info(f"[词级动画 v3.0] 模板: {template['name']}, 词数: {len(words_data)}, 输出: {output_ass_path}")
        
        return {
            'success': True,
            'ass_path': output_ass_path,
            'template_id': template_id,
            'template_name': template['name'],
            'word_count': len(words_data),
            'params': params,
        }
    
    def _randomize_params(self, template: Dict, position: str) -> Dict:
        """随机化参数"""
        params = template['style'].copy()
        
        # 字号随机
        font_size_base = params.get('font_size_base', 52)
        font_size_range = params.get('font_size_range', (-6, 10))
        params['font_size'] = font_size_base + random.randint(*font_size_range)
        
        # 位置
        pos_config = self.positions.get(position, self.positions['bottom_center'])
        params['alignment'] = pos_config['align']
        params['margin_v'] = pos_config.get('margin_v', 80)
        params['margin_l'] = pos_config.get('margin_l', 10)
        params['margin_r'] = pos_config.get('margin_r', 10)
        params['position_name'] = pos_config['name']
        
        # 动画参数
        params['animation'] = template['animation']
        
        return params
    
    def _generate_ass(
        self, 
        words_data: List[Dict], 
        params: Dict,
        video_width: int,
        video_height: int,
        animation_type: str
    ) -> str:
        """生成 ASS 字幕内容"""
        
        # Script Info
        script_info = f"""[Script Info]
Title: Word Level Animation v3.0 - {animation_type}
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

"""
        
        # Styles
        styles = self._build_styles(params)
        
        # Events - 根据动画类型生成
        if animation_type == 'pop':
            events = self._build_pop_events(words_data, params)
        elif animation_type == 'karaoke':
            events = self._build_karaoke_events(words_data, params)
        elif animation_type == 'hype':
            events = self._build_hype_events(words_data, params)
        else:
            events = self._build_pop_events(words_data, params)
        
        return script_info + styles + events
    
    def _build_styles(self, params: Dict) -> str:
        """构建样式定义"""
        font = params.get('font', 'Arial Black')
        font_size = params.get('font_size', 52)
        primary_color = params.get('primary_color', '&H00FFFFFF')
        outline_color = params.get('outline_color', '&H00000000')
        outline_width = params.get('outline_width', 5)
        shadow = params.get('shadow', 2)
        bold = -1 if params.get('bold', True) else 0
        blur = params.get('blur', 0)
        
        # 高亮样式颜色
        highlight_color = params.get('highlight_color', '&H0000FFFF')
        
        # 关键词样式（用于 hype 模式）
        keyword_scale = int(params.get('animation', {}).get('scale', 1.2) * 100)
        
        # 位置参数
        alignment = params.get('alignment', 2)
        margin_v = params.get('margin_v', 80)
        margin_l = params.get('margin_l', 10)
        margin_r = params.get('margin_r', 10)
        
        return f"""[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},{margin_l},{margin_r},{margin_v},1
Style: Highlight,{font},{font_size},{highlight_color},&H000000FF,{outline_color},&H80000000,{bold},0,0,0,115,115,0,0,1,{outline_width + 1},{shadow},{alignment},{margin_l},{margin_r},{margin_v},1
Style: Keyword,{font},{int(font_size * 1.1)},{params.get('highlight_color', '&H000000FF')},&H000000FF,{outline_color},&H80000000,{bold},0,0,0,{keyword_scale},{keyword_scale},0,0,1,{outline_width + 1},{shadow + 1},{alignment},{margin_l},{margin_r},{margin_v},1

"""
    
    def _build_pop_events(self, words_data: List[Dict], params: Dict) -> str:
        """
        构建 Pop Highlight 动画事件
        
        原理：
        - Layer 0: 基础层，整句显示，淡入淡出
        - Layer 1: 高亮层，逐词放大+变色
        """
        events = "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        
        animation = params.get('animation', {})
        fade_in = animation.get('fade_in_ms', 100)
        fade_out = animation.get('fade_out_ms', 100)
        scale = animation.get('scale', 1.15)
        duration_ms = animation.get('duration_ms', 150)
        
        # 按句子分组（以停顿 > 1 秒为分隔）
        sentences = self._group_words_into_sentences(words_data)
        
        for sentence in sentences:
            if not sentence:
                continue
            
            # 句子时间范围
            sentence_start = sentence[0]['start']
            sentence_end = sentence[-1]['end']
            sentence_text = ' '.join([w['word'] for w in sentence])
            
            # 基础层：整句显示
            start_time = self._format_ass_time(sentence_start)
            end_time = self._format_ass_time(sentence_end)
            fade_tag = f"{{\\fad({fade_in},{fade_out})}}"
            events += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{fade_tag}{sentence_text}\n"
            
            # 高亮层：逐词高亮
            for i, word in enumerate(sentence):
                word_start = self._format_ass_time(word['start'])
                word_end = self._format_ass_time(word['end'])
                
                # 构建高亮文本：当前词高亮，其他词保持原样
                highlighted_text = self._build_highlighted_text(sentence, i, scale)
                
                events += f"Dialogue: 1,{word_start},{word_end},Highlight,,0,0,0,,{highlighted_text}\n"
        
        return events
    
    def _build_karaoke_events(self, words_data: List[Dict], params: Dict) -> str:
        """
        构建 Karaoke 动画事件
        
        原理：
        - 使用 ASS \k 标签实现逐字变色
        - 已读词变亮，未读词半透明
        """
        events = "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        
        animation = params.get('animation', {})
        fade_in = animation.get('fade_in_ms', 100)
        fade_out = animation.get('fade_out_ms', 100)
        
        # 使用 ASS \k 标签实现卡拉OK效果
        # \k 接受的是十分之一秒 (centiseconds)
        
        sentences = self._group_words_into_sentences(words_data)
        
        for sentence in sentences:
            if not sentence:
                continue
            
            sentence_start = sentence[0]['start']
            sentence_end = sentence[-1]['end']
            
            # 构建 \k 标签序列
            karaoke_parts = []
            for word in sentence:
                # 计算词持续时间（十分之一秒）
                duration_cs = int((word['end'] - word['start']) * 100)
                karaoke_parts.append(f"{{\\k{duration_cs}}}{word['word']}")
            
            karaoke_text = ''.join(karaoke_parts)
            
            start_time = self._format_ass_time(sentence_start)
            end_time = self._format_ass_time(sentence_end)
            fade_tag = f"{{\\fad({fade_in},{fade_out})}}"
            
            events += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{fade_tag}{karaoke_text}\n"
        
        return events
    
    def _build_hype_events(self, words_data: List[Dict], params: Dict) -> str:
        """
        构建 Hype Gaming 动画事件
        
        原理：
        - Pop 基础效果
        - 关键词额外添加抖动效果
        - 发光效果 (\blur)
        """
        events = "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        
        animation = params.get('animation', {})
        fade_in = animation.get('fade_in_ms', 100)
        fade_out = animation.get('fade_out_ms', 100)
        scale = animation.get('scale', 1.2)
        shake_range = animation.get('shake_range', 3)
        shake_duration = animation.get('shake_duration_ms', 50)
        
        # 检测关键词（简单的长度/大小写启发式）
        keywords = self._detect_keywords(words_data)
        
        sentences = self._group_words_into_sentences(words_data)
        
        for sentence in sentences:
            if not sentence:
                continue
            
            sentence_start = sentence[0]['start']
            sentence_end = sentence[-1]['end']
            sentence_text = ' '.join([w['word'] for w in sentence])
            
            start_time = self._format_ass_time(sentence_start)
            end_time = self._format_ass_time(sentence_end)
            fade_tag = f"{{\\fad({fade_in},{fade_out})}}"
            
            # 基础层
            events += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{fade_tag}{sentence_text}\n"
            
            # 高亮层 + 抖动效果
            for i, word in enumerate(sentence):
                word_start = self._format_ass_time(word['start'])
                word_end = self._format_ass_time(word['end'])
                
                # 判断是否为关键词
                is_keyword = word['word'].lower() in [k.lower() for k in keywords]
                
                if is_keyword:
                    # 关键词：抖动 + 放大 + 发光
                    highlighted_text = self._build_hype_text(sentence, i, scale, shake_range)
                    events += f"Dialogue: 2,{word_start},{word_end},Keyword,,0,0,0,,{highlighted_text}\n"
                else:
                    # 普通词：仅高亮
                    highlighted_text = self._build_highlighted_text(sentence, i, scale)
                    events += f"Dialogue: 1,{word_start},{word_end},Highlight,,0,0,0,,{highlighted_text}\n"
        
        return events
    
    def _build_highlighted_text(self, sentence: List[Dict], highlight_index: int, scale: float = 1.15) -> str:
        """
        构建高亮文本
        
        当前词使用 \t 标签实现缩放动画
        """
        parts = []
        scale_percent = int(scale * 100)
        
        for i, word in enumerate(sentence):
            if i == highlight_index:
                # 高亮词：使用 \t 实现缩放动画
                # {\t(\fscx115\fscy115)}word{\r} - 放大后恢复
                parts.append(f"{{\\t(\\fscx{scale_percent}\\fscy{scale_percent})}}{word['word']}{{\\r}}")
            else:
                parts.append(word['word'])
        
        return ' '.join(parts)
    
    def _build_hype_text(self, sentence: List[Dict], highlight_index: int, scale: float, shake_range: int) -> str:
        """
        构建 Hype 模式文本（抖动效果）
        
        使用 \frx 实现抖动
        """
        parts = []
        scale_percent = int(scale * 100)
        
        for i, word in enumerate(sentence):
            if i == highlight_index:
                # 抖动 + 放大
                # {\t(\frx5)\t(\frx-5)\t(\frx5)\t(\fscx120\fscy120)}word{\r}
                shake_effect = f"{{\\t(\\frx{shake_range})\\t(\\frx-{shake_range})\\t(\\frx{shake_range})\\t(\\fscx{scale_percent}\\fscy{scale_percent})}}{word['word']}{{\\r}}"
                parts.append(shake_effect)
            else:
                parts.append(word['word'])
        
        return ' '.join(parts)
    
    def _detect_keywords(self, words_data: List[Dict]) -> List[str]:
        """
        检测关键词（简单启发式）
        
        规则：
        - 全大写词
        - 长度 > 6 的词
        - 感叹号前的词
        """
        keywords = []
        
        for i, word_data in enumerate(words_data):
            word = word_data['word']
            
            # 全大写
            if word.isupper() and len(word) > 2:
                keywords.append(word.lower())
            
            # 长词
            if len(word) > 6:
                keywords.append(word.lower())
            
            # 感叹号前
            if word.endswith('!') or word.endswith('!!'):
                keywords.append(word.rstrip('!').lower())
        
        # 限制数量（最多 3 个）
        return keywords[:3]
    
    def _group_words_into_sentences(self, words_data: List[Dict], pause_threshold: float = 1.0) -> List[List[Dict]]:
        """
        按停顿将词分组为句子
        
        Args:
            words_data: 词级数据
            pause_threshold: 停顿阈值（秒）
        
        Returns:
            句子列表，每个句子是词的列表
        """
        if not words_data:
            return []
        
        sentences = []
        current_sentence = [words_data[0]]
        
        for i in range(1, len(words_data)):
            prev_word = words_data[i - 1]
            curr_word = words_data[i]
            
            # 计算停顿时间
            pause = curr_word['start'] - prev_word['end']
            
            if pause > pause_threshold:
                # 停顿超过阈值，开始新句子
                sentences.append(current_sentence)
                current_sentence = [curr_word]
            else:
                current_sentence.append(curr_word)
        
        # 添加最后一个句子
        if current_sentence:
            sentences.append(current_sentence)
        
        return sentences
    
    def _format_ass_time(self, seconds: float) -> str:
        """
        格式化为 ASS 时间格式
        
        格式: H:MM:SS.cc (小时:分钟:秒.百分之一秒)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


# ==================== 便捷函数 ====================

def generate_word_level_animation(
    words_data: List[Dict],
    output_path: str,
    video_width: int = 1080,
    video_height: int = 1920,
    template_id: str = 'pop_highlight',
    position: str = 'bottom_center',
) -> Dict:
    """
    生成词级动画字幕（便捷函数）
    
    Args:
        words_data: WhisperX 词级数据
        output_path: 输出 ASS 文件路径
        video_width: 视频宽度
        video_height: 视频高度
        template_id: 模板 ID ('pop_highlight', 'karaoke_flow', 'hype_gaming')
        position: 位置 ('bottom_center', 'bottom_left', 'bottom_right', 'center', 'top_center')
    
    Returns:
        结果字典
    """
    engine = WordLevelAnimationEngine()
    return engine.generate_variant(
        words_data=words_data,
        output_ass_path=output_path,
        video_width=video_width,
        video_height=video_height,
        template_id=template_id,
        position=position,
    )


def get_available_templates() -> List[Dict]:
    """获取可用模板列表"""
    return [
        {
            'id': tid,
            'name': t['name'],
            'name_en': t['name_en'],
            'description': t['description'],
            'scene': t['scene'],
        }
        for tid, t in ANIMATION_TEMPLATES.items()
    ]


def get_available_positions() -> List[Dict]:
    """获取可用位置列表"""
    return [
        {
            'id': pid,
            'name': p['name'],
        }
        for pid, p in POSITION_GRID.items()
    ]


# ==================== 兼容包装函数 ====================

def generate_word_level_animation(
    words_data: List[Dict],
    output_path: str,
    video_width: int = 1080,
    video_height: int = 1920,
    template_id: str = 'pop_highlight',
    position: str = 'bottom_center',
    **kwargs
) -> Dict:
    """
    生成词级动画字幕（兼容包装函数）
    
    与 variant_engine.py 集成使用
    
    Args:
        words_data: WhisperX 词级数据 [{"word": "hello", "start": 0.0, "end": 0.5}, ...]
        output_path: 输出 ASS 文件路径
        video_width: 视频宽度
        video_height: 视频高度
        template_id: 模板 ID ('pop_highlight', 'karaoke_flow', 'hype_gaming')
        position: 位置 ('bottom_center', 'bottom_left', 'bottom_right', 'center', 'top_center')
        **kwargs: 额外参数（忽略）
    
    Returns:
        {
            'success': True/False,
            'ass_path': 输出文件路径,
            'template_id': 使用的模板,
            'word_count': 词数量,
            'error': 错误信息（失败时）
        }
    """
    engine = WordLevelAnimationEngine()
    return engine.generate_variant(
        words_data=words_data,
        output_ass_path=output_path,
        video_width=video_width,
        video_height=video_height,
        template_id=template_id,
        position=position,
    )


# ==================== 测试代码 ====================

if __name__ == '__main__':
    # 测试数据
    test_words = [
        {"word": "This", "start": 0.0, "end": 0.3},
        {"word": "is", "start": 0.3, "end": 0.5},
        {"word": "an", "start": 0.5, "end": 0.7},
        {"word": "AMAZING", "start": 0.7, "end": 1.2},
        {"word": "video", "start": 1.2, "end": 1.6},
        {"word": "!", "start": 1.6, "end": 1.7},
    ]
    
    engine = WordLevelAnimationEngine()
    
    # 测试三种模板
    for template_id in ['pop_highlight', 'karaoke_flow', 'hype_gaming']:
        output_path = f"/tmp/test_{template_id}.ass"
        result = engine.generate_variant(
            words_data=test_words,
            output_ass_path=output_path,
            template_id=template_id,
        )
        print(f"Template: {template_id}")
        print(f"  Success: {result['success']}")
        print(f"  Output: {result.get('ass_path')}")
        print()
