# shorts-fission Animated Caption 升级方案

> **创建日期**: 2026-03-21
> **创建者**: T.W (Twin William)
> **版本**: v1.0

---

## 执行摘要

本文档为 **shorts-fission** 项目的字幕系统升级提供完整的技术方案，目标是实现 **OpusClip 级别的 Animated Caption** 功能。

**核心目标**：
1. 动态字幕动画（词级高亮、弹出、淡入等）
2. 品牌模板系统（可自定义字体、颜色、动画）
3. AI 关键词标签（自动识别并高亮关键词）
4. 多语言支持（26+ 种语言）

---

## 1. OpusClip Animated Caption 核心特性

### 1.1 功能矩阵

| 特性 | OpusClip | shorts-fission 现状 | 升级目标 |
|------|----------|-------------------|---------|
| **字幕准确率** | 99%+ | ~90% (Whisper) | 95%+ |
| **词级动画** | ✅ | ❌ | ✅ P0 |
| **关键词高亮** | ✅ AI 自动 | ❌ | ✅ P0 |
| **动画模板** | 20+ 种 | 20 种 (静态) | 20+ 动态 |
| **品牌模板** | ✅ 自定义 | ❌ | ✅ P1 |
| **多语言** | 26+ | 10+ | 26+ |
| **Emoji 插入** | ✅ | ❌ | ✅ P2 |

### 1.2 OpusClip 字幕动画类型

```
1. 经典动画
   ├── Pop (弹出)
   ├── Fade In (淡入)
   ├── Slide (滑动)
   ├── Typewriter (打字机)
   └── Bounce (弹跳)

2. 高级效果
   ├── Word-by-word (逐词显示)
   ├── Karaoke (卡拉OK)
   ├── Highlight (高亮当前词)
   ├── Glow (发光)
   └── Shake (抖动)

3. 风格模板
   ├── Hype (动感/电竞风)
   ├── Minimalist (简约)
   ├── Netflix (电影感)
   ├── Gaming (游戏风)
   ├── News (新闻风)
   └── Social Media (社交媒体)
```

---

## 2. 技术方案对比

### 2.1 方案对比

| 方案 | 技术栈 | 优势 | 劣势 | 推荐度 |
|------|-------|------|------|-------|
| **方案 A: pycaps** | Python + CSS + Playwright | 开源、离线、模板系统 | 渲染慢、依赖浏览器 | ⭐⭐⭐ |
| **方案 B: Remotion** | React + CSS + FFmpeg | 生态强、动画丰富 | 学习曲线陡 | ⭐⭐⭐⭐ |
| **方案 C: 自研升级** | 现有架构 + ASS 增强 | 兼容现有系统 | 开发量大 | ⭐⭐⭐⭐⭐ |

### 2.2 推荐方案: **混合架构**

```
┌─────────────────────────────────────────────────────────────────┐
│              shorts-fission Animated Caption 架构               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: 转录层 (Transcription)                                │
│  ├── Whisper Large V3 (本地) - 95%+ 准确率                      │
│  ├── 词级时间戳 (word-level timestamps)                         │
│  └── 多说话人识别                                               │
│                                                                 │
│  Layer 2: AI 分析层 (Analysis)                                  │
│  ├── 关键词提取 (KeyBERT / LLM)                                 │
│  ├── 情感分析 (Emotion Detection)                               │
│  ├── 热词标签 (Trending Tags)                                   │
│  └── Emoji 建议                                                  │
│                                                                 │
│  Layer 3: 模板层 (Templates)                                    │
│  ├── 预设模板 (20+ styles)                                      │
│  ├── 品牌模板 (自定义字体/颜色)                                  │
│  ├── 动画模板 (Pop/Fade/Slide 等)                               │
│  └── 位置模板 (9:16/1:1/16:9)                                   │
│                                                                 │
│  Layer 4: 渲染层 (Rendering)                                    │
│  ├── ASS 增强 (词级动画)                                        │
│  ├── CSS 动画 (可选)                                            │
│  └── FFmpeg 烧录                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 详细实现方案

### 3.1 Phase 1: 词级时间戳 (P0)

**目标**: 实现词级别的字幕高亮

**实现方式**:

```python
# subtitle_service.py 升级

