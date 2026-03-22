"""
字幕文档模型 - 参考 PyCaps 架构
"""

from dataclasses import dataclass, field
from typing import List, Set, Optional
from datetime import datetime


@dataclass
class TimeRange:
    """时间范围"""
    start: float
    end: float
    
    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class Word:
    """词"""
    text: str
    time: TimeRange
    confidence: float = 1.0
    tags: Set[str] = field(default_factory=set)
    
    def add_tag(self, tag: str):
        self.tags.add(tag)
    
    def has_tag(self, tag: str) -> bool:
        return tag in self.tags
    
    def to_dict(self) -> dict:
        return {
            'text': self.text,
            'start': self.time.start,
            'end': self.time.end,
            'confidence': self.confidence,
            'tags': list(self.tags),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Word':
        return cls(
            text=data['word'],
            time=TimeRange(data['start'], data['end']),
            confidence=data.get('confidence', 1.0),
            tags=set(data.get('tags', [])),
        )


@dataclass
class Line:
    """行（包含多个词）"""
    words: List[Word] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    
    @property
    def time(self) -> TimeRange:
        if not self.words:
            return TimeRange(0, 0)
        return TimeRange(
            self.words[0].time.start,
            self.words[-1].time.end
        )
    
    @property
    def text(self) -> str:
        return ' '.join(w.text for w in self.words)
    
    def add_tag(self, tag: str):
        self.tags.add(tag)
    
    def get_segment(self) -> 'Segment':
        """获取所属 segment（由 Segment 设置）"""
        return self._segment if hasattr(self, '_segment') else None


@dataclass  
class Segment:
    """段落（包含多行，由停顿分隔）"""
    lines: List[Line] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        # 设置 line 的 segment 引用
        for line in self.lines:
            line._segment = self
    
    @property
    def time(self) -> TimeRange:
        if not self.lines:
            return TimeRange(0, 0)
        return TimeRange(
            self.lines[0].time.start,
            self.lines[-1].time.end
        )
    
    @property
    def words(self) -> List[Word]:
        return [w for line in self.lines for w in line.words]
    
    def add_tag(self, tag: str):
        self.tags.add(tag)


@dataclass
class Document:
    """文档（包含所有段落）"""
    segments: List[Segment] = field(default_factory=list)
    
    @property
    def lines(self) -> List[Line]:
        return [line for segment in self.segments for line in segment.lines]
    
    @property
    def words(self) -> List[Word]:
        return [w for segment in self.segments for w in segment.words]
    
    @property
    def duration(self) -> float:
        if not self.segments:
            return 0
        return self.segments[-1].time.end
    
    @classmethod
    def from_words_data(cls, words_data: List[dict], pause_threshold: float = 0.5) -> 'Document':
        """
        从 WhisperX 词级数据创建文档
        
        Args:
            words_data: WhisperX 输出的词级数据
            pause_threshold: 停顿阈值（秒），超过此值分割段落
        """
        # 转换为 Word 对象
        words = [Word.from_dict(w) for w in words_data]
        
        # 按停顿分割段落
        segments = []
        current_words = []
        
        for i, word in enumerate(words):
            if current_words:
                prev_word = current_words[-1]
                pause = word.time.start - prev_word.time.end
                
                if pause > pause_threshold:
                    # 创建新段落
                    segment = cls._create_segment_from_words(current_words)
                    segments.append(segment)
                    current_words = []
            
            current_words.append(word)
        
        # 添加最后一个段落
        if current_words:
            segment = cls._create_segment_from_words(current_words)
            segments.append(segment)
        
        return cls(segments=segments)
    
    @classmethod
    def _create_segment_from_words(cls, words: List[Word], max_chars_per_line: int = 40) -> Segment:
        """从词列表创建段落，按字符数分行"""
        lines = []
        current_line_words = []
        current_chars = 0
        
        for word in words:
            word_chars = len(word.text)
            
            if current_chars + word_chars + len(current_line_words) > max_chars_per_line:
                if current_line_words:
                    lines.append(Line(words=current_line_words))
                current_line_words = [word]
                current_chars = word_chars
            else:
                current_line_words.append(word)
                current_chars += word_chars
        
        if current_line_words:
            lines.append(Line(words=current_line_words))
        
        return Segment(lines=lines)
    
    def to_dict(self) -> dict:
        return {
            'segments': [
                {
                    'lines': [
                        {
                            'words': [w.to_dict() for w in line.words],
                            'tags': list(line.tags),
                        }
                        for line in segment.lines
                    ],
                    'tags': list(segment.tags),
                }
                for segment in self.segments
            ]
        }
