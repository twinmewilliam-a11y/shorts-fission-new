"""
字幕翻译服务

使用 OpenRouter API (google/gemini-2.5-flash-lite) 翻译字幕
"""

import os
import logging
import httpx
from typing import List, Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 显式加载 .env 文件（Celery Worker 独立进程需要）
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class TranslationConfig:
    """翻译配置"""
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "google/gemini-2.5-flash-lite"
    
    # 支持的目标语言
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'zh': 'Chinese',
        'auto': 'Auto (same as source)'
    }


class SubtitleTranslator:
    """字幕翻译器"""
    
    # API 配置 - 必须从环境变量读取
    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, config: Optional[TranslationConfig] = None):
        if config is None:
            # 从环境变量读取配置（必须设置 OPENROUTER_API_KEY）
            api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
            base_url = os.getenv('OPENROUTER_BASE_URL') or self.DEFAULT_BASE_URL
            
            if not api_key:
                raise ValueError("必须设置环境变量 OPENROUTER_API_KEY 或 OPENAI_API_KEY")
            
            config = TranslationConfig(
                api_key=api_key,
                base_url=base_url
            )
        
        self.config = config
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def translate_words(
        self,
        words: List[Dict],
        target_language: str,
        source_language: Optional[str] = None
    ) -> List[Dict]:
        """
        翻译词级数据，保持时间戳不变
        
        Args:
            words: 词级数据列表 [{'word': '你好', 'start': 0.0, 'end': 0.5}, ...]
            target_language: 目标语言 ('en', 'zh')
            source_language: 源语言（可选，如果不提供会自动检测）
        
        Returns:
            翻译后的词级数据，时间戳保持不变
        """
        if not words:
            return words
        
        # 如果目标语言是 auto，不翻译
        if target_language == 'auto':
            logger.info("[翻译] 目标语言为 auto，跳过翻译")
            return words
        
        # 提取所有词
        texts = [w['word'] for w in words]
        original_text = ' '.join(texts)
        
        logger.info(f"[翻译] 开始翻译 {len(words)} 个词，源语言: {source_language or 'auto'}, 目标语言: {target_language}")
        
        try:
            # 调用 OpenRouter API
            translated_text = await self._call_openrouter(
                original_text,
                target_language,
                source_language
            )
            
            if not translated_text:
                logger.warning("[翻译] 翻译返回空结果，使用原文")
                return words
            
            # 将翻译结果分割成词
            translated_words = self._split_translated_text(translated_text, len(words))
            
            # 保持时间戳，替换文字
            result = []
            for i, word in enumerate(words):
                new_word = word.copy()
                new_word['word'] = translated_words[i] if i < len(translated_words) else word['word']
                new_word['original_word'] = word['word']  # 保留原文
                result.append(new_word)
            
            logger.info(f"[翻译] 翻译完成，共 {len(result)} 个词")
            return result
            
        except Exception as e:
            logger.error(f"[翻译] 翻译失败: {e}")
            return words  # 失败时返回原文
    
    async def _call_openrouter(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Optional[str]:
        """
        调用 OpenRouter API 进行翻译
        
        Args:
            text: 要翻译的文本
            target_language: 目标语言
            source_language: 源语言（可选）
        
        Returns:
            翻译后的文本
        """
        language_names = {
            'en': 'English',
            'zh': 'Chinese (Simplified)',
            'ja': 'Japanese',
            'ko': 'Korean',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
        }
        
        target_name = language_names.get(target_language, target_language)
        
        # 构建翻译提示
        if source_language and source_language != 'auto':
            source_name = language_names.get(source_language, source_language)
            prompt = f"""Translate the following {source_name} text to {target_name}.
Keep the same number of words/segments as the original.
Only output the translated text, nothing else.

Original text:
{text}"""
        else:
            prompt = f"""Translate the following text to {target_name}.
Keep the same number of words/segments as the original.
Only output the translated text, nothing else.

Text:
{text}"""
        
        try:
            response = await self.client.post(
                f"{self.config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://shorts-fission.local",
                    "X-Title": "Shorts Fission"
                },
                json={
                    "model": self.config.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            )
            
            if response.status_code != 200:
                logger.error(f"[翻译] API 错误: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            translated_text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return translated_text.strip()
            
        except Exception as e:
            logger.error(f"[翻译] API 调用异常: {e}")
            return None
    
    def _split_translated_text(self, text: str, target_count: int) -> List[str]:
        """
        将翻译后的文本分割成指定数量的词
        
        Args:
            text: 翻译后的文本
            target_count: 目标词数
        
        Returns:
            分割后的词列表
        """
        # 简单分割：按空格分割
        words = text.split()
        
        # 如果词数不够，用空字符串填充
        while len(words) < target_count:
            words.append('')
        
        # 如果词数太多，合并多余的词
        if len(words) > target_count:
            # 将多余的词合并到最后一个
            merged = ' '.join(words[target_count-1:])
            words = words[:target_count-1] + [merged]
        
        return words[:target_count]
    
    def detect_language(self, words: List[Dict]) -> str:
        """
        检测字幕语言
        
        Args:
            words: 词级数据
        
        Returns:
            语言代码 ('en', 'zh', 'ja', etc.)
        """
        # 简单的语言检测：检查是否有中文字符
        text = ' '.join([w['word'] for w in words])
        
        # 检查中文字符
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if chinese_chars > len(text) * 0.3:
            return 'zh'
        
        # 检查日文字符
        japanese_chars = sum(1 for c in text if '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
        if japanese_chars > len(text) * 0.3:
            return 'ja'
        
        # 检查韩文字符
        korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7af')
        if korean_chars > len(text) * 0.3:
            return 'ko'
        
        # 默认为英文
        return 'en'
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()


# 便捷函数
async def translate_subtitle(
    words: List[Dict],
    target_language: str,
    source_language: Optional[str] = None
) -> List[Dict]:
    """
    翻译字幕的便捷函数
    
    Args:
        words: 词级数据
        target_language: 目标语言 ('en', 'zh', 'auto')
        source_language: 源语言（可选）
    
    Returns:
        翻译后的词级数据
    """
    if target_language == 'auto':
        return words
    
    try:
        translator = SubtitleTranslator()
        result = await translator.translate_words(words, target_language, source_language)
        await translator.close()
        return result
    except Exception as e:
        logger.error(f"[翻译] 翻译失败: {e}")
        return words
