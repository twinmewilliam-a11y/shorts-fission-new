"""
标签系统 - 参考 PyCaps Tagger 模块
"""

from typing import List, Set, Optional, Callable
from abc import ABC, abstractmethod
from .document import Document, Segment, Line, Word


class Tagger(ABC):
    """标签器基类"""
    
    @abstractmethod
    def tag(self, document: Document) -> Document:
        """为文档添加标签"""
        pass


class StructureTagger(Tagger):
    """
    结构标签器 - 添加结构化标签
    
    添加的标签：
    - first-word-in-line: 行首词
    - last-word-in-line: 行尾词
    - first-line-in-segment: 段落首行
    - last-line-in-segment: 段落尾行
    - single-word-line: 单词行
    """
    
    def tag(self, document: Document) -> Document:
        """添加结构标签"""
        for segment in document.segments:
            self._tag_segment(segment)
        return document
    
    def _tag_segment(self, segment: Segment):
        """为段落添加标签"""
        if not segment.lines:
            return
        
        # 标记首行和尾行
        first_line = segment.lines[0]
        last_line = segment.lines[-1]
        
        first_line.add_tag('first-line-in-segment')
        last_line.add_tag('last-line-in-segment')
        
        if first_line is last_line:
            first_line.add_tag('single-line-segment')
        
        # 为每行添加标签
        for line in segment.lines:
            self._tag_line(line)
    
    def _tag_line(self, line: Line):
        """为行添加标签"""
        if not line.words:
            return
        
        # 标记首词和尾词
        first_word = line.words[0]
        last_word = line.words[-1]
        
        first_word.add_tag('first-word-in-line')
        last_word.add_tag('last-word-in-line')
        
        # 单词行
        if len(line.words) == 1:
            first_word.add_tag('single-word-line')
        
        # 标记所有词
        for word in line.words:
            word.add_tag('word')


class SemanticTagger(Tagger):
    """
    语义标签器 - 添加语义标签（可扩展）
    
    内置规则：
    - 数字: number
    - 大写词: uppercase
    - 感叹词: exclamation
    
    可扩展：
    - 品牌词库
    - 行业术语
    - AI 语义分析
    """
    
    def __init__(self, 
                 custom_word_lists: dict = None,
                 enable_ai: bool = False):
        """
        Args:
            custom_word_lists: 自定义词库 {tag_name: [word_list]}
            enable_ai: 是否启用 AI 语义分析
        """
        self.custom_word_lists = custom_word_lists or {}
        self.enable_ai = enable_ai
    
    def tag(self, document: Document) -> Document:
        """添加语义标签"""
        for word in document.words:
            self._tag_word(word)
        
        # 应用自定义词库
        for tag_name, word_list in self.custom_word_lists.items():
            self._apply_word_list(document, tag_name, word_list)
        
        # AI 语义分析（可选）
        if self.enable_ai:
            self._apply_ai_tagging(document)
        
        return document
    
    def _tag_word(self, word: Word):
        """为词添加语义标签"""
        text = word.text
        
        # 数字
        if any(c.isdigit() for c in text):
            word.add_tag('number')
        
        # 全大写
        if text.isupper() and len(text) > 1:
            word.add_tag('uppercase')
        
        # 感叹词
        if text in ['WOW', 'OMG', 'YES', 'NO', 'HEY', 'WOW!', 'YES!']:
            word.add_tag('exclamation')
        
        # 问号结尾
        if text.endswith('?'):
            word.add_tag('question')
        
        # 感叹号结尾
        if text.endswith('!'):
            word.add_tag('emphasis')
    
    def _apply_word_list(self, document: Document, tag_name: str, word_list: List[str]):
        """应用自定义词库"""
        word_set = set(w.lower() for w in word_list)
        
        for word in document.words:
            if word.text.lower() in word_set:
                word.add_tag(tag_name)
    
    def _apply_ai_tagging(self, document: Document):
        """AI 语义分析（预留接口）"""
        # TODO: 接入 LLM 进行语义分析
        # 例如：识别强调词、情感词、关键词等
        pass


class TagCondition:
    """标签条件 - 用于筛选特定标签的词"""
    
    def __init__(self, tags: Set[str] = None, exclude_tags: Set[str] = None):
        self.tags = tags or set()
        self.exclude_tags = exclude_tags or set()
    
    def matches(self, word: Word) -> bool:
        """检查词是否匹配条件"""
        # 必须包含所有指定标签
        if self.tags and not self.tags.issubset(word.tags):
            return False
        
        # 不能包含排除标签
        if self.exclude_tags and self.exclude_tags.intersection(word.tags):
            return False
        
        return True
    
    def filter_words(self, words: List[Word]) -> List[Word]:
        """筛选匹配的词"""
        return [w for w in words if self.matches(w)]
