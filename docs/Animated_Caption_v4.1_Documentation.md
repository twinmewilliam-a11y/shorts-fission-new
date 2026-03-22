# Animated Caption 功能升级文档

## 版本信息
- **版本号**: v4.1.0
- **发布日期**: 2026-03-23
- **功能代号**: Word-Level Animated Captions

---

## 1. 功能概述

词级动画字幕系统（Word-Level Animated Captions）是一个基于 PyCaps 架构、使用 Remotion 渲染引擎的字幕生成系统。支持 12 个预设模板、3 个位置选项，输出透明背景的字幕 overlay。

### 1.1 核心特性

| 特性 | 描述 |
|------|------|
| **词级动画** | 每个词单独动画，当前词高亮/放大 |
| **透明背景** | PNG 序列直接 overlay，背景完全透明 |
| **12 个模板** | PyCaps 预设模板，覆盖多种风格 |
| **3 个位置** | 顶部/中部/底部居中，距边缘 300px |
| **大字体** | 56px 默认大小，自动换行 |
| **前端预览** | 模板选择器 + hover 预览效果 |

---

## 2. 技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Animated Caption 架构                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │  WhisperX   │────▶│ Subtitle    │────▶│  Remotion   │   │
│  │  词级时间戳  │     │ Processor   │     │   渲染引擎   │   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │ words.json  │     │ config.json │     │ PNG 序列    │   │
│  │ 词级数据     │     │ 模板/位置    │     │ element-*.png│   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
│                                                 │           │
│                                                 ▼           │
│                                         ┌─────────────┐    │
│                                         │   FFmpeg    │    │
│                                         │   overlay   │    │
│                                         └─────────────┘    │
│                                                 │           │
│                                                 ▼           │
│                                         ┌─────────────┐    │
│                                         │  Final MP4  │    │
│                                         │  透明字幕    │    │
│                                         └─────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 位置 | 功能 |
|------|------|------|
| **WhisperX** | `backend/app/services/subtitle_extractor.py` | 词级时间戳提取 |
| **SubtitleProcessor** | `backend/app/services/subtitle/` | 布局计算 + 标签 |
| **Remotion** | `remotion-caption/` | PNG 序列渲染 |
| **FFmpeg overlay** | `backend/app/tasks/celery_tasks.py` | 视频 + 字幕合成 |

### 2.3 数据流

```
1. 用户上传视频
      ↓
2. WhisperX 提取词级时间戳
      ↓
3. SubtitleProcessor 处理:
   - 布局计算（分行）
   - 结构标签（首词/末词）
   - 语义标签（高亮词）
      ↓
4. 生成 subtitle_config.json
      ↓
5. Remotion 渲染 PNG 序列:
   - 12 个模板样式
   - 3 个位置
   - RGBA 透明背景
      ↓
6. FFmpeg overlay:
   - 动态裁剪填充（无黑边）
   - PNG 序列直接 overlay
   - eof_action=pass（同步结束）
      ↓
7. 输出 MP4（透明字幕）
```

---

## 3. 动画字幕生成流程

### 3.1 词级时间戳提取

```python
# WhisperX 提取
words = [
    {"text": "Hello", "start": 0.0, "end": 0.5},
    {"text": "world", "start": 0.6, "end": 1.0},
    ...
]
```

### 3.2 布局计算

```python
# SubtitleProcessor 分行
lines = [
    {
        "id": 0,
        "text": "Hello world",
        "start": 0.0,
        "end": 1.0,
        "words": [...],
        "tags": ["first-line"]
    },
    ...
]
```

### 3.3 Remotion 配置生成

```json
{
  "config": {
    "template": "hype",
    "position": "bottom_center",
    "fontSize": 56,
    "videoWidth": 1080,
    "videoHeight": 1920
  },
  "lines": [...]
}
```

### 3.4 PNG 序列渲染

```bash
# Remotion 命令
npx remotion render src/index.ts Caption out/png_15/frames \
  --frames 0-752 \
  --fps 30 \
  --width 1080 \
  --height 1920 \
  --sequence
```

### 3.5 FFmpeg Overlay

```bash
# overlay 命令
ffmpeg -y \
  -i variant_001.mp4 \
  -framerate 30 -i element-%03d.png \
  -filter_complex \
    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];[bg][1:v]overlay=0:0:eof_action=pass[out]" \
  -map "[out]" -map 0:a? \
  -c:v mpeg4 -q:v 5 \
  -c:a aac -b:a 128k \
  -shortest \
  output.mp4
```

---

## 4. 12 个模板介绍

### 4.1 模板分类

| 类别 | 模板 | 特点 |
|------|------|------|
| **简约类** | minimalist, default, classic, neo_minimal, model | 干净简洁，适合正式场合 |
| **动感类** | hype, explosive, fast | 强烈动画，适合运动/游戏 |
| **活力类** | vibrant, word_focus, line_focus | 色彩丰富，适合娱乐 |
| **复古类** | retro_gaming | 像素风，适合游戏 |

### 4.2 详细介绍

#### 简约类

