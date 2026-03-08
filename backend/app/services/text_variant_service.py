# backend/app/services/text_variant_service.py
"""
文案变体服务 - Spintax 旋转和 AI 改写
"""
import random
import re
import json
from typing import Dict, List, Optional
from loguru import logger

class SpintaxEngine:
    """Spintax 文本旋转引擎"""
    
    @staticmethod
    def spin(text: str, seed: int = None) -> str:
        """
        解析并旋转 Spintax 文本
        格式: {选项1|选项2|选项3}
        
        示例:
        "这是一个{精彩|绝妙|震撼}的{视频|短片}！"
        → "这是一个精彩的短片！"
        """
        if seed is not None:
            random.seed(seed)
        
        def replace_spin(match):
            options = match.group(1).split('|')
            return random.choice(options)
        
        # 递归处理嵌套的 Spintax
        while '{' in text:
            new_text = re.sub(r'\{([^{}]+)\}', replace_spin, text)
            if new_text == text:
                break
            text = new_text
        
        return text
    
    @staticmethod
    def generate_variants(text: str, count: int = 10) -> List[str]:
        """生成多个 Spintax 变体"""
        variants = []
        for i in range(count):
            variant = SpintaxEngine.spin(text, seed=i)
            variants.append(variant)
        return list(set(variants))  # 去重


class TextVariantEngine:
    """文案变体引擎"""
    
    # 预定义的 Spintax 模板
    TEMPLATES = {
        'title': {
            'sports_highlight': "{精彩|绝妙|震撼|疯狂|史诗}的{进球|射门|扣篮|得分|瞬间}！{必看|收藏|转发}",
            'sports_news': "{今天|刚刚}发生的{精彩|重磅}体育{新闻|事件}，{你绝对不能错过|必看}",
            'call_to_action': "点击{链接|下方}观看{完整|高清}{比赛|视频}！",
        },
        'description': {
            'sports_highlight': """
{今天给大家带来|分享一个}{精彩|绝妙}的{体育|足球|篮球}瞬间！
{这个|本场}{进球|得分}太{精彩|震撼}了！
{订阅|关注|点赞}不迷路，{每天|每周}更新更多{精彩|体育}内容！
            """.strip(),
            'sports_news': """
{最新|刚刚}体育{新闻|资讯}！
{这个|本场}{比赛|赛事}{精彩|激烈}程度{超乎想象|令人惊叹}！
{订阅|关注}获取更多{体育|赛事}{资讯|新闻}！
            """.strip(),
        },
        'tags': {
            'baseball': ["#棒球", "#MLB", "#全垒打", "#精彩瞬间", "#体育", "#Baseball"],
            'basketball': ["#篮球", "#NBA", "#扣篮", "#精彩瞬间", "#体育", "#Basketball"],
            'football': ["#足球", "#英超", "#进球", "#精彩瞬间", "#体育", "#Football"],
            'hockey': ["#冰球", "#NHL", "#进球", "#精彩瞬间", "#体育", "#Hockey"],
            'general': ["#体育", "#精彩瞬间", "#必看", "#运动", "#Sports"],
        }
    }
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.spintax = SpintaxEngine()
    
    def generate_title_variants(
        self, 
        original_title: str,
        category: str = 'sports_highlight',
        count: int = 10
    ) -> List[Dict]:
        """生成标题变体"""
        variants = []
        
        # 使用模板生成
        if category in self.TEMPLATES['title']:
            template = self.TEMPLATES['title'][category]
            for i in range(count):
                title = self.spintax.spin(template, seed=i)
                variants.append({
                    'index': i + 1,
                    'title': title,
                    'source': 'template'
                })
        
        # 使用原标题生成变体（添加前缀/后缀）
        prefixes = ["🔥", "⚡", "🎯", "💪", "🏆", "必看！", "精彩！", "震撼！"]
        suffixes = ["！", "#体育", "#必看", "👍", "（完整版）"]
        
        for i in range(min(count, len(prefixes))):
            variant = f"{prefixes[i % len(prefixes)]}{original_title}"
            variants.append({
                'index': len(variants) + 1,
                'title': variant[:100],  # 限制长度
                'source': 'prefix'
            })
        
        return variants[:count]
    
    def generate_description_variants(
        self,
        original_description: str,
        category: str = 'sports_highlight',
        count: int = 5
    ) -> List[Dict]:
        """生成描述变体"""
        variants = []
        
        # 使用模板生成
        if category in self.TEMPLATES['description']:
            template = self.TEMPLATES['description'][category]
            for i in range(count):
                description = self.spintax.spin(template, seed=i)
                variants.append({
                    'index': i + 1,
                    'description': description,
                    'source': 'template'
                })
        
        return variants
    
    def generate_tag_variants(
        self,
        sport_type: str = 'general',
        count: int = 5
    ) -> List[List[str]]:
        """生成标签变体"""
        base_tags = self.TEMPLATES['tags'].get(sport_type, self.TEMPLATES['tags']['general'])
        
        variants = []
        for i in range(count):
            # 随机选择 3-5 个标签
            num_tags = random.randint(3, min(5, len(base_tags)))
            selected = random.sample(base_tags, num_tags)
            variants.append(selected)
        
        return variants
    
    def generate_full_metadata(
        self,
        original_title: str,
        original_description: str,
        sport_type: str = 'general',
        count: int = 15
    ) -> List[Dict]:
        """生成完整的元数据变体包"""
        titles = self.generate_title_variants(original_title, 'sports_highlight', count)
        descriptions = self.generate_description_variants(original_description, 'sports_highlight', min(count, 5))
        tags = self.generate_tag_variants(sport_type, count)
        
        variants = []
        for i in range(count):
            variant = {
                'index': i + 1,
                'title': titles[i]['title'] if i < len(titles) else titles[0]['title'],
                'description': descriptions[i % len(descriptions)]['description'],
                'tags': tags[i] if i < len(tags) else tags[0],
            }
            variants.append(variant)
        
        return variants