from whisper import Whisper
import json

class EnhancedSubtitleService:
    def __init__(self):
        self.model = Whisper("large-v3")
    
    def transcribe_with_word_timestamps(self, audio_path: str) -> dict:
        """转录并获取词级时间戳"""
        result = self.model.transcribe(
            audio_path,
            word_timestamps=True,  # 启用词级时间戳
            language="zh",  # 自动检测
        )
        
        # 构建词级字幕数据
        words = []
        for segment in result["segments"]:
            for word in segment.get("words", []):
                words.append({
                    "word": word["word"],
                    "start": word["start"],
                    "end": word["end"],
                    "confidence": word.get("probability", 1.0),
                })
        
        return {
            "text": result["text"],
            "segments": result["segments"],
            "words": words,  # 新增：词级数据
        }
```

**ASS 词级动画**:

```python
# text_layer_engine_v3.py

def generate_word_level_ass(words: list, template: dict) -> str:
    """生成词级动画 ASS 字幕"""
    
    ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H{color}&,&H000000FF,&H{outline}&,&H{shadow}&,{bold},0,0,0,100,100,0,0,1,{outline_width},0,2,10,10,50,1
Style: Highlight,{font},{size},&H{highlight_color}&,&H000000FF,&H{outline}&,&H{shadow}&,{bold},0,0,0,110,110,0,0,1,{outline_width},0,2,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(**template)
    
    # 按句子分组
    sentences = group_words_into_sentences(words)
    
    for sentence in sentences:
        # 基础字幕层（整句显示）
        base_text = " ".join([w["word"] for w in sentence])
        start_time = format_ass_time(sentence[0]["start"])
        end_time = format_ass_time(sentence[-1]["end"])
        
        # 生成高亮效果
        highlight_events = []
        for i, word in enumerate(sentence):
            word_start = format_ass_time(word["start"])
            word_end = format_ass_time(word["end"])
            
            # 构建高亮文本
            highlighted_text = build_highlighted_text(sentence, i)
            
            # 高亮层
            highlight_events.append(
                f"Dialogue: 1,{word_start},{word_end},Default,,0,0,0,,{highlighted_text}"
            )
        
        # 基础层
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{base_text}\n"
        
        # 高亮层
        for event in highlight_events:
            ass_content += event + "\n"
    
    return ass_content

def build_highlighted_text(sentence: list, highlight_index: int) -> str:
    """构建高亮文本 - 当前词高亮，其他词淡化"""
    parts = []
    for i, word in enumerate(sentence):
        if i == highlight_index:
            # 高亮词
            parts.append(f"{{\\c&H00FFFF&}}{word['word']}{{\\c&HFFFFFF&}}")
        else:
            # 普通词
            parts.append(word["word"])
    return " ".join(parts)
```

### 3.2 Phase 2: AI 关键词标签 (P0)

**目标**: 自动识别并高亮关键词

```python
# ai_keyword_tagger.py

from keybert import KeyBERT
import re