| 模板 | 字体 | 颜色 | 背景 | 适用场景 |
|------|------|------|------|---------|
| **minimalist** | Helvetica Neue | 白色 | 透明 | Vlog、教程 |
| **default** | Helvetica Neue | 白色 | 黑色半透明 | 通用 |
| **classic** | Georgia | 白色 | 黑色半透明 | 纪录片、教育 |
| **neo_minimal** | SF Pro Display | 白色 | 透明 | 时尚、生活 |
| **model** | Playfair Display 斜体 | 白色 | 透明 | 时尚、高端 |

#### 动感类

| 模板 | 字体 | 当前词颜色 | 特效 | 适用场景 |
|------|------|-----------|------|---------|
| **hype** | Arial Black | 橙色 | 放大 15% | 运动、电竞 |
| **explosive** | Arial Black | 黄色 | 放大 20% | 运动、游戏 |
| **fast** | Impact | 青色 | 大写 | 新闻、快节奏 |

#### 活力类

| 模板 | 字体 | 当前词颜色 | 背景 | 适用场景 |
|------|------|-----------|------|---------|
| **vibrant** | Poppins | 粉色 | 渐变紫 | 音乐、舞蹈 |
| **word_focus** | Montserrat | 绿色 | 透明 | 教育、教程 |
| **line_focus** | Roboto | 白色 | 深灰 | 新闻、教育 |

#### 复古类

| 模板 | 字体 | 颜色 | 特效 | 适用场景 |
|------|------|------|------|---------|
| **retro_gaming** | Courier New | 绿色 | 像素风 | 游戏、复古 |

---

## 5. 位置系统

### 5.1 3 个位置

| 位置 | 描述 | Y 坐标 |
|------|------|--------|
| **top_center** | 顶部居中 | 距顶 300px |
| **center** | 中部居中 | 屏幕 50% |
| **bottom_center** | 底部居中 | 距底 300px |

### 5.2 位置选择建议

| 视频类型 | 推荐位置 | 原因 |
|---------|---------|------|
| 运动/游戏 | bottom_center | 不遮挡动作 |
| 采访/Vlog | top_center | 不遮挡人物 |
| 音乐/舞蹈 | center | 居中突出 |
| 教育/教程 | bottom_center | 阅读习惯 |

---

## 6. 技术细节

### 6.1 透明背景实现

**方案 C: PNG 序列直接 overlay**

```
问题: WebM 编码会丢失 alpha 通道
解决: 跳过 WebM，直接用 PNG 序列 overlay
```

### 6.2 黑边处理

**动态裁剪填充**

```bash
# 填满 1080x1920，无黑边
scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920
```

### 6.3 同步结束

**eof_action=pass + -shortest**

```bash
# 视频/音频/字幕同步结束
overlay=0:0:eof_action=pass
-shortest
```

### 6.4 自动换行

**每行最多 20 字符**

```python
max_chars_per_line: int = 20  # 大字体需要更少的字符/行
```

---

## 7. 文件结构

```
shorts-fission/
├── backend/
│   └── app/
│       ├── services/
│       │   ├── subtitle/
│       │   │   ├── document.py      # 数据模型
│       │   │   ├── layout.py        # 布局计算
│       │   │   ├── tagger.py        # 标签系统
│       │   │   └── processor.py     # 主处理器
│       │   ├── word_level_animation.py  # 词级动画引擎
│       │   └── subtitle_extractor.py    # WhisperX 提取
│       └── tasks/
│           └── celery_tasks.py      # Remotion 集成
├── frontend/
│   └── src/
│       └── components/
│           └── AnimationTemplateSelector.tsx  # 模板选择器
└── remotion-caption/
    └── src/
        ├── WordAnimation.tsx        # 12 个模板 + 3 个位置
        └── index.ts                 # Remotion 入口
```

---

## 8. API 接口

### 8.1 获取模板列表

```
GET /api/videos/animation-templates
```

返回:
```json
[
  {"id": "minimalist", "name": "极简风格", "description": "白色无背景"},
  {"id": "default", "name": "默认风格", "description": "经典字幕效果"},
  ...
]
```

### 8.2 获取位置列表

```
GET /api/videos/animation-positions
```

返回:
```json
[
  {"id": "top_center", "name": "顶部居中 (距顶 300px)"},
  {"id": "center", "name": "中部居中"},
  {"id": "bottom_center", "name": "底部居中 (距底 300px)"}
]
```

---

## 9. 更新日志

### v2.1.0 (2026-03-23)

**新功能**:
- PyCaps 12 个预设模板
- Remotion 渲染引擎（PNG 序列透明背景）
- 3 个位置（300px 边距）
- 大字体（56px）+ 自动换行（20 字符）
- 前端模板选择器（实时预览）

**修复**:
- 字幕透明背景
- 黑边问题
- 字幕时长过长
- 视频/音频提前停止
- WebM alpha 通道丢失
- FFmpeg 编码器兼容
- 字体大小
- 自动换行

---

## 10. 参考资料

- [PyCaps 官方仓库](https://github.com/SocialComplexityLab/pycaps)
- [Remotion 文档](https://www.remotion.dev/docs)
- [WhisperX 项目](https://github.com/m-bain/whisperX)

---

*文档版本: v2.1.0*
*更新日期: 2026-03-23*
