"""
布局计算模块 - 参考 PyCaps Layout 模块
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from .document import Document, Segment, Line, Word


@dataclass
class LayoutOptions:
    """布局选项"""
    max_width_ratio: float = 0.85  # 最大宽度比例（相对于视频宽度）
    max_lines: int = 2  # 每段最大行数
    min_chars_per_line: int = 8   # 每行最小字符数（大字体）
    max_chars_per_line: int = 20  # 每行最大字符数（大字体，自动换行）
    line_spacing: int = 10  # 行间距（像素）
    vertical_align: str = 'bottom'  # 垂直对齐：top, center, bottom
    margin_bottom: int = 80  # 底部边距（像素）
    margin_horizontal: int = 40  # 水平边距（像素）


class LineSplitter:
    """行分割器 - 将词分割成行"""
    
    def __init__(self, options: LayoutOptions = None):
        self.options = options or LayoutOptions()
    
    def split(self, document: Document) -> Document:
        """重新分割文档中的行"""
        new_segments = []
        
        for segment in document.segments:
            new_lines = self._split_segment(segment)
            new_segments.append(Segment(lines=new_lines, tags=segment.tags))
        
        return Document(segments=new_segments)
    
    def _split_segment(self, segment: Segment) -> List[Line]:
        """分割段落为行"""
        words = segment.words.copy()
        lines = []
        current_words = []
        current_chars = 0
        
        for word in words:
            word_chars = len(word.text)
            space_chars = 1 if current_words else 0
            
            if current_chars + space_chars + word_chars > self.options.max_chars_per_line:
                if current_words:
                    lines.append(Line(words=current_words))
                current_words = [word]
                current_chars = word_chars
            else:
                current_words.append(word)
                current_chars += space_chars + word_chars
        
        if current_words:
            lines.append(Line(words=current_words))
        
        # 设置 segment 引用
        for line in lines:
            line._segment = segment
        
        return lines


class PositionsCalculator:
    """位置计算器 - 计算每行的显示位置"""
    
    def __init__(self, video_width: int = 1080, video_height: int = 1920, 
                 options: LayoutOptions = None):
        self.video_width = video_width
        self.video_height = video_height
        self.options = options or LayoutOptions()
    
    def calculate(self, document: Document) -> dict:
        """
        计算所有行的位置
        
        Returns:
            dict: {line_id: (x, y, width, height)}
        """
        positions = {}
        
        for line in document.lines:
            line_id = id(line)
            x, y, width, height = self._calculate_line_position(line)
            positions[line_id] = {
                'x': x,
                'y': y,
                'width': width,
                'height': height,
            }
        
        return positions
    
    def _calculate_line_position(self, line: Line) -> Tuple[int, int, int, int]:
        """计算单行位置"""
        # 计算行宽度（基于词数估算）
        word_count = len(line.words)
        avg_char_width = 30  # 平均字符宽度（像素）
        text_width = len(line.text) * avg_char_width
        
        # 限制最大宽度
        max_width = int(self.video_width * self.options.max_width_ratio)
        width = min(text_width + 40, max_width)  # 加 padding
        height = 60  # 固定行高
        
        # 计算水平位置（居中）
        x = (self.video_width - width) // 2
        
        # 计算垂直位置
        if self.options.vertical_align == 'bottom':
            y = self.video_height - self.options.margin_bottom - height
        elif self.options.vertical_align == 'center':
            y = (self.video_height - height) // 2
        else:  # top
            y = self.options.margin_bottom
        
        return x, y, width, height


class WordSizeCalculator:
    """词尺寸计算器"""
    
    def __init__(self, font_size: int = 24):
        self.font_size = font_size
        # 字符宽度估算（中英文混合）
        self.char_width_ratio = 0.6  # 相对于 font_size
    
    def calculate_word_width(self, word: Word) -> int:
        """计算单个词的宽度"""
        text = word.text
        # 简化估算：中文字符宽度 = font_size，英文字符宽度 = font_size * 0.6
        width = 0
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                width += self.font_size
            else:
                width += self.font_size * self.char_width_ratio
        return int(width) + 16  # 加 padding
    
    def calculate_line_width(self, line: Line) -> int:
        """计算行宽度"""
        total_width = 0
        for i, word in enumerate(line.words):
            total_width += self.calculate_word_width(word)
            if i > 0:
                total_width += 8  # 词间距
        return total_width