class AIKeywordTagger:
    def __init__(self):
        self.kw_model = KeyBERT()
        self.trending_words = self._load_trending_words()
        self.brand_words = []  # 品牌词库
    
    def tag_keywords(self, text: str, transcript_words: list) -> list:
        """识别并标记关键词"""
        tagged_words = []
        
        # 1. KeyBERT 提取关键词
        keywords = self.kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words=None,
            top_n=10
        )
        keyword_set = set([kw[0].lower() for kw in keywords])
        
        # 2. 热词匹配
        trending_matches = self._match_trending(text)
        
        # 3. 品牌词匹配
        brand_matches = self._match_brand(text)
        
        # 4. 为每个词打标签
        for word_data in transcript_words:
            word = word_data["word"].lower()
            tags = []
            
            # 关键词标签
            if word in keyword_set or any(word in kw for kw in keyword_set):
                tags.append("keyword")
            
            # 热词标签
            if word in trending_matches:
                tags.append("trending")
            
            # 品牌词标签
            if word in brand_matches:
                tags.append("brand")
            
            # 情感词标签
            emotion = self._detect_emotion(word)
            if emotion:
                tags.append(f"emotion:{emotion}")
            
            word_data["tags"] = tags
            word_data["highlight"] = len(tags) > 0
            tagged_words.append(word_data)
        
        return tagged_words
    
    def generate_highlighted_ass(self, tagged_words: list, template: dict) -> str:
        """生成带高亮的 ASS 字幕"""
        # 根据标签决定颜色
        # keyword: 黄色
        # trending: 红色
        # brand: 品牌色
        # emotion:joy: 橙色
        # emotion:surprise: 紫色
        pass
```

### 3.3 Phase 3: 动画模板系统 (P1)

**模板配置示例**:

```json
{
  "template_id": "hype_v1",
  "name": "动感电竞",
  "description": "适合游戏、体育、快节奏内容",
  "style": {
    "font_family": "Arial Black",
    "font_size_base": 52,
    "primary_color": "#FFFFFF",
    "outline_color": "#00FF00",
    "outline_width": 4,
    "shadow": 2,
    "bold": true
  },
  "animation": {
    "type": "pop",
    "word_animation": "highlight",
    "entrance": "fade_in",
    "entrance_duration": 150,
    "highlight_color": "#00FFFF",
    "highlight_scale": 1.1
  },
  "keyword_styles": {
    "keyword": {
      "color": "#FFFF00",
      "scale": 1.15,
      "effect": "glow"
    },
    "trending": {
      "color": "#FF0000",
      "scale": 1.2,
      "effect": "pulse"
    },
    "emotion:joy": {
      "color": "#FFA500",
      "emoji": "🔥"
    },
    "emotion:surprise": {
      "color": "#FF00FF",
      "emoji": "😱"
    }
  },
  "position": {
    "vertical": "bottom",
    "margin_v": 100,
    "alignment": "center"
  }
}
```

### 3.4 Phase 4: 品牌模板 (P1)

**用户自定义模板**:

```python
# brand_template.py

class BrandTemplate:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.fonts = {}  # 用户上传的字体
        self.colors = {}  # 品牌色
        self.logo = None  # 品牌Logo
    
    def create_template(self, config: dict) -> dict:
        """创建品牌模板"""
        template = {
            "template_id": f"brand_{self.user_id}_{uuid.uuid4().hex[:8]}",
            "name": config.get("name", "我的品牌模板"),
            "style": {
                "font_family": config.get("font", "Arial"),
                "primary_color": config.get("primary_color", "#FFFFFF"),
                "outline_color": config.get("outline_color", "#000000"),
                # ...
            },
            "brand": {
                "logo_position": config.get("logo_position"),
                "watermark": config.get("watermark"),
            }
        }
        return template
    
    def upload_font(self, font_file: bytes) -> str:
        """上传自定义字体"""
        # 保存字体文件
        # 返回字体ID
        pass
```

---

## 4. 实现路线图

### 4.1 阶段规划

```
Phase 1: 词级动画 (P0) - 1 周
├── Day 1-2: Whisper Large V3 集成
├── Day 3-4: 词级时间戳提取
├── Day 5-7: ASS 词级动画生成
└── 交付: 基础词级高亮功能

Phase 2: AI 关键词 (P0) - 1 周
├── Day 1-2: KeyBERT 集成
├── Day 3-4: 关键词标签系统
├── Day 5-7: 关键词高亮渲染
└── 交付: 自动关键词高亮

