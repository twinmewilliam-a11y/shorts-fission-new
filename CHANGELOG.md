# Changelog

## [v4.1.8] - 2026-04-05

### 🔧 代码质量优化 & 架构重构

基于后端（28项）和前端（35项）代码审查报告，按风险从低到高执行全面优化。

#### 功能修复
- **上传进度条修复**: `fetch` → `XMLHttpRequest`，接入真实上传进度回调，进度条从 0% 平滑显示到 100%

#### 后端优化（14项）
- 15处 bare `except:` → `except Exception:` 统一异常处理
- 9处未使用 import 批量清理（autoflake）
- 删除冗余模块: `remotion_caption.py`、`pycaps_subtitle.py`
- 删除重复函数定义: `generate_word_level_animation` 第一个定义
- batch-download 空路由 → `HTTPException(501)` 明确标注未实现
- LLM 翻译 TODO → 接入已有 `translator.py` 实现
- **celery_tasks.py 大文件拆分**（1168行 → 6个模块）:
  - `celery_app.py` (131行) — Celery 实例 + 全局变量 + 模型预热
  - `variant_tasks.py` (698行) — 变体生成任务
  - `download_tasks.py` (155行) — 下载任务
  - `subtitle_utils.py` (367行) — 字幕工具函数
  - `progress.py` (64行) — 进度更新
  - `__init__.py` (149行) — 兼容导出，保持旧路径可用

#### 前端优化（14项）
- 删除 4 个未使用组件: EffectSelector、SceneSelector、TextLayerConfig、VariantProgress
- 删除未使用常量 `constants/effects.ts`
- 删除双重 Tailwind 配置（保留 .js）
- 卸载 5 个未使用 npm 依赖: react-query、axios、clsx、tailwind-merge、zustand
- `alert()` → `Toast` 统一（Downloads、VideoDetailModal、VideoUploader 共 12 处）
- 清理 `index.css` 手写 Tailwind 类、`WS_BASE_URL` 未使用导出、`.bak` 备份文件
- 清理 remotion-caption 冗余 JSON（6个测试/备份文件）
- **VideoDetailModal 大组件拆分**（771行 → 8个子组件）:
  - `VideoPreview.tsx` — 视频/缩略图预览
  - `VideoInfo.tsx` — 视频信息卡片
  - `VariantCountSelector.tsx` — 变体数量 + 字幕选项
  - `ProcessingStatus.tsx` — 处理中状态
  - `VariantList.tsx` — 变体列表
  - `VariantDetail.tsx` — 变体详情弹窗（三层参数）
  - `AddVariantsModal.tsx` — 新增变体弹窗
- **类型统一**: 创建 `types/index.ts`，Video/Variant 类型集中管理
- **API 封装**: 创建 `api/client.ts`，统一 fetch 客户端

#### 部署后 Bug 修复（3项）
- 修复按钮重复渲染（VideoInfo 与主组件冲突）
- 修复视频信息卡片重复（VideoPreview 与 VideoInfo 冲突）
- 修复变体详情三层参数解析错乱 + 文字层标题修正（"字幕显示" → "词级动画字幕"）

#### 验证
- 后端全量 Python 语法检查 ✅（35个文件零错误）
- 前端 TypeScript 编译 ✅
- Flask 路由加载 ✅（34 routes）
- Celery 导入兼容性 ✅（旧路径 + 新路径均可用）

---

## [v4.1.7] - 2026-04-02

### 🎬 变体详情参数显示优化

#### 优化目标
优化"查看详情"弹窗中三层参数的显示格式，更清晰直观。

#### 三层参数新格式

**背景层：**
- 🔮 模糊σ=38 - 全景模糊参数
- 🔍 放大134% - 背景放大比例
- ⏩ 变速1.18x - 视频变速
- 🪞 镜像 ✓ - 水平翻转（如有）
- 🔄 旋转5.2° - 旋转角度（如有）

**中间层：**
- 📐 缩放134% - 中间层缩放
- ✂️ 裁剪10% - 裁剪比例
- ✨ 饱和 + 亮度 + 对比度 - 增强特效（最多显示3个）

**文字层：**
- 🎨 炫酷 - 动画模板名称（中文）
- 📍 顶部居中 - 字幕位置
- 🎬 占位字幕 ✓ - 是否使用占位字幕
- 🌐 翻译(英文) ✓ - 是否使用翻译

#### 修改文件
- `backend/app/tasks/celery_tasks.py` - effects_desc 生成逻辑优化

---

## [v4.1.6] - 2026-04-01

### ⚡ FFmpeg 编码优化

