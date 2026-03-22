# Changelog

## [v2.1.0] - 2026-03-23

### 🎉 词级动画字幕系统 (Word-Level Animated Captions)

#### 新功能
- **PyCaps 12 个预设模板**: minimalist, default, classic, neo_minimal, hype, explosive, fast, vibrant, word_focus, line_focus, retro_gaming, model
- **Remotion 渲染引擎**: PNG 序列直接 overlay，透明背景
- **智能位置系统**: 3 个位置（顶部/中部/底部居中），距边缘 300px
- **大字体优化**: 默认 56px，自动换行（每行最多 20 字符）
- **前端模板选择器**: 实时预览 + hover 效果

#### 技术改进
- **方案 C**: PNG 序列直接 overlay（跳过 WebM 编码，避免 alpha 通道丢失）
- **动态裁剪填充**: 无黑边，画面填满 1080x1920
- **eof_action=pass + -shortest**: 视频/音频/字幕同步结束
- **Remotion 相对路径修复**: 解决绝对路径导致的 sequence 渲染失败

#### 修复问题
- ✅ 字幕透明背景（PNG 序列 RGBA）
- ✅ 黑边问题（动态裁剪填充）
- ✅ 字幕时长过长（精确到最后一个词结束）
- ✅ 视频/音频提前停止（eof_action=pass）
- ✅ WebM alpha 通道丢失（跳过 WebM，直接 PNG overlay）
- ✅ FFmpeg 编码器兼容（mpeg4 替代 libx264/libopenh264）
- ✅ 字体大小（放大 1 倍）
- ✅ 自动换行（每行 20 字符）

### 📁 文件变更

#### 新增文件
- `backend/app/services/subtitle/` - 字幕处理模块
  - `document.py` - 数据模型
  - `layout.py` - 布局计算
  - `tagger.py` - 标签系统
  - `processor.py` - 主处理器
- `backend/app/services/word_level_animation.py` - 词级动画引擎
- `remotion-caption/` - Remotion 渲染项目
  - `src/WordAnimation.tsx` - 12 个模板 + 3 个位置
  - `src/index.ts` - Remotion 入口
- `frontend/src/components/AnimationTemplateSelector.tsx` - 模板选择器

#### 修改文件
- `backend/app/tasks/celery_tasks.py` - 集成 Remotion 渲染
- `backend/app/services/variant_engine.py` - PyCaps 模板支持
- `frontend/vite.config.ts` - 端口改为 3000

### 🎨 模板列表

| 模板 | 名称 | 描述 |
|------|------|------|
| minimalist | Minimalist | 极简风格 - 白色无背景 |
| default | Default | 默认风格 - 经典字幕效果 |
| classic | Classic | 经典风格 - 衬线字体 |
| neo_minimal | Neo Minimal | 新极简风格 - 现代简约 |
| hype | Hype | 动感风格 - 橙色高亮 + 缩放 |
| explosive | Explosive | 爆炸风格 - 黄色爆炸效果 |
| fast | Fast | 快速风格 - Impact 字体 |
| vibrant | Vibrant | 活力风格 - 渐变背景 |
| word_focus | Word Focus | 词焦点风格 - 当前词高亮 |
| line_focus | Line Focus | 行焦点风格 - 整行高亮 |
| retro_gaming | Retro Gaming | 复古游戏风格 - 像素风 |
| model | Model | 模特风格 - 高端斜体 |

### 📍 位置选项

| 位置 | 描述 |
|------|------|
| top_center | 顶部居中（距顶 300px）|
| center | 中部居中 |
| bottom_center | 底部居中（距底 300px）|

---

## [v2.0.0] - 2026-03-15

### 初始版本
- PIP 画中画变体生成
- ASS 字幕烧录
- BGM 替换
- 视频特效（模糊、缩放、变速等）
