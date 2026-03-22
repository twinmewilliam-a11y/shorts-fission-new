# TikTok/YouTube Shorts 流行动画字幕调研

> **调研日期**: 2026-03-22
> **调研者**: T.W (Twin William)

---

## 执行摘要

基于对 TikTok、YouTube Shorts 头部创作者的分析，总结了 **5 种最流行的动画字幕风格**，为 shorts-fission 升级提供参考。

---

## 1. MrBeast 字幕风格分析

### 1.1 核心特点

| 特性 | 描述 |
|------|------|
| **字体** | Impact / Anton (粗体无衬线) |
| **主色** | 纯白 (#FFFFFF) |
| **描边** | 粗黑边 (4-6px) |
| **阴影** | 深色投影 |
| **动画** | 逐词弹出 (Pop) |
| **高亮** | 关键词黄色/红色 |

### 1.2 动画效果

```
MrBeast 字幕动画流程:
1. 整句淡入 (Fade In, 100ms)
2. 当前词放大 + 变色 (Scale 1.2, Yellow)
3. 已读词恢复原色 (White)
4. 句子结束后淡出
```

### 1.3 技术实现要点

- **分层渲染**: 基础层(整句) + 高亮层(当前词)
- **颜色切换**: 当前词 `\c&H00FFFF&` (黄色) / 其他词 `\c&HFFFFFF&` (白色)
- **放大效果**: 当前词 `\t(\fscx120\fscy120)` (放大 20%)

---

## 2. 流行字幕风格 Top 5

### 风格 1: Pop Highlight (弹出高亮)

**适用场景**: 所有类型视频，最通用

```
特点:
- 当前词放大 10-20%
- 颜色从白色变为黄色
- 其他词保持原样
- 简洁有力

技术参数:
- 动画类型: Pop
- 高亮颜色: #FFFF00 (黄色)
- 正常颜色: #FFFFFF (白色)
- 缩放: 1.15x
- 动画时长: 150ms
```

### 风格 2: Karaoke (卡拉OK)

**适用场景**: 音乐视频、节奏感强的内容

```
特点:
- 词随音频逐字出现
- 已读词变深色
- 未读词浅色/透明
- 流畅过渡

技术参数:
- 动画类型: Progressive
- 已读颜色: #FFFFFF
- 未读颜色: #FFFFFF80 (50%透明)
- 过渡时长: 实时跟随音频
```

### 风格 3: Hype/Gaming (动感电竞)

**适用场景**: 游戏、体育、快节奏内容

```
特点:
- 荧光绿/霓虹蓝描边
- 文字带发光效果
- 关键词红色高亮
- 抖动/震动效果

技术参数:
- 主色: #FFFFFF
- 描边: #00FF00 (荧光绿)
- 关键词: #FF0000 (红色)
- 发光: \blur4
- 抖动: \t(\frx5)\t(\frx-5)
```

### 风格 4: Minimalist (简约)

**适用场景**: Vlog、教育、访谈

```
特点:
- 细字体、小描边
- 淡入淡出
- 无复杂动画
- 低调不抢眼

技术参数:
- 字体: Roboto / Open Sans
- 字号: 偏小 (40-45px)
- 描边: 2px 浅灰
- 动画: Fade (200ms)
```

### 风格 5: News/Professional (新闻风)

**适用场景**: 新闻、商业、严肃内容

```
特点:
- 底部横幅背景
- 黄色/橙色关键词
- 清晰易读
- 专业感

技术参数:
- 背景: 半透明黑条
- 主色: #FFFFFF
- 关键词: #FFA500 (橙色)
- 位置: 底部居中
```

---

## 3. 推荐实现的 5 个模板

| 模板名 | 风格描述 | 适用场景 | 优先级 |
|--------|---------|---------|--------|
| **pop_highlight** | MrBeast 风格，当前词放大+黄色高亮 | 通用、病毒视频 | P0 |
| **karaoke_flow** | 卡拉OK风格，逐字变色 | 音乐、节奏内容 | P1 |
| **hype_gaming** | 电竞风格，荧光色+发光+抖动 | 游戏、体育 | P1 |
| **minimalist_clean** | 简约风格，淡入淡出 | Vlog、教育 | P1 |
| **news_professional** | 新闻风格，底部背景条 | 商业、新闻 | P2 |

---

## 4. 技术实现参考

### 4.1 Pop Highlight (MrBeast 风格) ASS 代码

```ass
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,52,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,10,10,80,1
Style: Highlight,Arial Black,60,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,115,115,0,0,1,6,2,2,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
; 基础层 - 整句
Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,{\fad(100,100)}This is an amazing video
; 高亮层 - 逐词高亮
Dialogue: 1,0:00:00.00,0:00:00.30,Highlight,,0,0,0,,{\t(\fscx115\fscy115)}This{\r} is an amazing video
Dialogue: 1,0:00:00.30,0:00:00.60,Highlight,,0,0,0,,This {\t(\fscx115\fscy115)}is{\r} an amazing video
Dialogue: 1,0:00:00.60,0:00:00.90,Highlight,,0,0,0,,This is {\t(\fscx115\fscy115)}an{\r} amazing video
```

### 4.2 Hype Gaming 风格 ASS 代码

```ass
Style: Hype,Arial Black,56,&H00FFFFFF,&H000000FF,&H0000FF00,&HA0000000,1,0,0,0,100,100,0,0,1,4,3,2,10,10,80,1
Style: HypeKeyword,Arial Black,64,&H000000FF,&H000000FF,&H0000FF00,&HA0000000,1,0,0,0,120,120,0,0,1,5,4,2,10,10,80,1

; 关键词带抖动效果
Dialogue: 1,0:00:00.00,0:00:00.50,HypeKeyword,,0,0,0,,{\blur3\t(\frx5)\t(\frx-5)\t(\frx5)}EPIC{\r}
```

---

## 5. pycaps 参考实现

**pycaps** 是一个开源的 Python 字幕动画工具，可以作为技术参考：

```bash
# 安装
pip install "git+https://github.com/francozanardi/pycaps.git#egg=pycaps[all]"

# 使用模板
pycaps render --input video.mp4 --template hype
pycaps render --input video.mp4 --template minimalist
```

**pycaps 核心特性**:
- CSS 样式字幕
- `.word-being-narrated` 状态选择器（当前词）
- Whisper 词级时间戳
- 模板系统

---

## 6. 下一步行动

1. **立即**: 实现 `pop_highlight` 模板（P0）
2. **本周**: 实现 `karaoke_flow` 和 `hype_gaming` 模板
3. **下周**: 完成全部 5 个模板

---

## 7. 参考链接

- MrBeast YouTube: https://www.youtube.com/@MrBeast
- pycaps GitHub: https://github.com/francozanardi/pycaps
- pycaps 官网: https://www.pycaps.com/
- ASS 字幕格式: http://www.tcax.org/docs/ass-specs.htm

---

*文档版本: v1.0*
*创建日期: 2026-03-22*
*创建者: T.W (Twin William)*