#### 优化目标
在 4 核 CPU + 4 变体并行渲染场景下，避免 CPU 过载，提升渲染稳定性。

#### 优化内容

| 参数 | 位置 | 旧值 | 新值 | 说明 |
|------|------|------|------|------|
| `-q:v` | 字幕烧录 | - | 12 | 质量换速度，字幕烧录使用较低质量 |
| `-q:v` | PNG/WebM overlay | - | 10 | overlay 编码优化 |
| `-threads` | 全部 FFmpeg | auto | 2 | 每任务限制 2 线程，4变体×2=8线程 |
| `--concurrency` | Remotion | - | 4 | 并发渲染 4 帧 |

#### 修改文件
- `backend/app/services/variant_engine.py` - FFmpeg 编码参数优化
- `backend/app/tasks/celery_tasks.py` - Remotion 并发参数

---

## [v4.1.5] - 2026-03-30

### 🌐 字幕翻译功能

#### 功能概述
支持将非英文字幕自动翻译为英文或中文，使用 OpenRouter API（google/gemini-2.5-flash-lite 模型）。

#### 翻译配置
- **提供商**: OpenRouter
- **模型**: `google/gemini-2.5-flash-lite`
- **目标语言**: 英文、中文
- **翻译时机**: WhisperX 提取后立即翻译
- **原文保留**: 保留在数据库，视频只显示翻译后字幕

#### 前端选项
- **不翻译（保持原文）** - 默认选项
- **翻译为英文**
- **翻译为中文**

#### 技术实现
- **API 调用**: OpenRouter Chat Completions API
- **参数传递**: `target_language` 参数从前端 → API → Celery Worker
- **词级翻译**: 保持时间戳不变，只替换文字
- **代码位置**: `backend/app/services/translator.py`

### 📁 修改文件

#### 后端
- `backend/app/services/translator.py` - 翻译服务模块（新增）
- `backend/app/tasks/celery_tasks.py` - 集成翻译逻辑
- `backend/app/api/routes/videos.py` - API 参数 `target_language`
- `backend/app/config.py` - OpenRouter 配置（`OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`）

#### 前端
- `frontend/src/components/VideoDetailModal.tsx` - 语言选择器 UI

#### 配置
- `backend/.env` - 添加 OpenRouter API 配置

---

## [v4.1.4] - 2026-03-30

### 🎬 占位字幕功能（无字幕视频自动补充）

#### 功能概述
当 WhisperX 检测到视频**没有字幕**或**词数少于5个**时，自动生成占位字幕。

#### 字幕内容（2种方案随机选择）
- **方案1**: `Don't Miss Next Game👀   ⚽🏀🏈⚾🏒Sports Highlights & Live HD   🔥 Link in My Bio🔥`（5秒时长）
- **方案2**: `Watch HD LIVE → 🔥Link in My Bio🔥`（4秒时长）

#### 播放规则
- **开始时间**: 第3秒
- **显示间隔**: 5秒（从上一条字幕结尾计算）
- **位置**: 固定在顶部
- **动画模板**: 使用用户选择的 PyCaps 12种动画模板（或随机）
- **前端开关**: 默认启用，可手动关闭

#### 技术实现
- **触发条件**: `words_data` 为空 或 `len(words_data) < 5`
- **Emoji 支持**: 添加 Noto Color Emoji 字体到所有 Remotion 模板
- **代码位置**: `backend/app/tasks/celery_tasks.py`

### 🐛 Bug 修复

#### 单个变体下载文件名
- **修复前**: `variant_{variant_id}.mp4`
- **修复后**: `{视频ID}_variant_{变体序号}.mp4`
- **示例**: `22_variant_3.mp4`

#### 设置变体数量对话框
- **问题**: 深色主题下输入框数字看不见
- **修复**: 添加 `text-gray-900 bg-white` 样式

### 📁 修改文件

#### 后端
- `backend/app/tasks/celery_tasks.py` - 占位字幕生成逻辑
- `backend/app/api/routes/downloads.py` - 文件名格式修改
- `backend/app/api/routes/videos.py` - API 参数 `placeholder_subtitle_enabled`

#### 前端
- `frontend/src/components/VideoDetailModal.tsx` - 占位字幕开关、文件名格式
- `frontend/src/components/AnimationTemplateSelector.tsx` - 12种模板配置

#### Remotion
- `remotion-caption/src/WordAnimation.tsx` - 所有12种模板添加 `'Noto Color Emoji'` 字体支持

---

## [v4.1.3] - 2026-03-30

### 🎨 UI/UX 深色主题优化