Phase 3: 动画模板 (P1) - 2 周
├── Week 1: 模板系统设计 + 10 个基础模板
├── Week 2: 10 个高级模板 + 动画效果
└── 交付: 20+ 动画模板

Phase 4: 品牌模板 (P1) - 1 周
├── Day 1-3: 品牌模板创建界面
├── Day 4-5: 字体上传
├── Day 6-7: 模板分享
└── 交付: 用户自定义模板
```

### 4.2 优先级矩阵

| 功能 | 优先级 | 复杂度 | 影响度 | 排期 |
|------|--------|--------|--------|------|
| 词级时间戳 | P0 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Week 1 |
| 关键词高亮 | P0 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Week 2 |
| 动画模板 | P1 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Week 3-4 |
| 品牌模板 | P1 | ⭐⭐⭐ | ⭐⭐⭐ | Week 5 |
| Emoji 插入 | P2 | ⭐⭐ | ⭐⭐ | Week 6 |

---

## 5. 技术选型

### 5.1 转录引擎

| 引擎 | 准确率 | 速度 | 成本 | 推荐 |
|------|--------|------|------|------|
| **Whisper Large V3** | 95%+ | 慢 | 免费 | ✅ 推荐 |
| Whisper Medium | 90% | 中 | 免费 | 备选 |
| AssemblyAI | 99%+ | 快 | 付费 | 可选 |

### 5.2 关键词提取

| 工具 | 准确率 | 速度 | 推荐 |
|------|--------|------|------|
| **KeyBERT** | 高 | 快 | ✅ 推荐 |
| YAKE | 中 | 快 | 备选 |
| LLM (GPT-4) | 最高 | 慢 | 可选 |

### 5.3 渲染方式

| 方式 | 效果 | 速度 | 兼容性 | 推荐 |
|------|------|------|--------|------|
| **ASS 增强** | 中 | 快 | 高 | ✅ 推荐 |
| CSS + Playwright | 高 | 慢 | 中 | 可选 |
| Remotion | 最高 | 中 | 低 | 未来 |

---

## 6. 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| Whisper 转录慢 | 高 | 高 | 使用 GPU / 更小模型 |
| ASS 动画兼容性 | 中 | 中 | 测试多平台 |
| 关键词提取不准 | 中 | 中 | 结合多种方法 |
| 品牌字体版权 | 低 | 低 | 用户自行负责 |

---

## 7. 参考资料

### 7.1 OpusClip
- 官网: https://www.opus.pro/captions
- 特色: 99%+ 准确率、20+ 动画模板、品牌定制

### 7.2 pycaps
- GitHub: https://github.com/francozanardi/pycaps
- 特色: Python + CSS、离线渲染、模板系统
- CLI: `pycaps render --input video.mp4 --template hype`

### 7.3 Remotion
- 官网: https://remotion.dev
- 特色: React + CSS、视频编程、生态丰富

### 7.4 shorts-fission 现有代码
- `text_layer_engine_v2.py` - 现有文字层引擎
- `effect_templates.py` - 20 种特效模板
- `subtitle_extractor.py` - 字幕提取

---

## 8. 总结

### 8.1 核心升级点

1. **词级动画** - 从整句显示升级到逐词高亮
2. **AI 标签** - 自动识别关键词、热词、情感词
3. **模板系统** - 从静态模板升级到动态动画模板
4. **品牌定制** - 支持用户上传字体、颜色、Logo

### 8.2 预期效果

| 指标 | 现状 | 目标 |
|------|------|------|
| 字幕吸引力 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 用户停留 | 3 秒 | 8 秒 |
| 完播率提升 | - | +50% |
| 制作效率 | - | +200% |

### 8.3 下一步行动

1. **立即**: 安装 Whisper Large V3 模型
2. **本周**: 实现词级时间戳提取
3. **下周**: 实现 ASS 词级动画渲染
4. **两周后**: 集成 KeyBERT 关键词提取

---

*文档版本: v1.0*
*创建日期: 2026-03-21*
*创建者: T.W (Twin William)*
