"""
字幕处理流程 - 整合布局、标签、渲染
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .document import Document, Word, Line, Segment
from .layout import LineSplitter, PositionsCalculator, WordSizeCalculator, LayoutOptions
from .tagger import StructureTagger, SemanticTagger

logger = logging.getLogger(__name__)


@dataclass
class SubtitleConfig:
    """字幕配置"""
    template: str = 'pop_highlight'
    position: str = 'bottom_center'
    font_size: int = 56  # 放大1倍：24 → 56
    video_width: int = 1080
    video_height: int = 1920
    max_chars_per_line: int = 20  # 大字体需要更少的字符/行
    pause_threshold: float = 0.5  # 段落分割阈值


class SubtitleProcessor:
    """
    字幕处理器 - 整合完整流程
    
    流程：
    1. 从 WhisperX 数据创建 Document
    2. 布局计算（分行、位置）
    3. 标签添加（结构标签、语义标签）
    4. 输出配置文件给 Remotion
    """
    
    def __init__(self, config: SubtitleConfig = None):
        self.config = config or SubtitleConfig()
        
        # 布局选项
        self.layout_options = LayoutOptions(
            max_chars_per_line=config.max_chars_per_line if config else 40,
            vertical_align=self._get_vertical_align(config.position if config else 'bottom_center'),
        )
        
        # 初始化处理器
        self.line_splitter = LineSplitter(self.layout_options)
        self.structure_tagger = StructureTagger()
        self.semantic_tagger = SemanticTagger()
    
    def _get_vertical_align(self, position: str) -> str:
        """将位置映射为垂直对齐"""
        mapping = {
            'bottom_center': 'bottom',
            'bottom_left': 'bottom',
            'bottom_right': 'bottom',
            'center': 'center',
            'top_center': 'top',
        }
        return mapping.get(position, 'bottom')
    
    def process(self, words_data: List[dict]) -> Dict[str, Any]:
        """
        处理字幕数据
        
        Args:
            words_data: WhisperX 输出的词级数据
        
        Returns:
            dict: 处理后的字幕配置，用于 Remotion
        """
        logger.info(f"[SubtitleProcessor] 开始处理 {len(words_data)} 个词")
        
        # 1. 创建 Document
        document = Document.from_words_data(
            words_data, 
            pause_threshold=self.config.pause_threshold
        )
        logger.info(f"[SubtitleProcessor] 创建文档: {len(document.segments)} 段, {len(document.lines)} 行")
        
        # 2. 布局分割（重新分行）
        document = self.line_splitter.split(document)
        logger.info(f"[SubtitleProcessor] 布局分割完成: {len(document.lines)} 行")
        
        # 3. 添加结构标签
        document = self.structure_tagger.tag(document)
        logger.info(f"[SubtitleProcessor] 结构标签完成")
        
        # 4. 添加语义标签
        document = self.semantic_tagger.tag(document)
        logger.info(f"[SubtitleProcessor] 语义标签完成")
        
        # 5. 计算位置
        positions_calculator = PositionsCalculator(
            video_width=self.config.video_width,
            video_height=self.config.video_height,
            options=self.layout_options,
        )
        positions = positions_calculator.calculate(document)
        
        # 6. 生成输出配置
        output = self._generate_output(document, positions)
        
        logger.info(f"[SubtitleProcessor] 处理完成")
        return output
    
    def _generate_output(self, document: Document, positions: dict) -> Dict[str, Any]:
        """生成 Remotion 所需的配置"""
        # 转换为 Remotion 格式
        lines_data = []
        
        for i, line in enumerate(document.lines):
            line_data = {
                'id': i,
                'text': line.text,
                'start': line.time.start,
                'end': line.time.end,
                'words': [w.to_dict() for w in line.words],
                'tags': list(line.tags),
                'position': positions.get(id(line), {}),
            }
            lines_data.append(line_data)
        
        return {
            'config': {
                'template': self.config.template,
                'position': self.config.position,
                'fontSize': self.config.font_size,
                'videoWidth': self.config.video_width,
                'videoHeight': self.config.video_height,
            },
            'document': {
                'segments': [
                    {
                        'lines': [
                            {'id': i, 'tags': list(line.tags)}
                            for i, line in enumerate(document.lines)
                            if line in segment.lines
                        ],
                        'tags': list(segment.tags),
                    }
                    for segment in document.segments
                ],
            },
            'lines': lines_data,
            'words': [w.to_dict() for w in document.words],
        }
    
    def save_config(self, output: Dict[str, Any], output_path: str):
        """保存配置文件"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[SubtitleProcessor] 配置已保存: {output_path}")


# 便捷函数
def process_subtitle(words_data: List[dict], 
                     template: str = 'pop_highlight',
                     position: str = 'bottom_center',
                     font_size: int = 56) -> Dict[str, Any]:  # 放大1倍：24 → 56
    """
    处理字幕数据
    
    Args:
        words_data: WhisperX 词级数据
        template: 模板名称
        position: 位置
        font_size: 字体大小
    
    Returns:
        dict: 处理后的配置
    """
    config = SubtitleConfig(
        template=template,
        position=position,
        font_size=font_size,
    )
    processor = SubtitleProcessor(config)
    return processor.process(words_data)