#### 前端界面改进
- **深色主题统一**: 所有组件采用一致的深色配色（#0F172A 背景、#EC4899 主色）
- **视频卡片编号显示**: 左上角显示数据库 ID（#001, #002...），便于与下载包对应
- **骨架屏加载**: 添加 VideoCardSkeleton 组件，优化加载体验

#### 批量操作功能
- **批量选择模式**: 全选/取消全选按钮
- **批量下载**: 支持 ZIP 打包下载多个变体
- **批量删除**: 带确认弹窗的批量删除功能

### 🐛 Bug 修复

#### 跨域下载问题
- **问题**: 浏览器 Fetch API 在跨域下载文件时有 CORS 限制
- **尝试方案**:
  1. `fetch` + `blob` → CORS 错误 (`net::ERR_FAILED 200 OK`)
  2. `window.open()` → 打开新页面，用户体验差
  3. `<a>` 标签无延迟 → 只触发第一个下载
  4. `iframe` 方式 → 不触发任何下载
- **最终方案**: `<a>` 标签 + 2 秒延迟逐个触发下载

#### 下载功能修复
- ✅ 单个视频下载（不打开新页面）
- ✅ 单个变体下载（详情弹窗）
- ✅ 批量下载（逐个 ZIP 打包）

### 🧹 缓存清理系统

#### 自动清理 Hook
- **即时清理**: 变体生成完成后自动清理当前视频的 PNG 序列
- **大小清理**: 缓存超过 500 MB 时自动清理最旧的
- **集成点**: 已集成到 Celery 任务流程

#### 清理脚本
- **定时清理**: `scripts/cleanup_cache.py` 支持干运行和实际清理
- **Cron 配置**: 每天凌晨 3:00 自动清理过期缓存

### 📁 修改文件

#### 前端
- `frontend/src/pages/Videos.tsx` - 批量操作状态管理、下载/删除函数
- `frontend/src/components/VideoCard.tsx` - 编号显示、选择模式 UI
- `frontend/src/components/VideoDetailModal.tsx` - 单个变体下载修复
- 多个组件 - 深色主题样式统一

#### 后端
- `backend/app/api/routes/videos.py` - 批量删除 API (`/batch-delete`)
- `backend/app/api/routes/variants.py` - 批量下载 API (`/batch-download`)
- `backend/app/hooks/cache_cleanup.py` - 缓存清理 Hook 模块

#### 脚本
- `scripts/cleanup_cache.py` - 缓存清理脚本

### 🔧 技术总结

#### 跨域下载解决方案对比

| 方案 | 效果 | 问题 |
|------|------|------|
| `fetch` + `blob` | ❌ | CORS 错误 |
| `window.open()` | ❌ | 打开新页面 |
| `<a>` 标签无延迟 | ❌ | 只触发第一个 |
| **`<a>` 标签 + 2秒延迟** | ✅ | **成功** |

---

## [v4.1.2] - 2026-03-26

### ⚡ 性能优化

#### 方案 1: Remotion 并发渲染
- 添加 `--concurrency 4` 参数
- Remotion 同时渲染 4 帧（根据 CPU 核心数）
- 预期渲染速度提升 2-4 倍

#### 方案 2: FFmpeg 多线程优化
- 添加 `-threads 4` 参数到 overlay 命令
- FFmpeg 使用多线程处理视频合成
- 预期 overlay 速度提升 1.5-2 倍

#### WhisperX 模型预热
- Worker 启动时预先加载 WhisperX 模型
- 首次请求无需等待模型加载
- 预热耗时 ~12 秒

#### 方案 A: ThreadPoolExecutor 并行生成
- 使用 `ThreadPoolExecutor` 并行生成变体
- 最多 4 个并行线程
- 预期生成速度提升 2-4 倍

### 📁 修改文件
- `backend/app/tasks/celery_tasks.py` - 并行生成逻辑
- `backend/app/services/model_warmup.py` - 模型预热模块
- `backend/app/services/subtitle_extractor.py` - 使用缓存模型

---

## [v4.1.1] - 2026-03-26

### ⚡ 性能优化

#### 方案 1: Remotion 并发渲染
- 添加 `--concurrency 4` 参数
- Remotion 同时渲染 4 帧（根据 CPU 核心数）
- 预期渲染速度提升 2-4 倍

#### 方案 2: FFmpeg 多线程优化
- 添加 `-threads 4` 参数到 overlay 命令
- FFmpeg 使用多线程处理视频合成
- 预期 overlay 速度提升 1.5-2 倍

### 📁 修改文件
- `backend/app/tasks/celery_tasks.py` - 第 118-135 行（Remotion）、第 625 行（FFmpeg）

---

## [v4.1.0] - 2026-03-23

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
